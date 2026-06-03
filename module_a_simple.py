from flask import Flask, jsonify
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)

# Use English names to avoid encoding issues
services = [
    {"Id": 1, "Name": "Therapist Consultation", "Price": 1500, "Category": "Consultation"},
    {"Id": 2, "Name": "Ultrasound", "Price": 2500, "Category": "Diagnostics"},
    {"Id": 3, "Name": "Blood Test", "Price": 800, "Category": "Laboratory"},
    {"Id": 4, "Name": "Cardiologist Visit", "Price": 2000, "Category": "Consultation"},
    {"Id": 5, "Name": "MRI Scan", "Price": 5000, "Category": "Diagnostics"}
]

licenses = [
    {"Id": 1, "Name": "Medical License", "Status": "active", "LicenseNumber": "LIC-001"},
    {"Id": 2, "Name": "Telemedicine License", "Status": "active", "LicenseNumber": "LIC-002"}
]

@app.route('/services', methods=['GET'])
def get_services():
    response = jsonify(services)
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response

@app.route('/licenses', methods=['GET'])
def get_licenses():
    response = jsonify(licenses)
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response

@app.route('/health', methods=['GET'])
def health():
    return {"status": "ok", "module": "A"}

if __name__ == '__main__':
    print("=" * 50)
    print("Module A (Simple) running on http://0.0.0.0:5001")
    print("Services available:")
    for s in services:
        print(f"  {s['Id']}. {s['Name']} - ${s['Price']}")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5001, debug=True)
