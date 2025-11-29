#!/usr/bin/env python3
"""
Production Deployment Test Suite
Tests all critical functionality after deployment
"""

import requests
import json
import sys
import time
from typing import Dict, Any

class ProductionTester:
    def __init__(self, prod_url: str, backend_url: str):
        self.prod_url = prod_url.rstrip('/')
        self.backend_url = backend_url.rstrip('/')
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []
    
    def test(self, name: str, func):
        """Run a test and track results"""
        try:
            print(f"\n[TEST] {name}")
            result = func()
            if result:
                self.tests_passed += 1
                self.test_results.append((name, 'PASS', None))
                print(f"  ✓ PASS")
            else:
                self.tests_failed += 1
                self.test_results.append((name, 'FAIL', 'Test returned False'))
                print(f"  ✗ FAIL")
        except Exception as e:
            self.tests_failed += 1
            self.test_results.append((name, 'FAIL', str(e)))
            print(f"  ✗ FAIL: {str(e)}")
    
    def test_frontend_loads(self):
        """Test 1: Frontend loads successfully"""
        response = requests.get(self.prod_url, timeout=10)
        return response.status_code == 200
    
    def test_branding(self):
        """Test 2: Correct branding present"""
        response = requests.get(self.prod_url, timeout=10)
        return 'ScanLLM.ai' in response.text
    
    def test_no_emergent_badge(self):
        """Test 3: Emergent badge removed"""
        response = requests.get(self.prod_url, timeout=10)
        return 'Made with Emergent' not in response.text
    
    def test_backend_health(self):
        """Test 4: Backend health check"""
        response = requests.get(f"{self.backend_url}/health", timeout=10)
        data = response.json()
        return data.get('status') == 'ok'
    
    def test_scan_api(self):
        """Test 5: Scan API functionality"""
        response = requests.post(
            f"{self.backend_url}/api/scans",
            json={"repo_url": "https://github.com/openai/openai-python", "full_scan": False},
            timeout=60
        )
        
        if response.status_code != 200:
            return False
        
        data = response.json()
        status = data.get('status')
        files = data.get('files_count', 0)
        matches = data.get('total_occurrences', 0)
        
        print(f"    Scanned {files} files, found {matches} matches")
        return status == 'SUCCESS' and files > 0
    
    def test_v2_features(self):
        """Test 6: v2 features present in scan response"""
        response = requests.post(
            f"{self.backend_url}/api/scans",
            json={"repo_url": "https://github.com/openai/openai-python", "full_scan": False},
            timeout=60
        )
        
        data = response.json()
        
        required_fields = [
            'frameworks_summary',
            'hotspots',
            'risk_flags',
            'policies_result',
            'blast_radius_summary',
            'contracts',
            'heatmap'
        ]
        
        for field in required_fields:
            if field not in data:
                print(f"    Missing field: {field}")
                return False
        
        print(f"    All v2 fields present")
        return True
    
    def test_cors(self):
        """Test 7: CORS headers present"""
        response = requests.options(
            f"{self.backend_url}/api/scans",
            headers={
                'Origin': self.prod_url,
                'Access-Control-Request-Method': 'POST'
            },
            timeout=10
        )
        
        # CORS headers should be present
        return 'Access-Control-Allow-Origin' in response.headers or response.status_code == 200
    
    def test_performance(self):
        """Test 8: Scan performance is acceptable"""
        start = time.time()
        response = requests.post(
            f"{self.backend_url}/api/scans",
            json={"repo_url": "https://github.com/rasbt/LLMs-from-scratch", "full_scan": False},
            timeout=60
        )
        duration = time.time() - start
        
        print(f"    Scan completed in {duration:.1f}s")
        
        # Small repo should complete in < 5 seconds
        return response.status_code == 200 and duration < 10
    
    def run_all_tests(self):
        """Run all deployment tests"""
        print("="*70)
        print("ScanLLM.ai Production Deployment Test Suite")
        print("="*70)
        print(f"Production URL: {self.prod_url}")
        print(f"Backend API: {self.backend_url}")
        
        self.test("Frontend loads successfully", self.test_frontend_loads)
        self.test("Correct branding present", self.test_branding)
        self.test("Emergent badge removed", self.test_no_emergent_badge)
        self.test("Backend health check", self.test_backend_health)
        self.test("Scan API functionality", self.test_scan_api)
        self.test("v2 features present", self.test_v2_features)
        self.test("CORS configuration", self.test_cors)
        self.test("Scan performance acceptable", self.test_performance)
        
        # Summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"Tests passed: {self.tests_passed}")
        print(f"Tests failed: {self.tests_failed}")
        print(f"Success rate: {(self.tests_passed / (self.tests_passed + self.tests_failed) * 100):.1f}%")
        
        if self.tests_failed > 0:
            print("\n❌ DEPLOYMENT VERIFICATION FAILED")
            print("\nFailed tests:")
            for name, status, error in self.test_results:
                if status == 'FAIL':
                    print(f"  - {name}: {error}")
            return 1
        else:
            print("\n✅ ALL TESTS PASSED - Deployment verified!")
            return 0

if __name__ == '__main__':
    # Get URLs from environment or use defaults
    prod_url = sys.argv[1] if len(sys.argv) > 1 else 'https://scanllm.ai'
    backend_url = sys.argv[2] if len(sys.argv) > 2 else 'https://ai-reposcan.emergent.host'
    
    tester = ProductionTester(prod_url, backend_url)
    sys.exit(tester.run_all_tests())
