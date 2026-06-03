"""
Optimized Module A with Caching
"""

from flask import Flask, jsonify
from flask_cors import CORS
import time
from functools import wraps

app = Flask(__name__)
CORS(app)

# Simple cache implementation
cache = {}
CACHE_TTL = 60  # seconds

def cached(ttl=CACHE_TTL):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}_{args}_{kwargs}"
            if cache_key in cache:
                data, timestamp = cache[cache_key]
                if time.time() - timestamp < ttl:
                    print(f"  Cache HIT for {func.__name__}")
                    return data
            result = func(*args, **kwargs)
            cache[cache_key] = (result, time.time())
            print(f"  Cache MISS for {func.__name__}")
            return result
        return wrapper
    return decorator

# Data
services = [
    {"Id": 1, "Name": "Therapist Consultation", "Price": 1500, "Category": "Consultation"},
    {"Id": 2, "Name": "Ultrasound", "Price": 2500, "Category": "Diagnostics"},
    {"Id": 3, "Name": "Blood Test", "Price": 800, "Category": "Laboratory"},
]

licenses = [
    {"Id": 1, "Name": "Medical License", "Status": "active", "LicenseNumber": "LIC-001"},
]

@app.route('/services', methods=['GET'])
@cached(ttl=60)
def get_services():
    return jsonify(services)

@app.route('/licenses', methods=['GET'])
@cached(ttl=300)
def get_licenses():
    return jsonify(licenses)

@app.route('/health', methods=['GET'])
def health():
    return {"status": "ok", "module": "A", "caching": "enabled"}

if __name__ == '__main__':
    print("Optimized Module A with Caching running on port 5001")
    app.run(host='0.0.0.0', port=5001, debug=True)
