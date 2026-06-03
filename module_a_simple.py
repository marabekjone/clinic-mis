from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

services = [
    {"Id": 1, "Name": "Therapist Consultation", "Price": 1500, "Category": "Consultation"},
    {"Id": 2, "Name": "Ultrasound", "Price": 2500, "Category": "Diagnostics"},
    {"Id": 3, "Name": "Blood Test", "Price": 800, "Category": "Laboratory"},
]

licenses = [
    {"Id": 1, "Name": "Medical License", "Status": "active", "LicenseNumber": "LIC-001"},
    {"Id": 2, "Name": "Telemedicine License", "Status": "active", "LicenseNumber": "LIC-002"},
]

@app.route('/services', methods=['GET'])
def get_services():
    return jsonify(services)

@app.route('/licenses', methods=['GET'])
def get_licenses():
    return jsonify(licenses)

@app.route('/health', methods=['GET'])
def health():
    return {"status": "ok", "module": "A"}

if __name__ == '__main__':
    print("Module A running on http://0.0.0.0:5001")
    app.run(host='0.0.0.0', port=5001, debug=True)
