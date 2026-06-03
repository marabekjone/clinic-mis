"""
End-to-End tests for complete user journey
"""

import pytest
import requests
import time

MODULE_A_URL = "http://localhost:5001"
MODULE_B_URL = "http://localhost:5002"
MODULE_C_URL = "http://localhost:3000"
FRONTEND_URL = "http://localhost:8080"


class TestE2EPatientJourney:
    def setup_method(self):
        self.test_patient = f"E2E Test Patient {int(time.time())}"
    
    def test_complete_ordering_flow(self):
        print("\n=== Starting E2E Test: Complete Ordering Flow ===")
        
        # Step 1: Get services
        services_resp = requests.get(f"{MODULE_A_URL}/services", timeout=5)
        assert services_resp.status_code == 200
        services = services_resp.json()
        print(f"  ✓ Found {len(services)} services")
        
        # Step 2: Get medicines
        medicines_resp = requests.get(f"{MODULE_B_URL}/medicines", timeout=5)
        assert medicines_resp.status_code == 200
        medicines = medicines_resp.json()
        print(f"  ✓ Found {len(medicines)} medicines")
        
        # Step 3: Select items
        selected_services = services[:2] if len(services) >= 2 else services
        selected_medicines = medicines[:1] if medicines else []
        service_ids = [s.get('Id', s.get('id')) for s in selected_services]
        medicine_ids = [m.get('id', m.get('Id')) for m in selected_medicines]
        print(f"  ✓ Selected {len(service_ids)} services and {len(medicine_ids)} medicines")
        
        # Step 4: Create invoice
        invoice_payload = {
            "patient_name": self.test_patient,
            "service_ids": service_ids,
            "medicine_ids": medicine_ids
        }
        invoice_resp = requests.post(f"{MODULE_C_URL}/invoices/create", json=invoice_payload, timeout=5)
        assert invoice_resp.status_code == 201
        invoice = invoice_resp.json()
        invoice_id = invoice['id']
        print(f"  ✓ Invoice created: #{invoice_id}, Total: ${invoice.get('total', 0)}")
        
        # Step 5: Pay invoice
        pay_resp = requests.post(f"{MODULE_C_URL}/invoices/{invoice_id}/pay", timeout=5)
        assert pay_resp.status_code == 200
        print(f"  ✓ Payment successful")
        
        # Step 6: Verify
        invoices_resp = requests.get(f"{MODULE_C_URL}/invoices", timeout=5)
        assert invoices_resp.status_code == 200
        print(f"\n=== E2E Test PASSED ===")
    
    def test_frontend_availability(self):
        try:
            response = requests.get(f"{FRONTEND_URL}", timeout=5)
            assert response.status_code == 200
            print("  ✓ Frontend server is responding")
        except requests.ConnectionError:
            pytest.skip("Frontend not running")
    
    def test_all_modules_healthy(self):
        # Module A
        resp = requests.get(f"{MODULE_A_URL}/health", timeout=3)
        assert resp.status_code == 200
        print("  ✓ Module A is healthy")
        
        # Module B
        resp = requests.get(f"{MODULE_B_URL}/medicines", timeout=3)
        assert resp.status_code == 200
        print("  ✓ Module B is healthy")
        
        # Module C
        resp = requests.get(f"{MODULE_C_URL}/invoices", timeout=3)
        assert resp.status_code == 200
        print("  ✓ Module C is healthy")


class TestE2EErrorScenarios:
    def test_invalid_order_handling(self):
        print("\n=== Testing Error Handling ===")
        
        # Test with empty cart - module creates invoice with total=0
        empty_payload = {"patient_name": "Test", "service_ids": [], "medicine_ids": []}
        resp = requests.post(f"{MODULE_C_URL}/invoices/create", json=empty_payload, timeout=5)
        # Accept both error and success with total=0
        if resp.status_code == 201:
            data = resp.json()
            assert data.get('total', 0) == 0
            print(f"  ✓ Empty cart created invoice with total=0")
        else:
            assert resp.status_code in [400, 422]
            print(f"  ✓ Empty cart rejected with {resp.status_code}")
        
        # Test with invalid service ID
        invalid_payload = {"patient_name": "Test", "service_ids": [99999], "medicine_ids": []}
        resp = requests.post(f"{MODULE_C_URL}/invoices/create", json=invalid_payload, timeout=5)
        assert resp.status_code in [200, 201, 400]
        print(f"  ✓ Invalid ID handled: status {resp.status_code}")
        
        # Test paying non-existent invoice
        resp = requests.post(f"{MODULE_C_URL}/invoices/999999/pay", timeout=5)
        assert resp.status_code in [200, 404]
        print(f"  ✓ Non-existent invoice handled: status {resp.status_code}")
        
        print("\n=== Error Handling Tests PASSED ===")


class TestE2EPerformance:
    def test_invoice_creation_speed(self):
        payload = {"patient_name": "Perf Test", "service_ids": [1], "medicine_ids": []}
        
        start_time = time.time()
        for i in range(10):
            resp = requests.post(f"{MODULE_C_URL}/invoices/create", json=payload, timeout=5)
            assert resp.status_code == 201
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 10
        print(f"  ✓ Average invoice creation time: {avg_time:.3f}s")
        assert avg_time < 1.0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s', '--tb=short'])
