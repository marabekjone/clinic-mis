from flask import Flask, send_file, jsonify, request
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# API endpoints
API_A = "http://localhost:5001"
API_B = "http://localhost:5002"
API_C = "http://localhost:3000"

@app.route('/')
def index():
    return send_file('templates/index.html')

# Proxy endpoints
@app.route('/api/services', methods=['GET'])
def proxy_services():
    resp = requests.get(f"{API_A}/services")
    return jsonify(resp.json())

@app.route('/api/medicines', methods=['GET'])
def proxy_medicines():
    resp = requests.get(f"{API_B}/medicines")
    return jsonify(resp.json())

@app.route('/api/invoices', methods=['GET'])
def proxy_invoices():
    resp = requests.get(f"{API_C}/invoices")
    return jsonify(resp.json())

@app.route('/api/invoices/create', methods=['POST'])
def proxy_create_invoice():
    resp = requests.post(f"{API_C}/invoices/create", json=request.get_json())
    return jsonify(resp.json()), resp.status_code

@app.route('/api/invoices/<int:inv_id>/pay', methods=['POST'])
def proxy_pay_invoice(inv_id):
    resp = requests.post(f"{API_C}/invoices/{inv_id}/pay")
    return jsonify(resp.json()), resp.status_code

if __name__ == '__main__':
    print("=" * 50)
    print("Frontend Server with Proxy")
    print("URL: http://localhost:8080")
    print("Proxying to:")
    print(f"  Module A: {API_A}")
    print(f"  Module B: {API_B}")
    print(f"  Module C: {API_C}")
    print("=" * 50)
    app.run(host='0.0.0.0', port=8080, debug=True)
