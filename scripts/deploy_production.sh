#!/bin/bash
#
# ScanLLM.ai Production Deployment Script
# ScanLLM.ai Production Deployment
#

set -e

echo "========================================"
echo "ScanLLM.ai Production Deployment"
echo "========================================"
echo ""
echo "Target: http://localhost:8001"
echo "Custom Domain: https://scanllm.ai"
echo ""

# Environment check
echo "[Step 1/6] Environment Validation"
echo "----------------------------------"

if [ -f "/app/scripts/verify_env_config.py" ]; then
    python3 /app/scripts/verify_env_config.py || {
        echo "❌ Environment validation failed"
        echo "Please fix environment configuration before deploying"
        exit 1
    }
else
    echo "⚠ Environment validation script not found, skipping..."
fi

# Backend dependencies
echo ""
echo "[Step 2/6] Installing Backend Dependencies"
echo "-------------------------------------------"
cd /app/backend
pip install --no-cache-dir -r requirements.txt
echo "✓ Backend dependencies installed"

# Database initialization
echo ""
echo "[Step 3/6] Database Initialization"
echo "-----------------------------------"
python3 -c "from core.database import init_db; init_db(); print('✓ SQLite database initialized')"

# Frontend dependencies
echo ""
echo "[Step 4/6] Installing Frontend Dependencies"
echo "--------------------------------------------"
cd /app/frontend
yarn install --frozen-lockfile
echo "✓ Frontend dependencies installed"

# Frontend build
echo ""
echo "[Step 5/6] Building Frontend for Production"
echo "--------------------------------------------"
echo "Building with REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL"
yarn build
echo "✓ Frontend production build complete"

# Verification
echo ""
echo "[Step 6/6] Post-Build Verification"
echo "-----------------------------------"

# Check build output
if [ -d "/app/frontend/build" ]; then
    echo "✓ Build directory exists"
    BUILD_SIZE=$(du -sh /app/frontend/build | cut -f1)
    echo "  Build size: $BUILD_SIZE"
else
    echo "❌ Build directory not found"
    exit 1
fi

# Check for main bundle
if ls /app/frontend/build/static/js/main.*.js 1> /dev/null 2>&1; then
    echo "✓ Main JavaScript bundle created"
else
    echo "❌ Main JavaScript bundle not found"
    exit 1
fi

echo ""
echo "========================================"
echo "✅ Production Build Complete!"
echo "========================================"
echo ""
echo "Deployment Summary:"
echo "  - Backend: FastAPI + SQLite"
echo "  - Frontend: React 19 (optimized production build)"
echo "  - Features: v2 Enterprise Intelligence Platform"
echo "  - Performance: Parallel scanning + Smart filtering"
echo ""
echo "Next steps:"
echo "  1. Deploy to Kubernetes cluster"
echo "  2. Verify at: http://localhost:8001"
echo "  3. Test with sample repos"
echo "  4. Monitor for 15 minutes"
echo ""
echo "Verification command:"
echo "  bash /app/scripts/deployment_verification.sh"
echo ""
