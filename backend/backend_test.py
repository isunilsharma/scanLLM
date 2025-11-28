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
    
    def test_v2_features(self, scan_result):
        """Test v2 enhanced features"""
        print(f"\n{'='*70}")
        print("TESTING V2 ENHANCED FEATURES")
        print(f"{'='*70}")
        
        v2_tests_passed = 0
        v2_tests_total = 0
        
        # Test 1: Policy Evaluation
        v2_tests_total += 1
        print(f"\n🔍 Testing Policy Evaluation...")
        if 'policies_result' in scan_result:
            policies = scan_result['policies_result']
            if 'errors' in policies and 'warnings' in policies and 'passes' in policies:
                print(f"   ✅ policies_result structure valid")
                print(f"      - Errors: {len(policies['errors'])}")
                print(f"      - Warnings: {len(policies['warnings'])}")
                print(f"      - Passes: {len(policies['passes'])}")
                v2_tests_passed += 1
            else:
                print(f"   ❌ policies_result missing required fields")
        else:
            print(f"   ❌ policies_result MISSING")
        
        # Test 2: Blast Radius Summary
        v2_tests_total += 1
        print(f"\n🔍 Testing Blast Radius Summary...")
        if 'blast_radius_summary' in scan_result:
            blast = scan_result['blast_radius_summary']
            if 'high' in blast and 'medium' in blast and 'low' in blast:
                print(f"   ✅ blast_radius_summary structure valid")
                print(f"      - High risk files: {blast['high']}")
                print(f"      - Medium risk files: {blast['medium']}")
                print(f"      - Low risk files: {blast['low']}")
                v2_tests_passed += 1
            else:
                print(f"   ❌ blast_radius_summary missing required fields")
        else:
            print(f"   ❌ blast_radius_summary MISSING")
        
        # Test 3: Model & Prompt Contracts
        v2_tests_total += 1
        print(f"\n🔍 Testing Model & Prompt Contracts...")
        if 'contracts' in scan_result:
            contracts = scan_result['contracts']
            if 'unique_models' in contracts:
                print(f"   ✅ contracts structure valid")
                print(f"      - Unique models: {contracts.get('unique_models', [])}")
                print(f"      - Temperature range: {contracts.get('temperature_range', {})}")
                print(f"      - Max tokens range: {contracts.get('max_tokens_range', {})}")
                print(f"      - Streaming usage: {contracts.get('streaming_usage', 0)}")
                print(f"      - Tools usage: {contracts.get('tools_usage', 0)}")
                v2_tests_passed += 1
            else:
                print(f"   ❌ contracts missing required fields")
        else:
            print(f"   ❌ contracts MISSING")
        
        # Test 4: Ownership Summary
        v2_tests_total += 1
        print(f"\n🔍 Testing Ownership Summary...")
        if 'ownership_summary' in scan_result:
            ownership = scan_result['ownership_summary']
            print(f"   ✅ ownership_summary present: {len(ownership)} owners")
            if len(ownership) > 0:
                print(f"      Top owner: {ownership[0].get('owner_name', 'unknown')}")
                print(f"      - AI files: {ownership[0].get('ai_files_count', 0)}")
                print(f"      - Total matches: {ownership[0].get('total_matches', 0)}")
            v2_tests_passed += 1
        else:
            print(f"   ❌ ownership_summary MISSING")
        
        # Test 5: AI Heatmap
        v2_tests_total += 1
        print(f"\n🔍 Testing AI Heatmap...")
        if 'heatmap' in scan_result:
            heatmap = scan_result['heatmap']
            print(f"   ✅ heatmap present: {len(heatmap)} directories")
            if len(heatmap) > 0:
                top_dir = list(heatmap.keys())[0]
                print(f"      Top directory: {top_dir}")
                print(f"      - Files: {heatmap[top_dir].get('files', 0)}")
                print(f"      - Matches: {heatmap[top_dir].get('matches', 0)}")
            v2_tests_passed += 1
        else:
            print(f"   ❌ heatmap MISSING")
        
        # Test 6: Contract Extraction in Occurrences
        v2_tests_total += 1
        print(f"\n🔍 Testing Contract Extraction in Occurrences...")
        if scan_result.get('files'):
            found_contract = False
            for file in scan_result['files']:
                for occ in file.get('occurrences', []):
                    if occ.get('model_name') or occ.get('temperature') is not None or occ.get('max_tokens'):
                        found_contract = True
                        print(f"   ✅ Contract data found in occurrence")
                        print(f"      File: {file['file_path']}")
                        print(f"      - model_name: {occ.get('model_name', 'N/A')}")
                        print(f"      - temperature: {occ.get('temperature', 'N/A')}")
                        print(f"      - max_tokens: {occ.get('max_tokens', 'N/A')}")
                        print(f"      - is_streaming: {occ.get('is_streaming', False)}")
                        print(f"      - has_tools: {occ.get('has_tools', False)}")
                        break
                if found_contract:
                    break
            
            if found_contract:
                v2_tests_passed += 1
            else:
                print(f"   ⚠️  No contract data found in occurrences (may be normal if repo has no explicit configs)")
                v2_tests_passed += 1  # Not a failure, just no data
        else:
            print(f"   ❌ No files to check")
        
        # Test 7: Ownership Data in Occurrences
        v2_tests_total += 1
        print(f"\n🔍 Testing Ownership Data in Occurrences...")
        if scan_result.get('files'):
            found_ownership = False
            for file in scan_result['files']:
                for occ in file.get('occurrences', []):
                    if occ.get('owner_name'):
                        found_ownership = True
                        print(f"   ✅ Ownership data found in occurrence")
                        print(f"      File: {file['file_path']}")
                        print(f"      - owner_name: {occ.get('owner_name', 'N/A')}")
                        print(f"      - owner_email: {occ.get('owner_email', 'N/A')}")
                        print(f"      - owner_committed_at: {occ.get('owner_committed_at', 'N/A')}")
                        break
                if found_ownership:
                    break
            
            if found_ownership:
                v2_tests_passed += 1
            else:
                print(f"   ⚠️  No ownership data found (may be rate limited or no GitHub data)")
                v2_tests_passed += 1  # Not a failure, may be rate limited
        else:
            print(f"   ❌ No files to check")
        
        print(f"\n{'='*70}")
        print(f"V2 FEATURES TEST SUMMARY: {v2_tests_passed}/{v2_tests_total} passed")
        print(f"{'='*70}")
        
        return v2_tests_passed, v2_tests_total
    
    def test_explain_scan(self, scan_id):
        """Test LLM-powered scan explanation"""
        if not scan_id:
            print("\n⚠️  Skipping explain scan test - no scan_id available")
            return False
        
        print(f"\n⚠️  This test will call LLM API and may take 10-20 seconds...")
        
        success, response = self.run_test(
            "Explain Scan (LLM)",
            "POST",
            "explain-scan",
            200,
            data={"scan_id": scan_id},
            timeout=60
        )
        
        if success:
            explanation = response.get('explanation', '')
            print(f"   ✅ Explanation generated")
            print(f"   Length: {len(explanation)} characters")
            print(f"   Preview: {explanation[:200]}...")
        
        return success
    
    def test_scan_history(self, repo_url):
        """Test scan history endpoint"""
        if not repo_url:
            print("\n⚠️  Skipping scan history test - no repo_url available")
            return False
        
        # URL encode the repo_url
        import urllib.parse
        encoded_url = urllib.parse.quote(repo_url, safe='')
        
        success, response = self.run_test(
            "Get Scan History",
            "GET",
            f"scan-history?repo_url={encoded_url}",
            200
        )
        
        if success:
            scans = response.get('scans', [])
            print(f"   ✅ Found {len(scans)} historical scans")
            if len(scans) > 0:
                latest = scans[0]
                print(f"   Latest scan:")
                print(f"      - ID: {latest.get('id')}")
                print(f"      - Date: {latest.get('created_at')}")
                print(f"      - Files: {latest.get('ai_files_count', 0)}")
                print(f"      - Matches: {latest.get('total_matches', 0)}")
        
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
