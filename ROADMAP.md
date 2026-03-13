# ScanLLM Feature Roadmap — Build Order

## Timeline: 8 weeks to customer-ready product (solo dev + Claude Code)

---

## TIER 1: Core Engine (Weeks 1-2)
**Goal: Make the scanner actually good. Nothing else matters if scan results are wrong.**

### T1.1 — AST-based Python AI Scanner
**Priority: P0 — build this first**
- Create `scanner/python_scanner.py` using `ast.NodeVisitor`
- Walk every `.py` file's AST
- Match `Import`, `ImportFrom` nodes against `ai_signatures.yaml`
- Match `Call` nodes for API call patterns (e.g., `client.chat.completions.create()`)
- Extract `model=` keyword arguments from calls
- Track variable assignments that reference model names
- Return list of `Finding` objects with: file path, line number, component type, provider, model name, confidence score
- **Test with**: LangChain repos, CrewAI repos, typical FastAPI+OpenAI apps
- **Library**: Python stdlib `ast` module (zero dependencies)
- **Time estimate**: 3-5 days

### T1.2 — Dependency File Parser
**Priority: P0**
- Create `scanner/dependency_scanner.py`
- Parse: `requirements.txt`, `pyproject.toml` (use `tomllib`), `Pipfile`, `poetry.lock`, `package.json`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`
- Cross-reference package names + versions against AI package list in `ai_signatures.yaml`
- Flag: outdated versions, known CVE packages (check via OSV.dev API)
- **Library**: `tomllib` (stdlib 3.11+), `json` (stdlib), string parsing
- **Time estimate**: 2-3 days

### T1.3 — Secret & Environment Variable Detection
**Priority: P0**
- Create `scanner/secret_scanner.py`
- Scan `.env`, `.env.*` files and source code for AI API key patterns
- Use `detect-secrets` library programmatically for general detection
- Add custom regex layer for: OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY, PINECONE_API_KEY, HF_TOKEN, LANGCHAIN_API_KEY, and 30+ other AI-specific env vars
- Distinguish: key is present (governance) vs. key value is hardcoded (security risk)
- **Library**: `detect-secrets` (pip install)
- **Time estimate**: 1-2 days

### T1.4 — Config File Scanner
**Priority: P1**
- Create `scanner/config_scanner.py`
- Scan YAML, JSON, TOML files for: model name strings, endpoint URLs, Docker Compose AI services, MCP server configs, GitHub Actions AI steps
- Recursive key-value walker with pattern dictionary
- **Library**: PyYAML (already in stack), `json` (stdlib), `tomllib` (stdlib)
- **Time estimate**: 1-2 days

### T1.5 — JS/TS Import Detection (Regex)
**Priority: P1**
- Create `scanner/js_scanner.py`
- Regex patterns for `import ... from 'openai'`, `require('@anthropic-ai/sdk')`, `import { ChatOpenAI } from '@langchain/openai'`, Vercel AI SDK, MCP SDK imports
- Cover `.js`, `.ts`, `.jsx`, `.tsx` files
- **Time estimate**: 2-3 days

### T1.6 — Notebook Scanner
**Priority: P2**
- Create `scanner/notebook_scanner.py`
- Parse `.ipynb` JSON, extract code cells, run python_scanner on each
- Track cell index for line number equivalent
- **Time estimate**: 1 day

### T1.7 — Scanner Engine Orchestrator
**Priority: P0**
- Create `scanner/engine.py`
- Orchestrates all scanners: clone repo → walk files → dispatch to correct scanner → collect all findings → deduplicate → return unified results
- Async processing with background tasks (FastAPI BackgroundTasks or Celery later)
- **Time estimate**: 2 days

---

## TIER 2: Visualization & Intelligence (Weeks 3-4)
**Goal: Build the dependency graph. This is your hero feature and demo.**

### T2.1 — Dependency Graph Builder
**Priority: P0 — this is the product**
- Create `graph/builder.py` using `networkx.DiGraph`
- Take scanner findings → create nodes (one per unique AI component)
- Node types: `llm_provider`, `embedding_service`, `vector_db`, `orchestration_framework`, `agent_tool`, `prompt_file`, `mcp_server`, `inference_server`
- Build edges from:
  - Same-file co-location (two AI components in same file → likely related)
  - Import chains (file A imports module that file B defines)
  - Data flow heuristics (embedding call in same file/module as vector DB call → "feeds-into")
  - Config references (config mentions same model as code → "configures")
  - Agent-tool relationships (agent config lists tools → "has-access-to")
- **Library**: `networkx`
- **Time estimate**: 4-5 days

### T2.2 — React Flow Interactive Graph
**Priority: P0**
- Create `frontend/src/components/DependencyGraph.tsx`
- Use `@xyflow/react` with `dagre` for automatic layout
- Custom node components per type (different colors/icons for LLM, VectorDB, Agent, etc.)
- Use shadcn Card/Badge inside nodes
- Click node → side panel (shadcn Sheet) shows: all files using this component, line numbers, risk flags, model details
- Click edge → shows relationship type
- Zoom, pan, minimap, export as PNG
- **Library**: `@xyflow/react`, `dagre`, `elkjs`
- **Time estimate**: 5-6 days

### T2.3 — Scan Results Dashboard
**Priority: P0**
- Create `frontend/src/pages/Dashboard.tsx`
- Cards: total AI dependencies, risk score gauge, top providers (pie chart), scan history
- Table: all findings sortable/filterable by type, severity, file
- Per-repo drill-down
- **Library**: Recharts, shadcn/ui Card/Badge/Table, `@tanstack/react-table`
- **Time estimate**: 3-4 days

### T2.4 — GitHub OAuth Authentication
**Priority: P0**
- Implement GitHub OAuth login flow
- Use `fastapi-users` + `httpx-oauth` for: registration, JWT sessions, GitHub OAuth provider
- Store GitHub access token for private repo scanning
- SQLAlchemy User model with github_id, access_token (encrypted)
- **Library**: `fastapi-users[sqlalchemy]`, `httpx-oauth`
- **Time estimate**: 3-4 days

### T2.5 — API Formalization
**Priority: P1**
- Versioned API: `/api/v1/`
- API key authentication (separate from OAuth, for CI/CD)
- Rate limiting with `slowapi`
- Auto-generated OpenAPI docs (FastAPI built-in)
- Endpoints: POST /scan, GET /scans/{id}, GET /scans/{id}/graph, GET /scans/{id}/findings
- **Time estimate**: 2 days

---

## TIER 3: Security & Compliance (Weeks 5-6)
**Goal: Transform from "interesting tool" to "security tool that justifies budget"**

### T3.1 — Risk Scoring Engine
**Priority: P0**
- Create `scoring/risk_engine.py`
- Assign 0-100 score per repo based on weighted factors:
  - Hardcoded secrets (weight: 25)
  - OWASP Critical findings (weight: 20)
  - OWASP High findings (weight: 10)
  - Outdated AI packages with CVEs (weight: 5) — check via OSV.dev API
  - Provider concentration >80% (weight: 10)
  - Excessive agent permissions (weight: 15)
  - Missing safety configs like max_tokens (weight: 3)
- Configurable weights in `scoring/rules.yaml`
- Per-finding severity: Critical, High, Medium, Low, Info
- **Library**: `httpx` for OSV.dev API calls
- **Time estimate**: 3 days

### T3.2 — OWASP LLM Top 10 Mapping
**Priority: P0**
- Create `scoring/owasp_mapper.py`
- Map each finding to OWASP LLM Top 10 2025 categories
- Start with 5 highest-value static detections: LLM03, LLM05, LLM06, LLM07, LLM10
- Generate coverage report: which OWASP risks are present, which are mitigated
- Frontend: OWASP coverage card showing green/yellow/red per category
- **Time estimate**: 3-4 days

### T3.3 — AI-BOM Generation (CycloneDX ML-BOM)
**Priority: P1**
- Create `reports/aibom_generator.py`
- Generate CycloneDX 1.6+ ML-BOM in JSON and XML
- Include: component type, version, license, provider, model references, dependency relationships
- Use `cyclonedx-python-lib` (official OWASP library, v11.6+)
- Downloadable from dashboard
- **Library**: `cyclonedx-python-lib`
- **Time estimate**: 3-4 days

### T3.4 — PDF Compliance Reports
**Priority: P1**
- Create `reports/pdf_generator.py`
- Jinja2 HTML template → PDF via `xhtml2pdf` (pure Python, no system deps)
- Contents: executive summary, AI inventory table, risk score breakdown, OWASP mapping, dependency graph (static image via matplotlib/networkx), remediation recommendations
- Branded with org name and timestamp
- **Library**: `Jinja2`, `xhtml2pdf`
- **Time estimate**: 2-3 days

### T3.5 — LLM-Powered Scan Analysis
**Priority: P2**
- Create `services/analysis_service.py`
- Send scan results to Claude API with structured prompt
- Generate human-readable narrative: what was found, why it matters, prioritized remediation
- Display as "AI Analysis" section in dashboard
- Cost: ~$0.01-0.05 per scan
- **Library**: `anthropic` Python SDK
- **Time estimate**: 1-2 days

---

## TIER 4: Distribution & Growth (Weeks 7-8)
**Goal: Make it easy for people to adopt and share**

### T4.1 — GitHub Actions Integration
**Priority: P0**
- Create `.github/actions/scanllm-action/`
- GitHub Action YAML + Dockerfile that calls ScanLLM API
- Posts findings as PR comments or Check annotations
- Optional: fail build on new high-risk findings
- Publish to GitHub Marketplace
- **Time estimate**: 2-3 days

### T4.2 — CLI Tool
**Priority: P1**
- Create `cli/scanllm_cli.py`
- Thin wrapper around scanner engine
- Commands: `scanllm scan <repo-url>`, `scanllm scan ./local-path`
- Output formats: `--output table` (default), `--output json`, `--output cyclonedx`
- Installable via `pip install scanllm`
- **Time estimate**: 2 days

### T4.3 — Organization & Team Management
**Priority: P1**
- SQLAlchemy models: Organization, Team, Membership (many-to-many)
- Sync with GitHub organizations
- Roles: Owner, Admin, Member, Viewer
- Org-scoped dashboard showing aggregate data across repos
- **Time estimate**: 3-4 days

### T4.4 — Public Scan Page (Shareable)
**Priority: P2**
- Unique URL per scan result: `scanllm.ai/scan/{scan_id}`
- Read-only view of dependency graph + findings
- "Scan your own repo" CTA
- This is your viral distribution mechanism
- **Time estimate**: 1-2 days

### T4.5 — Onboarding Flow
**Priority: P1**
- First-time user experience: GitHub OAuth → select repo → scan → see results
- Should take <2 minutes from signup to first "wow" moment
- Progress indicators during scan
- Empty states with helpful guidance
- **Time estimate**: 2 days

---

## POST-LAUNCH (Months 3-6) — Do NOT build these now

- Full GitHub App with automated PR scanning (webhooks, Check Runs)
- Tree-sitter JS/TS deep analysis (upgrade from regex)
- Drift detection between consecutive scans
- Prompt injection static detection (AST taint analysis)
- License risk detection for AI models/packages
- Slack/email notifications
- NIST AI RMF / EU AI Act compliance mapping
- SSO/SAML (enterprise gate feature)
- Custom scanning rules/policies (enterprise)
- Multi-SCM support (GitLab, Bitbucket, Azure DevOps)
- Self-hosted Docker deployment
- Audit logging
- AI provider concentration & blast radius analysis

---

## Definition of Done — Customer Ready
The product is "customer ready" when a user can:
1. Sign in with GitHub OAuth
2. Select a private repo
3. Trigger a scan that completes in <60 seconds for a typical repo
4. See an interactive dependency graph showing all AI components
5. View risk score and OWASP LLM Top 10 mapping
6. Download a PDF report and/or AI-BOM
7. Add a GitHub Action to scan on every PR
8. Invite team members to their organization

If all 8 work reliably, you can charge money.

---
---

# Build Plan — Detailed Implementation Tasks

**Constraints:**
- Deployed on **Render** (Docker) - all changes must work with Render's environment
- This is an **enterprise, customer-facing** application - UI must be polished
- GitHub OAuth login + private repo scanning was **broken** (fixed in Phase 0)

---

## Phase 0: Bug Fixes & Code Cleanup ✅ COMPLETE

### 0.1 ✅ Fix scanner_v2.py duplicate methods (CRITICAL)
- **File:** `backend/services/scanner_v2.py`
- Removed duplicate definitions of `_scan_directory_parallel`, `_collect_files_smart`, `_should_exclude`, `_should_skip`, `_is_priority_file`, `_scan_single_file`, `_extract_snippet`, `_build_summary_json`
- Removed dead code block. Reduced from 499 → 349 lines.

### 0.2 ✅ Fix GitHub OAuth + Private Repo Scanning (CRITICAL)
- **A)** Fixed missing Authorization header in `PrivateRepos.jsx` — added `Bearer ${token}` header
- **B)** Added `GITHUB_REDIRECT_URI` to `docker-compose.yml`
- **C)** Identified two conflicting OAuth callback flows (cleanup deferred to Phase 1)
- **D)** Added all required OAuth env vars to `docker-compose.yml`
- **E)** Made CORS origins configurable via env var in `server.py`

### 0.3 ✅ Fix bare except clauses
- `github_scanner.py` — catch `Exception` with logging
- `session_manager.py` — catch `jwt.JWTError`
- `github_api.py` — catch `requests.RequestException`

### 0.4 ✅ DB session threading — verified safe
- Workers return plain dicts, all DB writes happen in main thread. No fix needed.

### 0.5 ✅ Fix auth_github.py request parameter
- Changed `request: dict` to `request: ExchangeRequest(BaseModel)` with `code: str` and `state: str`

### 0.6 ✅ Fix insecure default session secret
- Added warning when `SESSION_SECRET` not set, dev-only fallback

### 0.7 ✅ Fix github_scanner.py newline handling
- Fixed `content.split('\\n')` → `content.split('\n')` and `'\\n'.join()` → `'\n'.join()`

### 0.8 ✅ Frontend: Add Error Boundary
- Created `ErrorBoundary.jsx`, wrapped app in `App.js`

### 0.9 ✅ Frontend: Create centralized API config
- Created `frontend/src/lib/api.js` with axios instance, auth interceptors, 401 handling

### 0.10 ✅ Frontend: Fix unsafe JSON.parse
- Wrapped `JSON.parse` in try-catch in `ScanHistory.jsx`

### 0.11 ✅ Frontend: Fix polling cleanup
- Added proper `useEffect` cleanup with `cancelled` flag in `ScanPage.jsx`

### 0.12 ✅ Clean up requirements.txt
- Removed unused: `motor`, `pymongo`, `s5cmd`, `pytokens`, `tiktoken`

### 0.13 ✅ Render Deployment Hardening
- Created `render.yaml` Blueprint for Infrastructure-as-Code
- Dockerfile verified with health check support

---

## Phase 1: Restructure to CLAUDE.md Architecture

### 1.1 Create new directory structure
```
backend/
├── app/
│   ├── main.py              (move from server.py)
│   ├── config.py             (move from core/config.py, use pydantic-settings)
│   ├── models/               (move from models/)
│   ├── api/
│   │   └── v1/
│   │       ├── scans.py      (move from server.py scan endpoints)
│   │       ├── repos.py      (move from api/github_endpoints.py)
│   │       ├── reports.py    (new)
│   │       └── auth.py       (move from api/auth_github.py)
│   ├── scanner/              (NEW - core engine)
│   │   ├── engine.py         (orchestrator, refactor from scanner_v2.py)
│   │   ├── python_scanner.py (NEW - AST-based)
│   │   ├── js_scanner.py     (NEW - regex-based JS/TS)
│   │   ├── config_scanner.py (NEW - YAML/JSON/TOML/env)
│   │   ├── dependency_scanner.py (NEW)
│   │   ├── notebook_scanner.py (NEW)
│   │   ├── secret_scanner.py (NEW)
│   │   └── signatures/
│   │       └── ai_signatures.yaml (merged file)
│   ├── graph/                (NEW)
│   │   ├── builder.py
│   │   ├── analyzer.py
│   │   └── serializer.py
│   ├── scoring/              (NEW)
│   │   ├── risk_engine.py
│   │   ├── owasp_mapper.py
│   │   └── rules.yaml
│   ├── reports/              (NEW)
│   │   ├── pdf_generator.py
│   │   ├── aibom_generator.py
│   │   └── templates/
│   └── services/
│       ├── github_service.py (refactor from services/*)
│       └── analysis_service.py (move from llm_explainer.py)
```

### 1.2 Merge signature files
- Merge `config/patterns.yml` (28 patterns with regex) + root `ai_signatures.yaml` (200+ patterns with metadata)
- Output: single `backend/app/scanner/signatures/ai_signatures.yaml`

### 1.3 Update imports across codebase

### 1.4 Verify nothing breaks

---

## Phase 1.5: UI Polish (Enterprise-Grade)

### 1.5.1 Loading & Empty States
### 1.5.2 Error UX
### 1.5.3 Dashboard Polish
### 1.5.4 Scan Results Page Improvements
### 1.5.5 Navigation & Onboarding

---

## Phase 2: Core Engine (T1 from Roadmap)

### 2.1 AST-based Python Scanner
### 2.2 JS/TS Scanner
### 2.3 Config File Scanner
### 2.4 Dependency File Parser
### 2.5 Notebook Scanner
### 2.6 Secret Scanner
### 2.7 Scanner Engine Orchestrator

---

## Phase 3: Dependency Graph (T2 from Roadmap)

### 3.1 Graph Builder
### 3.2 Graph Analyzer
### 3.3 Graph Serializer
### 3.4 React Flow Frontend Component
### 3.5 Graph API Endpoint

---

## Phase 4: Security & Compliance (T3 from Roadmap)

### 4.1 Risk Scoring Engine
### 4.2 OWASP LLM Top 10 Mapper
### 4.3 AI-BOM Generator (CycloneDX)
### 4.4 PDF Report Generator

---

## Phase 5: Distribution (T4 from Roadmap)

### 5.1 GitHub Actions Integration
### 5.2 CLI Tool (`scanllm scan <repo>`)
### 5.3 Organization & Team Management
### 5.4 Public Scan Page (shareable URL)
### 5.5 Onboarding Flow

---

## Build Order Summary

```
Phase 0: Bug fixes + OAuth fix + Render hardening  ✅ COMPLETE
  └─> Phase 1: Restructure to CLAUDE.md architecture
        └─> Phase 1.5: UI polish (enterprise-grade)
              └─> Phase 2: Core engine scanners (AST, config, deps, secrets)
                    └─> Phase 3: Dependency graph (hero feature)
                          └─> Phase 4: Security & compliance (risk, OWASP, reports)
                                └─> Phase 5: Distribution (GitHub Actions, CLI, orgs)
```

## Verification Plan

After each phase:
1. Run `pytest tests/` - all tests pass
2. Start backend: `cd backend && uvicorn app.main:app --reload --port 8000`
3. Start frontend: `cd frontend && npm run dev`
4. Test scan endpoint: `POST /api/scans` with a sample repo
5. Verify scan results display correctly in UI
6. Docker build: `docker-compose build && docker-compose up`

## Deployment (Render)

All phases must be deployable on Render:
- Backend: Docker web service, health check at `/health`
- Frontend: Static site or Docker web service
- Environment variables managed via Render Dashboard (never committed)
- SQLite on Render persistent disk (plan PostgreSQL migration for Phase 5)
- `render.yaml` Blueprint for reproducible deploys
