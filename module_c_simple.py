from flask import Flask, request, jsonify
from flask_cors import CORS
import random
from datetime import datetime

app = Flask(__name__)
CORS(app)

invoices = []
next_id = 1

services_map = {
    1: {"name": "Therapist Consultation", "price": 1500},
    2: {"name": "Ultrasound", "price": 2500},
    3: {"name": "Blood Test", "price": 800},
}

medicines_map = {
    1: {"name": "Amoxicillin", "price": 300},
    2: {"name": "Paracetamol", "price": 150},
}

@app.route('/invoices', methods=['GET'])
def get_invoices():
    return jsonify(invoices)

@app.route('/invoices/create', methods=['POST'])
def create_invoice():
    global next_id
    data = request.get_json()
    
    patient_name = data.get('patient_name', 'Unknown')
    service_ids = data.get('service_ids', [])
    medicine_ids = data.get('medicine_ids', [])
    
    total = 0
    items = []
    
    for sid in service_ids:
        if sid in services_map:
            total += services_map[sid]['price']
            items.append(services_map[sid])
    
    for mid in medicine_ids:
        if mid in medicines_map:
            total += medicines_map[mid]['price']
            items.append(medicines_map[mid])
    
    invoice = {
        "Id": next_id,
        "PatientName": patient_name,
        "TotalAmount": total,
        "Status": "unpaid",
        "Items": items,
        "CreatedAt": datetime.now().isoformat()
    }
    invoices.append(invoice)
    next_id += 1
    
    return jsonify({"id": invoice["Id"], "patient": patient_name, "total": total, "status": "unpaid"}), 201

@app.route('/invoices/<int:invoice_id>/pay', methods=['POST'])
def pay_invoice(invoice_id):
    for inv in invoices:
        if inv["Id"] == invoice_id:
            inv["Status"] = "paid"
            return jsonify({"status": "paid", "id": invoice_id})
    return jsonify({"error": "Invoice not found"}), 404

@app.route('/health', methods=['GET'])
def health():
    return {"status": "ok", "module": "C"}

if __name__ == '__main__':
    print("Module C running on http://0.0.0.0:3000")
    app.run(host='0.0.0.0', port=3000, debug=True)
