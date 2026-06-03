# Модуль А: Лицензии и Услуги
from flask import Flask, jsonify

app = Flask(__name__)

licenses = [
    {"id": 1, "name": "Медицинская лицензия", "status": "активна"},
    {"id": 2, "name": "Лицензия на телемедицину", "status": "активна"}
]

services = [
    {"id": 1, "name": "Приём терапевта", "price": 1500},
    {"id": 2, "name": "УЗИ", "price": 2500},
    {"id": 3, "name": "Анализ крови", "price": 800}
]

@app.route('/licenses', methods=['GET'])
def get_licenses():
    return jsonify(licenses)

@app.route('/services', methods=['GET'])
def get_services():
    return jsonify(services)

if __name__ == '__main__':
    print("Модуль А запущен на http://localhost:5001")
    print("Доступные эндпоинты:")
    print("  GET /licenses - список лицензий")
    print("  GET /services - список услуг")
    app.run(port=5001, debug=True)