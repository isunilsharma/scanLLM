# GitHub OAuth + Private Repo Scanning - Implementation Guide

## ✅ Completed (3/18 tasks)

1. ✅ Updated scan_jobs model with GitHub OAuth fields
2. ✅ Created session_manager.py (JWT sessions)
3. ✅ Created token_encryption.py (Fernet encryption)
4. ✅ Created github_user.py model
5. ✅ Created github_token.py model
6. ✅ GitHub App credentials stored in .env

## 📋 Remaining Tasks (Continue in Next Session)

### Backend (9 tasks remaining):

**Task 6:** Create `/app/backend/services/github_api.py`
- Class: GitHubAPI(access_token)
- Methods: get_user(), get_repos(), get_file_tree(), get_file_content()
- Uses GitHub REST API v3

**Task 7:** Create `/app/backend/services/github_scanner.py`
- Scan repos via GitHub API (no git clone)
- Reuse parallel processing logic
- Smart filtering for private repos

**Task 8:** Create `/app/backend/api/auth_github.py`
- GET /auth/github/login (redirect to GitHub)
- GET /auth/github/callback (exchange code for token)
- Store user + token in database

**Task 9:** Create `/app/backend/api/github_endpoints.py`
- GET /api/github/user (current user info)
- GET /api/github/repos (list repos with filter)
- POST /api/github/revoke (disconnect GitHub)

**Task 10:** Create `/app/backend/api/scan_github.py`
- POST /api/scan/github (scan private repo)
- GET /api/scan/{id}/results (get results)

**Task 11:** Update `/app/backend/server.py`
- Include auth router
- Include GitHub API router
- Add auth dependency for protected routes

**Task 12:** Create auth middleware
- Dependency function to verify JWT from cookies
- Protect private endpoints

**Task 13:** Database migration
- Run init_db() to create new tables
- Test user/token storage

**Task 14:** Test OAuth flow end-to-end

### Frontend (8 tasks remaining):

**Task 15:** Create `/app/frontend/src/context/AuthContext.jsx`
- Manage auth state (user, isAuthenticated)
- Store JWT in cookies
- Provide login/logout functions

**Task 16:** Create `/app/frontend/src/components/LoginButton.jsx`
- "Sign in with GitHub" button
- Redirects to /auth/github/login

**Task 17:** Create `/app/frontend/src/pages/PrivateRepos.jsx`
- Fetch and display user's repos
- Filter: All/Private/Public
- Scan button for each repo
- Show user profile with disconnect

**Task 18:** Create `/app/frontend/src/components/RepoListItem.jsx`
- Display repo info (name, private badge, last updated)
- Scan button with options (smart/full)

**Task 19:** Create `/app/frontend/src/components/UserProfile.jsx`
- Avatar + username
- "Disconnect GitHub" button

**Task 20:** Update `/app/frontend/src/pages/Home.jsx`
- Add "Try Demo" vs "Sign in with GitHub" dual CTAs
- Add "How It Works" section
- Image/video placeholders

**Task 21:** Update `/app/frontend/src/App.js`
- Add /private/repos route
- Add /auth/github/callback route (loading page)
- Wrap App with AuthContext

**Task 22:** Create `/app/frontend/src/components/ProtectedRoute.jsx`
- Redirect to home if not authenticated
- Use for /private/repos

## 🔐 GitHub App Configuration

**Your Credentials:**
- App ID: 2555016
- Client ID: Iv23li2mezQqblk71a9U
- Client Secret: 42c0efc02fa36b7cf272a494306050897c025fee

**Callback URLs Configured:**
- Production: https://scanllm.ai/auth/github/callback
- Preview: https://aireposcan.preview.emergentagent.com/auth/github/callback

**Permissions Required:**
- Repository: Contents (Read-only)
- Repository: Metadata (Read-only)

## 📝 Implementation Notes

**OAuth Flow:**
1. User clicks "Sign in with GitHub"
2. Redirect to GitHub OAuth with client_id + state
3. GitHub redirects back to /auth/github/callback?code=...
4. Exchange code for access_token
5. Fetch user info from GitHub
6. Store user + encrypted token in database
7. Create JWT session
8. Redirect to /private/repos

**Private Repo Scanning:**
1. User selects repo from list
2. POST /api/scan/github {owner, repo, branch, full_scan}
3. Backend uses GitHub API (not git clone):
   - Fetch file tree recursively
   - Filter to scannable files
   - Fetch file contents via API (parallel)
   - Run pattern matching
   - Store findings
4. Return scan results (same format as public scans)

**Database Schema:**
- github_users: User profile from GitHub
- github_tokens: Encrypted access tokens
- scan_jobs: Updated with github_user_id, repo_owner, repo_name, repo_private, source

## 🚀 Quick Start for Next Session

```
Continue implementing GitHub OAuth for ScanLLM.ai. 

Completed: Models (github_user, github_token), encryption (token_encryption.py), session (session_manager.py), scan_jobs updated.

Remaining: Implement OAuth endpoints, GitHub API service, private scanner, and complete frontend (AuthContext, LoginButton, PrivateRepos page, dual CTAs on homepage).

GitHub App credentials:
- Client ID: Iv23li2mezQqblk71a9U
- Client Secret: 42c0efc02fa36b7cf272a494306050897c025fee  
- App ID: 2555016
- Callback: https://scanllm.ai/auth/github/callback

All credentials stored in /app/backend/.env. Database models ready. Start with OAuth flow implementation.
```

---

**Status:** 5/22 tasks complete. Ready to continue implementation in next session with fresh token budget.
