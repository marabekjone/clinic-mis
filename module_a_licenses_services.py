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

@app.route('/health', methods=['GET'])
def health():
    return {"status": "ok", "module": "A"}

if __name__ == '__main__':
    print("Модуль А запущен на http://0.0.0.0:5001")
    print("Доступные эндпоинты:")
    print("  GET /licenses - список лицензий")
    print("  GET /services - список услуг")
    print("  GET /health - проверка здоровья")
    # ВАЖНО: host='0.0.0.0' для Docker
    app.run(host='0.0.0.0', port=5001, debug=True)
