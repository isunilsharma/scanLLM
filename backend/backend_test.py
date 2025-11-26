import requests
import sys
import time
from datetime import datetime

class AIDepScannerTester:
    def __init__(self, base_url="https://ai-reposcan.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.scan_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=120):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return False, {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timeout after {timeout}s")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health(self):
        """Test health endpoint"""
        url = f"{self.base_url}/health"
        print(f"\n🔍 Testing Health Check...")
        print(f"   URL: {url}")
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ Health check passed")
                return True
            else:
                print(f"❌ Health check failed - Status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check failed - Error: {str(e)}")
            return False

    def test_get_patterns(self):
        """Test pattern configuration endpoint"""
        success, response = self.run_test(
            "Get Pattern Configuration",
            "GET",
            "config/patterns",
            200
        )
        
        if success and 'frameworks' in response:
            print(f"   Found {len(response['frameworks'])} frameworks configured")
            for fw in response['frameworks'][:3]:
                print(f"   - {fw.get('name', 'unknown')}: {len(fw.get('patterns', []))} patterns")
        
        return success

    def test_create_scan_invalid_url(self):
        """Test scan with invalid URL"""
        success, response = self.run_test(
            "Create Scan with Invalid URL",
            "POST",
            "scans",
            400,
            data={"repo_url": "https://example.com/not-github"}
        )
        return success

    def test_create_scan_valid_repo(self, repo_url):
        """Test scan with valid GitHub repo"""
        print(f"\n⚠️  This test will clone and scan a real repository: {repo_url}")
        print(f"   This may take 30-60 seconds...")
        
        success, response = self.run_test(
            "Create Scan with Valid Repo",
            "POST",
            "scans",
            200,
            data={"repo_url": repo_url},
            timeout=120
        )
        
        if success:
            self.scan_id = response.get('scan_id')
            print(f"   Scan ID: {self.scan_id}")
            print(f"   Status: {response.get('status')}")
            print(f"   Files scanned: {response.get('files_count', 0)}")
            print(f"   Total occurrences: {response.get('total_occurrences', 0)}")
            
            # Test enhanced features
            print(f"\n   📊 Enhanced Features:")
            
            # Test frameworks_summary
            if 'frameworks_summary' in response:
                print(f"   ✅ frameworks_summary present: {len(response['frameworks_summary'])} frameworks")
                for fw in response['frameworks_summary'][:2]:
                    print(f"      - {fw.get('framework')}: {fw.get('total_matches')} matches, {fw.get('files_count')} files")
                    if fw.get('categories'):
                        print(f"        Categories: {[c.get('category') for c in fw['categories'][:3]]}")
            else:
                print(f"   ❌ frameworks_summary MISSING")
            
            # Test hotspots
            if 'hotspots' in response:
                print(f"   ✅ hotspots present: {len(response['hotspots'])} hotspots")
                for hs in response['hotspots'][:2]:
                    print(f"      - {hs.get('directory')}: {hs.get('files_with_ai')} files, {hs.get('total_matches')} matches")
            else:
                print(f"   ❌ hotspots MISSING")
            
            # Test risk_flags
            if 'risk_flags' in response:
                print(f"   ✅ risk_flags present: {len(response['risk_flags'])} flags")
                for rf in response['risk_flags'][:2]:
                    print(f"      - {rf.get('label')} (severity: {rf.get('severity')})")
            else:
                print(f"   ❌ risk_flags MISSING")
            
            # Test recommended_actions
            if 'recommended_actions' in response:
                print(f"   ✅ recommended_actions present: {len(response['recommended_actions'])} actions")
                for ra in response['recommended_actions'][:2]:
                    print(f"      - {ra.get('title')}")
            else:
                print(f"   ❌ recommended_actions MISSING")
            
            # Test enhanced occurrence metadata
            if response.get('files'):
                print(f"\n   📄 Sample file with enhanced metadata:")
                sample_file = response['files'][0]
                print(f"      File: {sample_file.get('file_path')}")
                if sample_file.get('occurrences'):
                    occ = sample_file['occurrences'][0]
                    print(f"      - pattern_category: {occ.get('pattern_category', 'MISSING')}")
                    print(f"      - pattern_severity: {occ.get('pattern_severity', 'MISSING')}")
                    print(f"      - pattern_description: {occ.get('pattern_description', 'MISSING')[:50]}...")
                    print(f"      - snippet present: {'Yes' if occ.get('snippet') else 'No'}")
                    if occ.get('snippet'):
                        has_hit_marker = '[[[HIT]]]' in occ['snippet']
                        print(f"      - snippet has [[[HIT]]] marker: {'Yes' if has_hit_marker else 'No'}")
        
        return success, response

    def test_get_scan(self, scan_id):
        """Test retrieving a scan by ID"""
        if not scan_id:
            print("\n⚠️  Skipping get scan test - no scan_id available")
            return False
        
        success, response = self.run_test(
            "Get Scan by ID",
            "GET",
            f"scans/{scan_id}",
            200
        )
        
        if success:
            print(f"   Retrieved scan: {response.get('repo_url')}")
            print(f"   Status: {response.get('status')}")
            print(f"   Files: {response.get('files_count', 0)}")
            print(f"   Occurrences: {response.get('total_occurrences', 0)}")
        
        return success

    def test_get_scan_not_found(self):
        """Test retrieving non-existent scan"""
        success, response = self.run_test(
            "Get Non-existent Scan",
            "GET",
            "scans/non-existent-id-12345",
            404
        )
        return success

def main():
    print("=" * 70)
    print("AI DEPENDENCY SCANNER - BACKEND API TESTS")
    print("=" * 70)
    
    tester = AIDepScannerTester()
    
    # Test 1: Health check
    if not tester.test_health():
        print("\n❌ Backend is not responding. Stopping tests.")
        return 1
    
    # Test 2: Get patterns configuration
    tester.test_get_patterns()
    
    # Test 3: Invalid URL
    tester.test_create_scan_invalid_url()
    
    # Test 4: Valid repo scan - using a small repo with known LLM usage
    # Using openai-python repo as it's guaranteed to have openai imports
    test_repo = "https://github.com/openai/openai-python"
    success, scan_result = tester.test_create_scan_valid_repo(test_repo)
    
    # Test 5: Get scan by ID
    if success and tester.scan_id:
        tester.test_get_scan(tester.scan_id)
    
    # Test 6: Get non-existent scan
    tester.test_get_scan_not_found()
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {tester.tests_run}")
    print(f"Tests passed: {tester.tests_passed}")
    print(f"Tests failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success rate: {(tester.tests_passed / tester.tests_run * 100):.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("\n✅ All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {tester.tests_run - tester.tests_passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
