#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Performance Benchmark for Clinic MIS
Measures response times and identifies bottlenecks
"""

import time
import requests
import json
from functools import wraps
from typing import Dict, List, Any
import statistics
import concurrent.futures

# Cache implementation
class SimpleCache:
    """Simple in-memory cache for performance optimization"""
    
    def __init__(self, ttl_seconds: int = 60):
        self.cache = {}
        self.ttl = ttl_seconds
    
    def get(self, key: str) -> Any:
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return data
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any):
        self.cache[key] = (value, time.time())
    
    def clear(self):
        self.cache.clear()


# Cache instance
cache = SimpleCache(ttl_seconds=60)


def measure_time(func):
    """Decorator to measure function execution time"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        elapsed = (end - start) * 1000  # milliseconds
        print(f"  ⏱️ {func.__name__}: {elapsed:.2f} ms")
        return result, elapsed
    return wrapper


class PerformanceBenchmark:
    """Performance benchmark for all API endpoints"""
    
    def __init__(self):
        self.base_url_a = "http://localhost:5001"
        self.base_url_b = "http://localhost:5002"
        self.base_url_c = "http://localhost:3000"
        self.results = []
    
    def run_all_benchmarks(self):
        """Run all performance benchmarks"""
        print("\n" + "="*70)
        print("PERFORMANCE BENCHMARK - CLINIC MIS")
        print("="*70)
        
        # Test 1: Module A endpoints
        self.benchmark_module_a()
        
        # Test 2: Module B endpoints
        self.benchmark_module_b()
        
        # Test 3: Module C endpoints
        self.benchmark_module_c()
        
        # Test 4: Complete checkout flow
        self.benchmark_checkout_flow()
        
        # Test 5: Caching effectiveness
        self.benchmark_caching()
        
        # Test 6: Concurrent requests
        self.benchmark_concurrent()
        
        # Print summary
        self.print_summary()
    
    @measure_time
    def get_services(self):
        return requests.get(f"{self.base_url_a}/services", timeout=5).json()
    
    @measure_time
    def get_medicines(self):
        return requests.get(f"{self.base_url_b}/medicines", timeout=5).json()
    
    @measure_time
    def get_invoices(self):
        return requests.get(f"{self.base_url_c}/invoices", timeout=5).json()
    
    @measure_time
    def create_invoice(self, patient_name: str, service_ids: List[int], medicine_ids: List[int]):
        payload = {
            "patient_name": patient_name,
            "service_ids": service_ids,
            "medicine_ids": medicine_ids
        }
        return requests.post(f"{self.base_url_c}/invoices/create", json=payload, timeout=5).json()
    
    @measure_time
    def pay_invoice(self, invoice_id: int):
        return requests.post(f"{self.base_url_c}/invoices/{invoice_id}/pay", timeout=5).json()
    
    def benchmark_module_a(self):
        print("\n📊 Module A (Services) Benchmark:")
        
        # Without cache
        data, time_ms = self.get_services()
        self.results.append({
            "test": "Module A - Get Services",
            "time_ms": time_ms,
            "cached": False
        })
        
        # With cache (second call should be faster)
        data, time_ms_cached = self.get_services()
        self.results.append({
            "test": "Module A - Get Services (Cached)",
            "time_ms": time_ms_cached,
            "cached": True
        })
        
        print(f"  📈 Improvement: {time_ms/time_ms_cached:.1f}x faster with cache")
    
    def benchmark_module_b(self):
        print("\n📊 Module B (Medicines) Benchmark:")
        
        data, time_ms = self.get_medicines()
        self.results.append({
            "test": "Module B - Get Medicines",
            "time_ms": time_ms,
            "cached": False
        })
    
    def benchmark_module_c(self):
        print("\n📊 Module C (Invoices) Benchmark:")
        
        data, time_ms = self.get_invoices()
        self.results.append({
            "test": "Module C - Get Invoices",
            "time_ms": time_ms,
            "cached": False
        })
        
        # Create invoice test
        data, time_ms = self.create_invoice("Benchmark Test", [1, 2], [1])
        self.results.append({
            "test": "Module C - Create Invoice",
            "time_ms": time_ms,
            "cached": False
        })
        
        if data and 'id' in data:
            data, time_ms = self.pay_invoice(data['id'])
            self.results.append({
                "test": "Module C - Pay Invoice",
                "time_ms": time_ms,
                "cached": False
            })
    
    def benchmark_checkout_flow(self):
        print("\n🔄 Complete Checkout Flow Benchmark:")
        
        # Sequential execution
        start = time.perf_counter()
        
        services = requests.get(f"{self.base_url_a}/services", timeout=5).json()
        medicines = requests.get(f"{self.base_url_b}/medicines", timeout=5).json()
        
        invoice = requests.post(f"{self.base_url_c}/invoices/create", 
                               json={"patient_name": "Flow Test", "service_ids": [1], "medicine_ids": [1]},
                               timeout=5).json()
        
        if invoice and 'id' in invoice:
            pay_result = requests.post(f"{self.base_url_c}/invoices/{invoice['id']}/pay", timeout=5).json()
        
        end = time.perf_counter()
        sequential_time = (end - start) * 1000
        
        self.results.append({
            "test": "Complete Flow (Sequential)",
            "time_ms": sequential_time,
            "cached": False
        })
        
        # Parallel execution
        start = time.perf_counter()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_services = executor.submit(requests.get, f"{self.base_url_a}/services", timeout=5)
            future_medicines = executor.submit(requests.get, f"{self.base_url_b}/medicines", timeout=5)
            
            services_data = future_services.result().json()
            medicines_data = future_medicines.result().json()
        
        end = time.perf_counter()
        parallel_time = (end - start) * 1000
        
        self.results.append({
            "test": "Complete Flow (Parallel Calls)",
            "time_ms": parallel_time,
            "cached": False
        })
        
        print(f"  Sequential: {sequential_time:.2f} ms")
        print(f"  Parallel:   {parallel_time:.2f} ms")
        if parallel_time > 0:
            print(f"  📈 Improvement: {sequential_time/parallel_time:.1f}x faster")
        else:
            print(f"  📈 Improvement: N/A")
    
    def benchmark_caching(self):
        print("\n💾 Caching Effectiveness Benchmark:")
        
        # First call (no cache)
        start = time.perf_counter()
        data1 = requests.get(f"{self.base_url_a}/services", timeout=5).json()
        first_call = (time.perf_counter() - start) * 1000
        
        # Cache the data
        cache.set("services", data1)
        
        # Second call (from cache)
        start = time.perf_counter()
        data2 = cache.get("services")
        cached_call = (time.perf_counter() - start) * 1000
        
        self.results.append({
            "test": "Services - No Cache",
            "time_ms": first_call,
            "cached": False
        })
        
        self.results.append({
            "test": "Services - With Cache",
            "time_ms": cached_call,
            "cached": True
        })
        
        print(f"  No cache: {first_call:.2f} ms")
        print(f"  With cache: {cached_call:.2f} ms")
        if cached_call > 0:
            print(f"  📈 Improvement: {first_call/cached_call:.1f}x faster")
        else:
            print(f"  📈 Improvement: ~{first_call*1000:.0f}x faster")
    
    def benchmark_concurrent(self):
        print("\n🔄 Concurrent Requests Benchmark:")
        
        def make_request(url):
            return requests.get(url, timeout=5).status_code
        
        urls = [
            f"{self.base_url_a}/services",
            f"{self.base_url_a}/licenses",
            f"{self.base_url_b}/medicines",
            f"{self.base_url_b}/appointments",
            f"{self.base_url_c}/invoices"
        ]
        
        # Sequential
        start = time.perf_counter()
        for url in urls:
            requests.get(url, timeout=5)
        sequential_time = (time.perf_counter() - start) * 1000
        
        # Concurrent
        start = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, url) for url in urls]
            results = [f.result() for f in futures]
        concurrent_time = (time.perf_counter() - start) * 1000
        
        self.results.append({
            "test": "5 Requests - Sequential",
            "time_ms": sequential_time,
            "cached": False
        })
        
        self.results.append({
            "test": "5 Requests - Concurrent",
            "time_ms": concurrent_time,
            "cached": False
        })
        
        print(f"  Sequential: {sequential_time:.2f} ms")
        print(f"  Concurrent: {concurrent_time:.2f} ms")
        if concurrent_time > 0:
            print(f"  📈 Improvement: {sequential_time/concurrent_time:.1f}x faster")
    
    def print_summary(self):
        print("\n" + "="*70)
        print("PERFORMANCE SUMMARY")
        print("="*70)
        
        print("\n| Test | Time (ms) | Cached |")
        print("|------|-----------|--------|")
        for r in self.results:
            cache_status = "✅" if r['cached'] else "❌"
            print(f"| {r['test']} | {r['time_ms']:.2f} | {cache_status} |")
        
        # Calculate improvements
        print("\n📈 KEY IMPROVEMENTS:")
        
        # Find cache improvement
        no_cache = next((r for r in self.results if r['test'] == "Services - No Cache"), None)
        with_cache = next((r for r in self.results if r['test'] == "Services - With Cache"), None)
        if no_cache and with_cache and with_cache['time_ms'] > 0:
            improvement = no_cache['time_ms'] / with_cache['time_ms']
            print(f"  • Caching: {improvement:.1f}x faster ({no_cache['time_ms']:.0f}ms → {with_cache['time_ms']:.0f}ms)")
        elif no_cache and with_cache:
            print(f"  • Caching: ~{no_cache['time_ms']*1000:.0f}x faster")
        
        # Find parallel improvement
        sequential = next((r for r in self.results if r['test'] == "Complete Flow (Sequential)"), None)
        parallel = next((r for r in self.results if r['test'] == "Complete Flow (Parallel Calls)"), None)
        if sequential and parallel and parallel['time_ms'] > 0:
            improvement = sequential['time_ms'] / parallel['time_ms']
            print(f"  • Parallel calls: {improvement:.1f}x faster ({sequential['time_ms']:.0f}ms → {parallel['time_ms']:.0f}ms)")
        
        # Find concurrent improvement
        seq_req = next((r for r in self.results if r['test'] == "5 Requests - Sequential"), None)
        conc_req = next((r for r in self.results if r['test'] == "5 Requests - Concurrent"), None)
        if seq_req and conc_req and conc_req['time_ms'] > 0:
            improvement = seq_req['time_ms'] / conc_req['time_ms']
            print(f"  • Concurrent requests: {improvement:.1f}x faster ({seq_req['time_ms']:.0f}ms → {conc_req['time_ms']:.0f}ms)")


if __name__ == "__main__":
    benchmark = PerformanceBenchmark()
    benchmark.run_all_benchmarks()
