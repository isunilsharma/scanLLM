#!/usr/bin/env python3
"""
Environment Configuration Verification Script
Verifies that environment variables are correctly set for deployment
"""

import os
import sys
from pathlib import Path

def check_env_file(file_path, required_vars):
    """Check if .env file exists and contains required variables"""
    print(f"\nChecking {file_path}...")
    
    if not Path(file_path).exists():
        print(f"  ✗ File does not exist: {file_path}")
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    all_present = True
    for var in required_vars:
        if var in content:
            # Extract value (simplified)
            lines = [line for line in content.split('\n') if line.startswith(var)]
            if lines:
                value = lines[0].split('=', 1)[1] if '=' in lines[0] else 'MISSING'
                # Mask sensitive values
                if 'KEY' in var or 'SECRET' in var:
                    display_value = value[:20] + '...' if len(value) > 20 else value
                else:
                    display_value = value
                print(f"  ✓ {var} = {display_value}")
        else:
            print(f"  ✗ Missing: {var}")
            all_present = False
    
    return all_present

def verify_backend_url_consistency():
    """Verify backend URLs are consistent across environment"""
    print("\n=== Backend URL Consistency Check ===")
    
    # Read frontend .env
    frontend_env = Path('/app/frontend/.env')
    if frontend_env.exists():
        with open(frontend_env) as f:
            for line in f:
                if 'REACT_APP_BACKEND_URL' in line:
                    url = line.split('=')[1].strip().strip('"').strip("'")
                    print(f"  Frontend expects: {url}")
                    
                    # Check if it's a valid production URL
                    if 'preview' in url:
                        print(f"  ⚠ WARNING: Frontend is using PREVIEW URL!")
                        print(f"  This will cause scans to fail in production.")
                        print(f"  Expected: https://ai-reposcan.emergent.host or https://scanllm.ai")
                        return False
                    elif 'localhost' in url:
                        print(f"  ⚠ WARNING: Frontend is using LOCALHOST!")
                        return False
                    else:
                        print(f"  ✓ Production URL detected")
                        return True
    return False

def check_no_hardcoded_urls():
    """Verify no hardcoded URLs in critical files"""
    print("\n=== Hardcoded URL Check ===")
    
    # Check Home.jsx
    home_file = Path('/app/frontend/src/pages/Home.jsx')
    if home_file.exists():
        with open(home_file) as f:
            content = f.read()
            if 'process.env.REACT_APP_BACKEND_URL' in content:
                print("  ✓ Home.jsx uses environment variable")
            else:
                print("  ✗ Home.jsx might have hardcoded URL")
                return False
    
    return True

def main():
    print("="*60)
    print("ScanLLM.ai Deployment Environment Verification")
    print("="*60)
    
    # Check backend .env
    backend_ok = check_env_file(
        '/app/backend/.env',
        ['EMERGENT_LLM_KEY', 'CORS_ORIGINS']
    )
    
    # Check frontend .env
    frontend_ok = check_env_file(
        '/app/frontend/.env',
        ['REACT_APP_BACKEND_URL']
    )
    
    # Verify URL consistency
    url_ok = verify_backend_url_consistency()
    
    # Check for hardcoded URLs
    no_hardcoded = check_no_hardcoded_urls()
    
    print("\n" + "="*60)
    if backend_ok and frontend_ok and url_ok and no_hardcoded:
        print("✅ ALL CHECKS PASSED - Ready for deployment!")
        print("="*60)
        sys.exit(0)
    else:
        print("❌ DEPLOYMENT VERIFICATION FAILED")
        print("="*60)
        print("\nIssues found:")
        if not backend_ok:
            print("  - Backend .env missing required variables")
        if not frontend_ok:
            print("  - Frontend .env missing required variables")
        if not url_ok:
            print("  - Backend URL not configured for production")
        if not no_hardcoded:
            print("  - Hardcoded URLs detected in source code")
        print("\nPlease fix these issues before deploying.\n")
        sys.exit(1)

if __name__ == '__main__':
    main()
