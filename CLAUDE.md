# ScanLLM — AI Dependency Intelligence Platform

## Project Overview
ScanLLM is a B2B SaaS platform that scans codebases to discover, map, and govern all AI/LLM dependencies. Think "Snyk for AI systems." It answers the question no tool answers today: "What AI is in our code, where, and what depends on what?"

## Tech Stack
- **Backend:** FastAPI (Python 3.11+), SQLAlchemy + SQLite (migrate to PostgreSQL later), GitPython, PyYAML
- **Frontend:** React 19, Tailwind CSS + shadcn/ui, Recharts for charts, React Flow (@xyflow/react) for dependency graphs, Axios for API
- **Hosting:** Render (Docker)
- **Auth:** GitHub OAuth via fastapi-users + httpx-oauth, JWT sessions
- **Key Libraries (backend):** `detect-secrets`, `cyclonedx-python-lib`, `networkx`, `slowapi`
- **Key Libraries (frontend):** `@xyflow/react`, `dagre`, `@tanstack/react-table`

## Architecture

```
scanllm/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app entry
│   │   ├── config.py               # Settings via pydantic-settings
│   │   ├── models/                 # SQLAlchemy models
│   │   │   ├── user.py
│   │   │   ├── organization.py
│   │   │   ├── scan.py
│   │   │   └── finding.py
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── scans.py        # POST /scan, GET /scans/{id}
│   │   │   │   ├── repos.py        # Repo management
│   │   │   │   ├── reports.py      # PDF/AI-BOM export
│   │   │   │   └── auth.py         # GitHub OAuth
│   │   │   └── deps.py             # Shared dependencies
│   │   ├── scanner/                # CORE ENGINE
│   │   │   ├── engine.py           # Orchestrates all scanners
│   │   │   ├── python_scanner.py   # AST-based Python analysis
│   │   │   ├── js_scanner.py       # Regex-based JS/TS scanning
│   │   │   ├── config_scanner.py   # YAML/JSON/TOML/env scanning
│   │   │   ├── dependency_scanner.py  # requirements.txt, package.json
│   │   │   ├── notebook_scanner.py # .ipynb cell extraction
│   │   │   ├── secret_scanner.py   # AI-specific secret detection
│   │   │   └── signatures/
│   │   │       └── ai_signatures.yaml  # 200+ AI detection patterns
│   │   ├── graph/
│   │   │   ├── builder.py          # networkx graph construction
│   │   │   ├── analyzer.py         # Concentration risk, blast radius
│   │   │   └── serializer.py       # Graph → React Flow JSON
│   │   ├── scoring/
│   │   │   ├── risk_engine.py      # 0-100 risk scoring
│   │   │   ├── owasp_mapper.py     # Map findings → OWASP LLM Top 10
│   │   │   └── rules.yaml          # Configurable scoring weights
│   │   ├── reports/
│   │   │   ├── pdf_generator.py    # Jinja2 + xhtml2pdf
│   │   │   ├── aibom_generator.py  # CycloneDX ML-BOM output
│   │   │   └── templates/
│   │   └── services/
│   │       ├── github_service.py   # Clone, list repos, OAuth
│   │       └── analysis_service.py # LLM-powered scan analysis (Claude API)
│   ├── tests/
│   └── alembic/                    # DB migrations
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── DependencyGraph.tsx  # React Flow interactive graph
│   │   │   ├── RiskDashboard.tsx    # Overview with Recharts
│   │   │   ├── ScanResults.tsx      # Findings table
│   │   │   ├── OwaspMapping.tsx     # OWASP LLM Top 10 coverage
│   │   │   └── RepoScanner.tsx      # Scan trigger UI
│   │   ├── pages/
│   │   └── lib/
│   └── public/
├── cli/                            # Thin CLI wrapper
│   └── scanllm_cli.py
├── signatures/
│   └── ai_signatures.yaml          # Externalized AI patterns
├── CLAUDE.md                       # This file
├── ROADMAP.md                      # Feature roadmap & specs
└── docker-compose.yml
```

## Core Scanning Engine — How It Works

### Step 1: Clone repo
Use GitPython to clone into a temp directory. Support both public URLs and private repos via GitHub OAuth token.

### Step 2: Walk all files
Recursively walk the repo, filtering by extension: `.py`, `.js`, `.ts`, `.jsx`, `.tsx`, `.ipynb`, `.yaml`, `.yml`, `.json`, `.toml`, `.env`, `.env.*`, `requirements.txt`, `pyproject.toml`, `Pipfile`, `package.json`, `Dockerfile`, `docker-compose.yml`, `.github/workflows/*.yml`

### Step 3: Parse by file type

