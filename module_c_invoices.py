from flask import Flask, request, jsonify

app = Flask(__name__)

invoices = []
next_id = 1

SERVICES = {
    1: {"name": "Приём терапевта", "price": 1500},
    2: {"name": "УЗИ", "price": 2500},
    3: {"name": "Анализ крови", "price": 800}
}

MEDICINES = {
    1: {"name": "Амоксициллин", "price": 300},
    2: {"name": "Парацетамол", "price": 150},
    3: {"name": "Нурофен", "price": 200}
}

@app.route('/')
def root():
    return {"message": "МИС Модуль В - Счета", "status": "ok"}

@app.route('/health', methods=['GET'])
def health():
    return {"status": "ok", "module": "C"}

@app.route('/invoices/create', methods=['POST'])
def create_invoice():
    global next_id
    data = request.get_json()
    
    service_ids = data.get("service_ids", [])
    medicine_ids = data.get("medicine_ids", [])
    patient_name = data.get("patient_name", "Не указан")
    
    total = 0
    items = []
    
    for sid in service_ids:
        if sid in SERVICES:
            total += SERVICES[sid]["price"]
            items.append(SERVICES[sid])
    
    for mid in medicine_ids:
        if mid in MEDICINES:
            total += MEDICINES[mid]["price"]
            items.append(MEDICINES[mid])
    
    invoice = {
        "id": next_id,
        "patient": patient_name,
        "items": items,
        "total": total,
        "status": "не оплачен",
        "created_at": "2026-06-03"
    }
    invoices.append(invoice)
    next_id += 1
    
    return jsonify(invoice), 201

@app.route('/invoices', methods=['GET'])
def list_invoices():
    return jsonify(invoices)

@app.route('/invoices/<int:inv_id>/pay', methods=['POST'])
def pay_invoice(inv_id):
    inv = next((i for i in invoices if i["id"] == inv_id), None)
    if not inv:
        return jsonify({"error": "Счёт не найден"}), 404
    inv["status"] = "оплачен"
    return jsonify(inv)

if __name__ == '__main__':
    print("Модуль В запущен на http://0.0.0.0:3000")
    print("Доступные эндпоинты:")
    print("  GET /health - проверка здоровья")
    print("  POST /invoices/create - создать счёт")
    print("  GET /invoices - список счетов")
    print("  POST /invoices/{id}/pay - оплатить счёт")
    # ВАЖНО: host='0.0.0.0' для Docker
    app.run(host='0.0.0.0', port=3000, debug=True)
