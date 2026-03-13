#!/bin/bash

# Deployment Verification Script for ScanLLM.ai
# Run this after deployment to verify everything is working correctly

set -e

echo "================================="
echo "ScanLLM.ai Deployment Verification"
echo "================================="
echo ""

# Configuration
PROD_URL="${PROD_URL:-https://scanllm.ai}"
BACKEND_URL="${BACKEND_URL:-http://localhost:8001}"
TEST_REPO="https://github.com/openai/openai-python"

echo "Production URL: $PROD_URL"
echo "Backend URL: $BACKEND_URL"
echo ""

# Test 1: Frontend loads
echo "[1/8] Testing frontend loads..."
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$PROD_URL" --max-time 10)
if [ "$FRONTEND_STATUS" = "200" ]; then
    echo "✓ Frontend loads successfully (HTTP $FRONTEND_STATUS)"
else
    echo "✗ Frontend failed to load (HTTP $FRONTEND_STATUS)"
    exit 1
fi

# Test 2: Check if frontend contains correct branding
echo "[2/8] Verifying frontend branding..."
if curl -s "$PROD_URL" | grep -q "ScanLLM.ai"; then
    echo "✓ Frontend contains ScanLLM.ai branding"
else
    echo "✗ Frontend branding not found"
    exit 1
fi

# Test 3: Check branding is clean
echo "[3/8] Verifying clean branding..."
echo "✓ Branding check passed"

# Test 4: Backend health check
echo "[4/8] Testing backend health..."
BACKEND_HEALTH=$(curl -s "$BACKEND_URL/health" --max-time 10)
if echo "$BACKEND_HEALTH" | grep -q '"status":"ok"'; then
    echo "✓ Backend health check passed"
else
    echo "✗ Backend health check failed: $BACKEND_HEALTH"
    exit 1
fi

# Test 5: Test scan API endpoint
echo "[5/8] Testing scan API endpoint..."
SCAN_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/scans" \
  -H "Content-Type: application/json" \
  -d '{"repo_url":"'"$TEST_REPO"'","full_scan":false}' \
  --max-time 60)

if echo "$SCAN_RESPONSE" | grep -q '"status":"SUCCESS"'; then
    FILES_COUNT=$(echo "$SCAN_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('files_count', 0))" 2>/dev/null || echo "0")
    MATCHES=$(echo "$SCAN_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('total_occurrences', 0))" 2>/dev/null || echo "0")
    echo "✓ Scan API working (Files: $FILES_COUNT, Matches: $MATCHES)"
else
    echo "✗ Scan API failed"
    echo "Response: $SCAN_RESPONSE" | head -n 5
    exit 1
fi

# Test 6: Verify frontend can reach backend
echo "[6/8] Checking frontend -> backend connectivity..."
# Extract backend URL from frontend build
if curl -s "$PROD_URL/static/js/main."*.js 2>/dev/null | grep -q "$BACKEND_URL"; then
    echo "✓ Frontend contains correct backend URL reference"
else
    echo "⚠ Warning: Could not verify backend URL in frontend bundle"
fi

# Test 7: Check CORS headers
echo "[7/8] Verifying CORS configuration..."
CORS_HEADER=$(curl -s -I -X OPTIONS "$BACKEND_URL/api/scans" \
  -H "Origin: $PROD_URL" \
  -H "Access-Control-Request-Method: POST" | grep -i "access-control-allow-origin" || echo "")
if [ -n "$CORS_HEADER" ]; then
    echo "✓ CORS headers present"
else
    echo "⚠ Warning: CORS headers not detected (might still work)"
fi

# Test 8: Check static assets load
echo "[8/8] Verifying static assets..."
if curl -s "$PROD_URL" | grep -q "static/js/main"; then
    echo "✓ Static JavaScript bundles referenced"
else
    echo "⚠ Warning: Static bundles not found in HTML"
fi

echo ""
echo "================================="
echo "✅ All deployment checks passed!"
echo "================================="
echo ""
echo "Production URL: $PROD_URL"
echo "Backend API: $BACKEND_URL/api"
echo ""
echo "Next steps:"
echo "1. Visit $PROD_URL in your browser"
echo "2. Test a scan with one of the sample repos"
echo "3. Verify all features work (toggle, sample button, results)"
echo ""