**Python files (.py):** Use `ast.NodeVisitor` to walk the AST. Extract:
- `Import` and `ImportFrom` nodes → match against ai_signatures.yaml
- `Call` nodes → detect `client.chat.completions.create()`, `embeddings.create()`, etc.
- `Assign` nodes → track `model="gpt-4o"` parameter values
- String literals → detect model names, endpoint URLs
- f-strings/concatenation with user input → flag prompt injection risk

**JS/TS files (.js, .ts, .jsx, .tsx):** Regex-based for v1:
- `import ... from 'openai'` / `require('openai')` patterns
- `import ... from '@langchain/...'` patterns
- `import ... from '@anthropic-ai/sdk'` patterns
- `new OpenAI()`, `generateText()`, `streamText()` call patterns

**Config files:** PyYAML/json/tomllib parsing:
- Model name references (gpt-4o, claude-sonnet, llama-3, etc.)
- Endpoint URLs (api.openai.com, api.anthropic.com, etc.)
- Docker services (ollama, vllm, text-generation-inference)
- MCP server configs (claude_desktop_config.json, .cursor/mcp.json)

**Dependency files:** Parse and cross-reference against AI package list:
- requirements.txt, pyproject.toml, Pipfile, poetry.lock
- package.json, package-lock.json, yarn.lock

**Environment files (.env*):** 
- `detect-secrets` library for general secret detection
- Custom patterns for: OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY, PINECONE_API_KEY, HF_TOKEN, LANGCHAIN_API_KEY, AWS_BEDROCK_*, AZURE_OPENAI_*, and 30+ others

**Notebooks (.ipynb):** Extract code cells from JSON, run Python scanner on each.

### Step 4: Classify findings into component types
Each finding gets tagged with: `llm_provider`, `embedding_service`, `vector_db`, `orchestration_framework`, `agent_tool`, `prompt_file`, `mcp_server`, `inference_server`, `ai_package`, `secret`, `config_reference`

### Step 5: Build dependency graph edges
Use file-level and function-level relationships:
- Same file imports → components are co-located
- Import chains → A imports B which uses C
- Data flow → embedding output feeds vector DB input
- Config references → config file points to same model as code
- Agent tools → agent config lists tool functions defined elsewhere

Use `networkx.DiGraph` to build the graph. Each node has: id, type, label, files (with line numbers), metadata, risk_score. Each edge has: source, target, relationship type.

### Step 6: Serialize for frontend
Convert networkx graph to React Flow format:
```json
{
  "nodes": [{"id": "...", "type": "...", "position": {"x": 0, "y": 0}, "data": {...}}],
  "edges": [{"id": "...", "source": "...", "target": "...", "label": "..."}]
}
```
Use `dagre` layout algorithm (via Python `pygraphviz` or frontend `dagre`) for automatic positioning.

## AI Signatures File Format (ai_signatures.yaml)

```yaml
providers:
  openai:
    display_name: "OpenAI"
    category: "llm_provider"
    python:
      imports: ["openai", "from openai import"]
      calls: ["client.chat.completions.create", "openai.ChatCompletion.create", "client.embeddings.create"]
      models: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo", "o1", "o1-mini", "o1-pro", "o3", "o3-mini", "o4-mini"]
    javascript:
      imports: ["from 'openai'", "require('openai')"]
      calls: ["openai.chat.completions.create", "new OpenAI"]
    env_vars: ["OPENAI_API_KEY", "OPENAI_ORG_ID", "OPENAI_BASE_URL"]
    risk_weight: 1.0
    
  anthropic:
    display_name: "Anthropic"
    category: "llm_provider"
    python:
      imports: ["anthropic", "from anthropic import"]
      calls: ["client.messages.create", "client.completions.create"]
      models: ["claude-sonnet-4-20250514", "claude-opus-4-20250514", "claude-haiku-4-5-20251001"]
    env_vars: ["ANTHROPIC_API_KEY"]
    
  # ... 30+ more providers

vector_databases:
  chromadb:
    display_name: "ChromaDB"
    category: "vector_db"
    python:
      imports: ["chromadb", "from chromadb import"]
      calls: ["client.get_collection", "collection.add", "collection.query"]
    
  pinecone:
    display_name: "Pinecone"
    category: "vector_db"
    python:
      imports: ["pinecone", "from pinecone import"]
      calls: ["Pinecone()", "index.upsert", "index.query"]
    env_vars: ["PINECONE_API_KEY", "PINECONE_ENVIRONMENT"]

  # ... faiss, qdrant, weaviate, milvus, pgvector

frameworks:
  langchain:
    display_name: "LangChain"
    category: "orchestration_framework"
    python:
      imports: ["langchain", "langchain_openai", "langchain_anthropic", "langchain_community", "langchain_core", "langgraph"]
      calls: ["ChatOpenAI", "ChatAnthropic", "RetrievalQA", "ConversationalRetrievalChain"]
    
  # ... llamaindex, crewai, autogen, dspy, haystack

agents:
  crewai:
    display_name: "CrewAI"
    category: "agent_tool"
    python:
      imports: ["crewai", "from crewai import"]
      calls: ["Agent(", "Task(", "Crew("]
      risk_patterns:
        - pattern: "tools=["
          owasp: "LLM06"
          severity: "medium"
          message: "Agent with tool access — verify tools are least-privilege"

  mcp_server:
    display_name: "MCP Server"
    category: "mcp_server"
    config_files: ["claude_desktop_config.json", ".cursor/mcp.json", ".codex/config.toml"]
    python:
      imports: ["mcp", "from mcp import"]
    javascript:
      imports: ["@modelcontextprotocol/sdk"]
```

