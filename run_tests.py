#!/usr/bin/env python3
"""
Run all tests: unit, integration, and E2E
"""

import subprocess
import sys
import os


def run_command(cmd, description):
    """Run command and print result"""
    print(f"\n{'='*60}")
    print(f"RUNNING: {description}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, shell=True)
    
    if result.returncode == 0:
        print(f"✅ {description} PASSED")
    else:
        print(f"❌ {description} FAILED")
    
    return result.returncode


def main():
    print("\n" + "="*60)
    print("CLINIC MIS - TEST SUITE")
    print("="*60)
    
    results = []
    
    # Check if modules are running
    print("\nChecking module availability...")
    import requests
    modules_ok = True
    
    for name, url in [("Module A", "http://localhost:5001/health"),
                      ("Module B", "http://localhost:5002/medicines"),
                      ("Module C", "http://localhost:3000/invoices")]:
        try:
            resp = requests.get(url, timeout=3)
            if resp.status_code < 500:
                print(f"  ✅ {name} is running")
            else:
                print(f"  ⚠️ {name} returned {resp.status_code}")
        except:
            print(f"  ❌ {name} is NOT running")
            modules_ok = False
    
    if not modules_ok:
        print("\n⚠️ Some modules are not running!")
        print("Please start all modules before running integration tests:")
        print("  python module_a_simple.py")
        print("  python module_b_appointments_medicines.py")
        print("  python module_c_simple.py")
        
        response = input("\nContinue with unit tests only? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Run unit tests
    ret = run_command(
        "python -m pytest tests/unit/ -v --tb=short",
        "Unit Tests"
    )
    results.append(("Unit Tests", ret))
    
    # Run integration tests (only if modules are running)
    if modules_ok:
        ret = run_command(
            "python -m pytest tests/integration/ -v --tb=short",
            "Integration Tests"
        )
        results.append(("Integration Tests", ret))
        
        # Run E2E tests
        ret = run_command(
            "python -m pytest tests/e2e/ -v -s --tb=short",
            "E2E Tests"
        )
        results.append(("E2E Tests", ret))
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    all_passed = True
    for name, ret in results:
        status = "✅ PASSED" if ret == 0 else "❌ FAILED"
        print(f"  {name}: {status}")
        if ret != 0:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️ SOME TESTS FAILED")
    print("="*60)
    
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
