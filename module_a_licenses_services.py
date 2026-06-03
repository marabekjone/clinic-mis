"""
Module A: Licenses and Services
"""

from flask import Flask, jsonify, request
from database import ServiceRepository, LicenseRepository, init_database

app = Flask(__name__)

init_database()

@app.route('/services', methods=['GET'])
def get_services():
    services = ServiceRepository.get_all()
    return jsonify(services)

@app.route('/services/<int:service_id>', methods=['GET'])
def get_service(service_id):
    service = ServiceRepository.get_by_id(service_id)
    if service:
        return jsonify(service)
    return jsonify({"error": "Service not found"}), 404

@app.route('/licenses', methods=['GET'])
def get_licenses():
    licenses = LicenseRepository.get_all()
    return jsonify(licenses)

@app.route('/health', methods=['GET'])
def health():
    return {"status": "ok", "module": "A", "database": "connected"}

if __name__ == '__main__':
    print("=" * 50)
    print("Module A (Licenses + Services)")
    print("Port: 5001")
    print("Endpoints:")
    print("  GET  /services      - list of services")
    print("  GET  /services/<id> - service by ID")
    print("  GET  /licenses      - list of licenses")
    print("  GET  /health        - health check")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5001, debug=True)
