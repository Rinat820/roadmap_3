from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import urllib.parse

from src.models.model import DatabaseModel  
from src.controller.error_handler import ErrorHandler


db = DatabaseModel()
db.conn.execute('PRAGMA journal_mode=WAL;')  
db.conn.execute('PRAGMA synchronous=NORMAL;')  


class SimpleHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.db = db  
        super().__init__(*args, **kwargs)

    @ErrorHandler.handle_errors
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = parsed.query
        
        if path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header('Access-Control-Allow-Origin', '*')#
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, PATCH, OPTIONS')#
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')#
            self.end_headers()
            body = "<h1>Hello World!</h1><p>Сервер работает.</p>"
            self.wfile.write(body.encode('utf-8'))
        
        elif path == '/currencies':
            currencies = self.db.get_all_currencies()
            self.send_json_response(200, currencies)
        
        elif path.startswith('/currency/'):
            parts = path.split('/')
            if len(parts) == 3 and parts[1] == 'currency' and len(parts[2]) == 3 and parts[2].isupper():
                currency_code = parts[2]
                currency = self.db.get_currency_by_code(currency_code)
                self.send_json_response(200, currency)
            else:
                raise ValueError('Некорректный формат пути: ожидается /currency/{КОД_3_БУКВЫ}')
        
        elif path == '/exchangeRates':
            exchange_rates = self.db.get_all_exchange_rates()
            self.send_json_response(200, exchange_rates)
        
        elif path.startswith('/exchangeRate/'):
            parts = path.split('/')
            if len(parts) == 3 and parts[1] == 'exchangeRate' and len(parts[2]) == 6 and parts[2].isupper():
                pair = parts[2]
                exchange_rate = self.db.get_exchange_rate_by_pair(pair)
                self.send_json_response(200, exchange_rate)
            else:
                raise ValueError('Некорректный формат пути: ожидается /exchangeRate/{ПАРА_6_БУКВ}')
        
        elif path == '/exchange':
            if not query:
                raise ValueError('Отсутствуют query-параметры для /exchange')
            params = urllib.parse.parse_qs(query)
            from_currency = params.get('from', [None])[0]
            to_currency = params.get('to', [None])[0]
            amount_str = params.get('amount', [None])[0]
            if not all([from_currency, to_currency, amount_str]):
                raise ValueError('Отсутствуют обязательные параметры: from, to и amount')
            try:
                amount = float(amount_str)
            except ValueError:
                raise ValueError('Некорректное значение amount: ожидается число')
            result = self.db.calculate_exchange(from_currency, to_currency, amount)
            self.send_json_response(200, result)
        
        else:
            self.send_json_response(404, 'Эндпоинт не найден')
            
    @ErrorHandler.handle_errors
    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        
        if path == '/currencies':
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                raise ValueError('Отсутствует тело запроса')
            post_data = self.rfile.read(content_length).decode('utf-8')
            params = urllib.parse.parse_qs(post_data)
            name = params.get('name', [None])[0]
            code = params.get('code', [None])[0]
            sign = params.get('sign', [None])[0]
            currency = self.db.add_currency(name, code, sign)
            self.send_json_response(201, currency)
        
        elif path == '/exchangeRates':
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                raise ValueError('Отсутствует тело запроса')
            post_data = self.rfile.read(content_length).decode('utf-8')
            params = urllib.parse.parse_qs(post_data)
            base_currency_code = params.get('baseCurrencyCode', [None])[0]
            target_currency_code = params.get('targetCurrencyCode', [None])[0]
            rate_str = params.get('rate', [None])[0]
            if not rate_str:
                raise ValueError('Отсутствует нужное поле формы (rate)')
            try:
                rate = float(rate_str)
            except ValueError:
                raise ValueError('Некорректное значение rate: ожидается число')
            exchange_rate = self.db.add_exchange_rate(base_currency_code, target_currency_code, rate)
            self.send_json_response(201, exchange_rate)
        
        else:
            self.send_json_response(404, 'Эндпоинт не найден')
        
    @ErrorHandler.handle_errors
    def do_PATCH(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        
        if path.startswith('/exchangeRate/'):
            parts = path.split('/')
            if len(parts) == 3 and parts[1] == 'exchangeRate' and len(parts[2]) == 6 and parts[2].isupper():
                pair = parts[2]
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length == 0:
                    raise ValueError('Отсутствует тело запроса')
                post_data = self.rfile.read(content_length).decode('utf-8')
                params = urllib.parse.parse_qs(post_data)
                rate_str = params.get('rate', [None])[0]
                if not rate_str:
                    raise ValueError('Отсутствует нужное поле формы (rate)')
                try:
                    rate = float(rate_str)
                except ValueError:
                    raise ValueError('Некорректное значение rate: ожидается число')
                updated_rate = self.db.update_exchange_rate(pair, rate)
                self.send_json_response(200, updated_rate)
            else:
                raise ValueError('Некорректный формат пути: ожидается /exchangeRate/{ПАРА_6_БУКВ}')
        
        else:
            self.send_json_response(404, 'Эндпоинт не найден')

    def send_json_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')#
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PATCH, OPTIONS')#
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')#
        self.end_headers()
        if isinstance(data, str):
            response = {'message': data}
        else:
            response = data
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
    
    
    @ErrorHandler.handle_errors
    def do_OPTIONS(self):
        """Обрабатывает preflight-запросы CORS для браузера (например, перед POST/PATCH). Возвращает 200 без тела."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')  # Разрешает запросы с любого домена (для теста; в проде укажите конкретный)
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PATCH, OPTIONS')  # Разрешенные методы
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')  # Разрешенные заголовки (для форм)
        self.end_headers()    


if __name__ == '__main__':
    server = HTTPServer(('localhost', 8000), SimpleHandler)
    print("Сервер запущен на http://localhost:8000")
    server.serve_forever()