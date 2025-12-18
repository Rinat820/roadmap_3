import sqlite3
from typing import List, Dict, Any, Optional

from src.models.base_dao import BaseDAO

from src.models.init_db import connection


class CurrencyDAO(BaseDAO):
    def __init__(self, conn = connection):
        self.conn = conn
        
        
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
        if len(name) > 20:
            raise ValueError('Имя валюты должно быть не больше 20 символов')
        cursor = self.conn.cursor()
        try:
            cursor.execute('INSERT INTO Currencies (FullName, Code, Sign) VALUES (?, ?, ?)', (name, code, sign))
            currency_id = cursor.lastrowid
            self.conn.commit()
            return {'id': currency_id, 'name': name, 'code': code, 'sign': sign}
        except sqlite3.IntegrityError:
            raise sqlite3.IntegrityError('Валюта с таким кодом уже существует')