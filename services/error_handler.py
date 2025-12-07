import json
import sqlite3


class ErrorHandler:
    @staticmethod
    def handle_errors(func):
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except ValueError as e:
                if str(e) == "Коды валют пары отсутствуют в адресе":
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"message": str(e)}).encode('utf-8'))
                else:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"message": "Ошибка валидации"}).encode('utf-8'))
            except KeyError as e:
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": str(e)}).encode('utf-8'))
            except sqlite3.IntegrityError as e:
                self.send_response(409)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": str(e)}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Внутренняя ошибка сервера"}).encode('utf-8'))
        return wrapper
