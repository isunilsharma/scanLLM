# ScanLLM.ai Pre-Deployment Checklist

## Environment Configuration

### Frontend Environment Variables
- [ ] `REACT_APP_BACKEND_URL` is set to production URL
  - ✅ Correct: `https://ai-reposcan.emergent.host` or `https://scanllm.ai`
  - ❌ Incorrect: `https://ai-reposcan.preview.emergentagent.com` or `http://localhost:8001`

### Backend Environment Variables
- [ ] `EMERGENT_LLM_KEY` is set (for AI explanations)
- [ ] `CORS_ORIGINS` is set to `*` or includes production domain

## Code Verification

### Frontend
- [ ] No hardcoded backend URLs in components
- [ ] All API calls use `process.env.REACT_APP_BACKEND_URL`
- [ ] "Made with Emergent" badge removed from `public/index.html`
- [ ] Page title is "ScanLLM.ai - AI Dependency Intelligence"

### Backend
- [ ] Git fallback mechanism in place (no git binary required)
- [ ] All API endpoints use `/api` prefix
- [ ] Database initialization works (SQLite)
- [ ] Scanner uses parallel processing and smart filtering

## Build Verification

### Frontend Build
```bash
cd /app/frontend
yarn build
```
- [ ] Build completes without errors
- [ ] Build output contains `main.*.js` bundles
- [ ] No console errors about missing environment variables

### Backend Dependencies
```bash
cd /app/backend
pip install -r requirements.txt
```
- [ ] All dependencies install successfully
- [ ] emergentintegrations installed (for LLM features)
- [ ] No dependency conflicts

## Functionality Tests

### Backend API Tests
- [ ] `GET /health` returns `{"status":"ok"}`
- [ ] `POST /api/scans` completes in 2-15 seconds
- [ ] `GET /api/scans/{id}` retrieves scan results
- [ ] `POST /api/explain-scan` generates AI summary
- [ ] `GET /api/scan-history` returns historical scans

### Frontend Tests
- [ ] Homepage loads with ScanLLM.ai branding
- [ ] Sample button shows example repos
- [ ] Full scan toggle works (blue when ON)
- [ ] Scan completes and shows results
- [ ] Mobile hamburger menu works
- [ ] All pages accessible (Home, Blog, About, How It Works)

## Performance Verification

- [ ] Small repos (< 100 files): 1-3 seconds
- [ ] Medium repos (100-500 files): 5-10 seconds
- [ ] Large repos (500-1000 files): 10-15 seconds
- [ ] Full scan option available and functional

## Security & Compliance

- [ ] No API keys in source code
- [ ] All secrets in environment variables
- [ ] CORS properly configured
- [ ] LinkedIn link points to correct company page

## Cache & Resources

- [ ] Browser cache headers set correctly
- [ ] Static assets (JS/CSS) load from CDN
- [ ] No 404 errors for static resources
- [ ] Favicon and meta tags present

## Post-Deployment Validation

### Immediate (0-5 minutes)
1. Visit production URL
2. Check page loads completely
3. Verify no console errors in browser DevTools
4. Test one quick scan

### Extended (5-30 minutes)
1. Test all 4 sample repos
2. Test full scan toggle
3. Test AI explanation feature
4. Verify mobile responsiveness
5. Check all blog posts load

## Rollback Plan

If deployment fails:
1. Note the specific error
2. Revert to previous deployment in Emergent dashboard
3. Fix issues in development
4. Re-run this checklist
5. Deploy again

## Success Criteria

✅ All items checked
✅ No errors in verification scripts
✅ Production URL loads in < 3 seconds
✅ Scans complete successfully
✅ All v2 features working (policies, blast radius, contracts, etc.)

---

**Deployment Date:** _____________
**Deployed By:** _____________
**Version:** v2.0 Enterprise Intelligence Platform
**Production URL:** https://scanllm.ai
**Status:** _____________
