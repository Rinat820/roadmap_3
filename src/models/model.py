import sqlite3
from typing import List, Dict, Any, Optional


class DatabaseModel:
    def __init__(self, db_path='exchange_rates.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        
    
    def get_all_currencies(self) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, fullname, code, sign FROM currencies')
        rows = cursor.fetchall()
        return [{'id': row['id'], 'name': row['fullname'], 'code': row['code'], 'sign': row['sign']} for row in rows]


    def get_currency_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        if not code or len(code) != 3 or not code.isupper():
            raise ValueError('Код валюты отсутствует в адресе или некорректный (ожидается 3 заглавные буквы)')
        cursor = self.conn.cursor()
        cursor.execute('SELECT ID, FullName, Code, Sign FROM Currencies WHERE Code = ?', (code,))
        row = cursor.fetchone()
        if row:
            return {'id': row['ID'], 'name': row['FullName'], 'code': row['Code'], 'sign': row['Sign']}
        raise KeyError('Валюта не найдена')


    def add_currency(self, name: str, code: str, sign: str) -> Dict[str, Any]:
        if not all([name, code, sign]):
            raise ValueError('Отсутствует нужное поле формы (name, code, sign)')
        if len(code) != 3 or not code.isupper():
            raise ValueError('Код валюты должен быть ровно 3 заглавными буквами')
        cursor = self.conn.cursor()
        try:
            cursor.execute('INSERT INTO Currencies (FullName, Code, Sign) VALUES (?, ?, ?)', (name, code, sign))
            currency_id = cursor.lastrowid
            self.conn.commit()
            return {'id': currency_id, 'name': name, 'code': code, 'sign': sign}
        except sqlite3.IntegrityError:
            raise sqlite3.IntegrityError('Валюта с таким кодом уже существует')


    def get_all_exchange_rates(self) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT er.ID, er.Rate, 
                bc.ID AS base_id, bc.FullName AS base_name, bc.Code AS base_code, bc.Sign AS base_sign,
                tc.ID AS target_id, tc.FullName AS target_name, tc.Code AS target_code, tc.Sign AS target_sign
            FROM ExchangeRates er
            JOIN Currencies bc ON er.BaseCurrencyId = bc.ID
            JOIN Currencies tc ON er.TargetCurrencyId = tc.ID
        ''')
        rows = cursor.fetchall()
        return [{
            'id': row['ID'],
            'baseCurrency': {'id': row['base_id'], 'name': row['base_name'], 'code': row['base_code'], 'sign': row['base_sign']},
            'targetCurrency': {'id': row['target_id'], 'name': row['target_name'], 'code': row['target_code'], 'sign': row['target_sign']},
            'rate': row['Rate']
        } for row in rows]


    def get_exchange_rate_by_pair(self, pair: str) -> Optional[Dict[str, Any]]:
        if not pair or len(pair) != 6 or not pair.isupper():
            raise ValueError('Коды валют пары отсутствуют в адресе или некорректные (ожидается 6 заглавных букв)')
        base_code, target_code = pair[:3], pair[3:]
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT er.ID, er.Rate, 
                bc.ID AS base_id, bc.FullName AS base_name, bc.Code AS base_code, bc.Sign AS base_sign,
                tc.ID AS target_id, tc.FullName AS target_name, tc.Code AS target_code, tc.Sign AS target_sign
            FROM ExchangeRates er
            JOIN Currencies bc ON er.BaseCurrencyId = bc.ID
            JOIN Currencies tc ON er.TargetCurrencyId = tc.ID
            WHERE bc.Code = ? AND tc.Code = ?
        ''', (base_code, target_code))
        row = cursor.fetchone()
        if row:
            return {
                'id': row['ID'],
                'baseCurrency': {'id': row['base_id'], 'name': row['base_name'], 'code': row['base_code'], 'sign': row['base_sign']},
                'targetCurrency': {'id': row['target_id'], 'name': row['target_name'], 'code': row['target_code'], 'sign': row['target_sign']},
                'rate': row['Rate']
            }
        raise KeyError('Обменный курс для пары не найден')


    def add_exchange_rate(self, base_code: str, target_code: str, rate: float) -> Dict[str, Any]:
        if not all([base_code, target_code, rate is not None]):
            raise ValueError('Отсутствует нужное поле формы (baseCurrencyCode, targetCurrencyCode, rate)')
        cursor = self.conn.cursor()
        cursor.execute('SELECT ID FROM Currencies WHERE Code = ?', (base_code,))
        base_id = cursor.fetchone()
        cursor.execute('SELECT ID FROM Currencies WHERE Code = ?', (target_code,))
        target_id = cursor.fetchone()
        if not base_id or not target_id:
            raise KeyError('Одна (или обе) валюта из валютной пары не существует в БД')
        try:
            cursor.execute('INSERT INTO ExchangeRates (BaseCurrencyId, TargetCurrencyId, Rate) VALUES (?, ?, ?)', 
                        (base_id['ID'], target_id['ID'], rate))
            rate_id = cursor.lastrowid
            self.conn.commit()
            return self.get_exchange_rate_by_id(rate_id)
        except sqlite3.IntegrityError:
            raise sqlite3.IntegrityError('Валютная пара с таким кодом уже существует')


    def update_exchange_rate(self, pair: str, rate: float) -> Dict[str, Any]:
        if not pair or len(pair) != 6 or not pair.isupper():
            raise ValueError('Валютная пара отсутствует в адресе или некорректная')
        if rate is None:
            raise ValueError('Отсутствует нужное поле формы (rate)')
        base_code, target_code = pair[:3], pair[3:]
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE ExchangeRates SET Rate = ? 
            WHERE BaseCurrencyId = (SELECT ID FROM Currencies WHERE Code = ?) 
            AND TargetCurrencyId = (SELECT ID FROM Currencies WHERE Code = ?)
        ''', (rate, base_code, target_code))
        if cursor.rowcount == 0:
            raise KeyError('Валютная пара отсутствует в базе данных')
        self.conn.commit()
        return self.get_exchange_rate_by_pair(pair)


    def get_exchange_rate_by_id(self, rate_id: int) -> Dict[str, Any]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT er.ID, er.Rate, 
                bc.ID AS base_id, bc.FullName AS base_name, bc.Code AS base_code, bc.Sign AS base_sign,
                tc.ID AS target_id, tc.FullName AS target_name, tc.Code AS target_code, tc.Sign AS target_sign
            FROM ExchangeRates er
            JOIN Currencies bc ON er.BaseCurrencyId = bc.ID
            JOIN Currencies tc ON er.TargetCurrencyId = tc.ID
            WHERE er.ID = ?
        ''', (rate_id,))
        row = cursor.fetchone()
        return {
            'id': row['ID'],
            'baseCurrency': {'id': row['base_id'], 'name': row['base_name'], 'code': row['base_code'], 'sign': row['base_sign']},
            'targetCurrency': {'id': row['target_id'], 'name': row['target_name'], 'code': row['target_code'], 'sign': row['target_sign']},
            'rate': row['Rate']
        }


    def calculate_exchange(self, from_code: str, to_code: str, amount: float) -> Dict[str, Any]:
        if not all([from_code, to_code, amount is not None]):
            raise ValueError('Отсутствуют параметры from, to или amount')
        amount = float(amount)
        usd_rate_from = self._get_rate_for_pair('USD', from_code)
        usd_rate_to = self._get_rate_for_pair('USD', to_code)
        if usd_rate_from and usd_rate_to:
            direct_rate = usd_rate_to / usd_rate_from
            converted = amount * direct_rate
            return self._build_exchange_response(from_code, to_code, direct_rate, amount, converted)
        
        raise KeyError('Невозможно рассчитать обмен: нет подходящих курсов')


    def _get_rate_for_pair(self, base_code: str, target_code: str) -> Optional[float]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT er.Rate FROM ExchangeRates er
            JOIN Currencies bc ON er.BaseCurrencyId = bc.ID
            JOIN Currencies tc ON er.TargetCurrencyId = tc.ID
            WHERE bc.Code = ? AND tc.Code = ?
        ''', (base_code, target_code))
        row = cursor.fetchone()
        return row['Rate'] if row else None


    def _build_exchange_response(self, from_code: str, to_code: str, rate: float, amount: float, converted: float) -> Dict[str, Any]:
        base_currency = self.get_currency_by_code(from_code)
        target_currency = self.get_currency_by_code(to_code)
        return {
            'baseCurrency': base_currency,
            'targetCurrency': target_currency,
            'rate': rate,
            'amount': amount,
            'convertedAmount': converted
        }