from http.server import HTTPServer

from src.backend.controller.server import SimpleHandler
 
from src.backend.db.init_db import DatabaseInitializer


initializer = DatabaseInitializer()
initializer.create_tables()


if __name__ == '__main__':
    server = HTTPServer(('localhost', 8000), SimpleHandler)
    print("Сервер запущен на http://localhost:8000")
    server.serve_forever()
    
    
#   python -m src.backend.main