## OWASP LLM Top 10 2025 — Static Detection Patterns

Map these to scan findings:

| OWASP ID | Name | What ScanLLM detects | Severity |
|----------|------|---------------------|----------|
| LLM01 | Prompt Injection | User input concatenated into prompts without sanitization (f-strings, .format()) | High |
| LLM02 | Sensitive Info Disclosure | Credentials/PII in system prompts, missing output filtering | High |
| LLM03 | Supply Chain | Unverified model sources, outdated AI packages with CVEs, phantom dependencies | Critical |
| LLM05 | Improper Output Handling | `eval(llm_response)`, unsanitized LLM output to SQL/shell/HTML | Critical |
| LLM06 | Excessive Agency | Agent configs with broad tool access, missing human-in-the-loop | High |
| LLM07 | System Prompt Leakage | API keys/secrets in prompt templates, business logic in system prompts | Medium |
| LLM08 | Vector/Embedding Weaknesses | Unauthenticated vector DB connections, no access controls | Medium |
| LLM10 | Unbounded Consumption | Missing max_tokens, no rate limiting, no timeout on LLM calls | Low |

## Risk Scoring Formula

```
repo_risk_score = (
    secrets_found * 25 +           # Hardcoded keys are critical
    owasp_critical_count * 20 +     # Critical OWASP findings
    owasp_high_count * 10 +         # High OWASP findings
    outdated_packages * 5 +         # Known CVEs
    provider_concentration * 10 +   # Single provider dependency
    missing_safety_configs * 3 +    # No max_tokens, etc.
    excessive_agent_perms * 15      # Overprivileged agents
) / max_possible_score * 100       # Normalize to 0-100
```

## Coding Standards
- Python: Use type hints everywhere. Pydantic models for all API request/response schemas.
- FastAPI: Versioned API under /api/v1/. Use dependency injection for DB sessions.
- React: Functional components with hooks. shadcn/ui for all UI components. 
- Error handling: Never swallow exceptions. Log with structlog.
- Tests: pytest for backend, focus on scanner accuracy tests with fixture repos.

## Development Commands
```bash
# Backend
cd backend && uvicorn app.main:app --reload --port 8000

# Frontend  
cd frontend && npm run dev

# Run scanner tests
cd backend && pytest tests/scanner/ -v

# Format
ruff format backend/ && ruff check backend/ --fix
```

## Current State
- Production demo live at scanllm.ai
- All 5 development phases COMPLETE (see ROADMAP.md for details)
- 7 specialized scanners (Python AST, JS/TS, config, dependencies, notebooks, secrets) — 3,000+ lines
- Dependency graph with interactive React Flow visualization
- Risk scoring (0-100, A-F grades), OWASP LLM Top 10 mapping
- AI-BOM (CycloneDX 1.6), PDF reports, LLM-powered analysis
- CLI tool (910 lines), GitHub Actions integration, org/team management
- 145+ tests passing across all modules
- See ROADMAP.md for next feature prioritization (open-source vs paid tiers)

## Competitive Moat — Why ScanLLM Wins

ScanLLM's defensible position rests on five pillars. No single competitor combines all of these:

### 1. Only Tool Combining Code-Level AI Discovery + Dependency Graph + OWASP LLM Mapping
- **Cycode** ($80M) and **Noma** ($132M) are expensive, closed-source enterprise platforms where AI scanning is one feature among many. They sell top-down to CISOs, not bottom-up to developers.
- **Promptfoo** (open source) does LLM red teaming but does not scan codebases. It answers "are my prompts safe?" not "what AI is in my code?"
- **Snyk** found only 10/26 LLM-specific vulnerabilities in independent testing. AI scanning is a bolt-on.
- **Sonatype** does AI-BOM from package manifests but cannot discover AI usage at the code level.
- **ScanLLM** does AST-level Python analysis + JS/TS scanning + config/dependency/secret/notebook scanning, producing a dependency graph and OWASP risk mapping — in one open-source-friendly package.

