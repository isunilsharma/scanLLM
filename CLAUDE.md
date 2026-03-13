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
- MLP demo is live at scanllm.ai
- Basic repo scanning works (public + small private repos)
- Need to expand scanner coverage, add dependency graph, risk scoring, OWASP mapping
- See ROADMAP.md for full feature prioritization
