from http.server import HTTPServer

from src.controller.server import SimpleHandler


if __name__ == '__main__':
    server = HTTPServer(('localhost', 8000), SimpleHandler)
    print("Сервер запущен на http://localhost:8000")
    server.serve_forever()