### 2. AI Signatures Database (Compounding Data Asset)
The `ai_signatures.yaml` file (200+ detection patterns, 30+ providers) is a curated, community-maintainable asset. Every new AI framework, model, and tool that enters the ecosystem requires new patterns. Community contributions accelerate detection quality — a network effect competitors cannot replicate without open-sourcing their own signature sets.

### 3. Developer-First Distribution
`pip install scanllm && scanllm scan .` — zero-config, instant results. No enterprise sales cycle, no procurement, no demo call. Competitors (Cycode, Noma, Lakera) require paid accounts to even start scanning. ScanLLM's free CLI is the primary adoption vector.

### 4. Interactive Dependency Graph Intelligence
No competitor visualizes the relationship between LLM providers, vector databases, orchestration frameworks, and agent tools as a navigable, interactive graph. This is the "hero feature" that makes the invisible visible — the moment a CISO sees 47 AI components connected across 12 repos, the governance conversation starts.

### 5. CI/CD Integration Switching Cost
Once ScanLLM is in a team's GitHub Actions pipeline with configured policies, historical scan baselines, and trend reporting, switching requires re-establishing baselines, losing drift detection history, and reconfiguring all policy rules. This creates natural retention.

### Where ScanLLM Should NOT Compete
- **Runtime protection** (Lakera/Check Point, Noma) — requires agents/proxies in production, fundamentally different product
- **AI model governance/registry** (Credo AI, IBM watsonx.governance) — policy management platform, not a scanning tool
- **Shadow AI via network monitoring** (Witness AI) — requires network-level integration, not code scanning
- **Full SAST/SCA** (Snyk, Cycode) — ScanLLM integrates with these tools, does not replace them

**Positioning:** ScanLLM is the scanning engine layer that feeds into your existing security and governance stack. It produces the AI inventory that your GRC platform, your SAST tool, and your compliance team all need but cannot generate themselves.

## Target Customers

### Primary: AppSec / Platform Engineering Lead (Mid-Market)
- **Title:** Head of Application Security, Platform Engineering Lead, DevSecOps Manager
- **Company:** Series B-D tech company or mid-market enterprise (200-2,000 employees), 20-100 developers
- **Pain point:** "Our developers are using OpenAI, LangChain, and other AI tools, but we have no inventory. Our CISO needs an AI-BOM for SOC 2 audit, and we cannot produce one. We need this before our next board meeting / EU AI Act deadline / customer audit."
- **Why they buy (paid tier):** Org-wide scanning, AI-BOM generation, OWASP reports for auditors, trend reporting, CI/CD policy enforcement
- **Budget:** $500-2,000/month (VP Engineering or CISO approval, no board approval needed)
- **Buying trigger:** SOC 2 audit question, EU AI Act preparation, customer security questionnaire, security incident involving AI

### Secondary: Individual Developer / Tech Lead
- **Title:** Senior Developer, Tech Lead, Staff Engineer
- **Company:** Startup (10-50 people) or individual developer building AI-powered applications
- **Pain point:** "I want to understand my AI dependency tree, check for hardcoded keys, and make sure I'm not doing something obviously insecure. I don't want to pay $50K/year for Cycode to find out."
- **Why they use (free/OSS tier):** CLI scan, dependency graph, OWASP check, AI-BOM for documentation
- **Conversion trigger:** Team grows, adds more repos, starts getting compliance questions → upgrades because they already trust the tool

### Tertiary (Future): GRC / Compliance Team
- **Title:** Chief Compliance Officer, AI Governance Lead, Risk Manager
- **Company:** Large enterprise (2,000+ employees) or regulated industry (financial services, healthcare, government)
- **Pain point:** EU AI Act Article 9 requires documented AI system inventory. NIST AI RMF requires AI risk assessment. They need structured data feeding into their GRC platform.
- **Why they buy (enterprise tier):** API-first export to ServiceNow/Archer/OneTrust, scheduled scanning for continuous monitoring evidence, compliance report templates
- **Entry point:** Comes through the AppSec lead who already uses ScanLLM

## Open Source vs Paid Strategy
- **Open Source (Community Edition):** Genuinely useful single-repo scanning — CLI, signature database, JSON/CycloneDX output, detection accuracy improvements, new language support. Drives developer adoption and community contributions.
- **Paid (Team/Enterprise Edition):** Organizational visibility, historical tracking, compliance outputs, policy enforcement, team features. Solves problems that only matter at scale or under regulatory pressure.
- **The line feels natural:** Individual dev needs (free) vs team/enterprise needs (paid). The CLI never feels crippled.
