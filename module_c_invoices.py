"""
Module C: Invoices
"""

from flask import Flask, request, jsonify
from database import InvoiceRepository, PatientRepository, ServiceRepository, MedicineRepository, init_database

app = Flask(__name__)

init_database()

@app.route('/invoices', methods=['GET'])
def get_invoices():
    invoices = InvoiceRepository.get_all()
    return jsonify(invoices)

@app.route('/invoices/create', methods=['POST'])
def create_invoice():
    data = request.get_json()
    
    patient_name = data.get('patient_name', 'Unknown')
    service_ids = data.get('service_ids', [])
    medicine_ids = data.get('medicine_ids', [])
    
    names = patient_name.split()
    first_name = names[0] if len(names) > 0 else "Unknown"
    last_name = names[1] if len(names) > 1 else "Unknown"
    
    patient_id = PatientRepository.get_or_create(first_name, last_name)
    
    services = []
    for sid in service_ids:
        s = ServiceRepository.get_by_id(sid)
        if s:
            services.append(s)
    
    medicines = []
    for mid in medicine_ids:
        all_meds = MedicineRepository.get_all()
        m = next((x for x in all_meds if x['Id'] == mid), None)
        if m:
            medicines.append(m)
    
    total = sum(s['Price'] for s in services) + sum(m['Price'] for m in medicines)
    
    if total == 0:
        return jsonify({"error": "No services or medicines selected"}), 400
    
    invoice_id = InvoiceRepository.create(patient_id, total)
    
    for s in services:
        InvoiceRepository.add_item(invoice_id, 'service', s['Id'], s['Name'], float(s['Price']))
    
    for m in medicines:
        InvoiceRepository.add_item(invoice_id, 'medicine', m['Id'], m['Name'], float(m['Price']))
    
    return jsonify({
        "id": invoice_id,
        "patient": patient_name,
        "total": total,
        "status": "unpaid"
    }), 201

@app.route('/invoices/<int:invoice_id>/pay', methods=['POST'])
def pay_invoice(invoice_id):
    InvoiceRepository.pay(invoice_id)
    return jsonify({"status": "paid", "id": invoice_id})

@app.route('/health', methods=['GET'])
def health():
    return {"status": "ok", "module": "C", "database": "connected"}

if __name__ == '__main__':
    print("=" * 50)
    print("Module C (Invoices)")
    print("Port: 3000")
    print("Endpoints:")
    print("  GET  /invoices           - list of invoices")
    print("  POST /invoices/create    - create invoice")
    print("  POST /invoices/<id>/pay  - pay invoice")
    print("  GET  /health             - health check")
    print("=" * 50)
    app.run(host='0.0.0.0', port=3000, debug=True)
