<p align="center">
  <h1 align="center">ScanLLM</h1>
  <p align="center"><strong>AI Dependency Intelligence for Engineering Teams</strong></p>
  <p align="center">Discover, map, and govern every AI/LLM component in your codebase.</p>
</p>

<p align="center">
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python 3.11+"></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-0.110+-green.svg" alt="FastAPI"></a>
  <a href="https://reactjs.org/"><img src="https://img.shields.io/badge/React-19-blue.svg" alt="React 19"></a>
  <a href="https://scanllm.ai"><img src="https://img.shields.io/badge/demo-scanllm.ai-purple.svg" alt="Live Demo"></a>
</p>

---

## What is ScanLLM?

ScanLLM answers the question no existing tool answers: **"What AI is in our code, where, and what depends on what?"**

It scans GitHub repositories to produce a complete inventory of AI/LLM dependencies — from direct SDK calls and framework usage to hardcoded secrets and agent configurations — then visualizes the relationships as an interactive dependency graph with OWASP LLM Top 10 risk mapping.

**Built for AppSec teams, platform engineers, and developers** who need AI governance without a six-figure enterprise contract.

### Key Capabilities

- **7 specialized scanners** — Python AST analysis, JS/TS regex scanning, config/dependency/notebook/secret detection
- **200+ AI detection patterns** — OpenAI, Anthropic, LangChain, LlamaIndex, CrewAI, ChromaDB, Pinecone, and 30+ more providers
- **Interactive dependency graph** — Visualize how LLM providers, vector databases, orchestration frameworks, and agent tools connect
- **OWASP LLM Top 10 mapping** — Automatically flag prompt injection, sensitive data disclosure, excessive agency, and more
- **Risk scoring (0-100)** — Weighted scoring across secrets, OWASP findings, provider concentration, and safety configurations
- **AI-BOM generation** — CycloneDX 1.6 machine-learning bill of materials for compliance
- **PDF executive reports** — One-click export for auditors and leadership
- **CI/CD integration** — GitHub Actions workflow for continuous scanning with policy enforcement

## Quick Start

### Docker (Recommended)

```bash
git clone https://github.com/isunilsharma/ScanLLM.git
cd ScanLLM

# Set your GitHub OAuth credentials
export GITHUB_CLIENT_ID=your_client_id
export GITHUB_CLIENT_SECRET=your_client_secret

docker compose up --build
```

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8001
- **API Docs:** http://localhost:8001/docs

### CLI

```bash
pip install scanllm
scanllm scan https://github.com/your-org/your-repo
```

### Manual Setup

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001

# Frontend (separate terminal)
cd frontend
npm install --legacy-peer-deps
npm start
```

## Architecture

```
scanllm/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application entry point
│   │   ├── config.py            # Pydantic settings (env var driven)
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── api/v1/              # Versioned REST API endpoints
│   │   ├── scanner/             # Core scanning engine (7 modules)
│   │   ├── graph/               # Dependency graph builder + serializer
│   │   ├── scoring/             # Risk engine + OWASP mapper
│   │   ├── reports/             # PDF + CycloneDX AI-BOM generators
│   │   └── services/            # GitHub OAuth, LLM analysis
│   └── tests/                   # 145+ pytest tests
├── frontend/
│   └── src/
│       ├── components/          # React Flow graph, risk dashboard, OWASP mapping
│       ├── pages/               # Dashboard, scan results, auth
│       └── lib/                 # API client, utilities
├── cli/                         # CLI tool (pip install scanllm)
├── config/
│   ├── ai_signatures.yaml       # 200+ AI detection patterns
│   ├── patterns.yml             # Regex pattern definitions
│   ├── policies.yml             # Scan policy rules
│   └── settings.yml             # Scanner configuration
├── docker-compose.yml           # PostgreSQL + backend + frontend
└── render.yaml                  # One-click Render deployment
```

## How Scanning Works

```
Clone Repo → Walk Files → Parse by Type → Classify Findings → Build Graph → Score Risk
```

| Scanner | Files | Technique |
|---------|-------|-----------|
| **Python** | `.py` | AST visitor — imports, calls, model params, f-string injection |
| **JavaScript/TS** | `.js`, `.ts`, `.jsx`, `.tsx` | Regex — import/require, SDK instantiation, API calls |
| **Config** | `.yaml`, `.json`, `.toml`, `.env` | Structure parsing — model refs, endpoints, MCP configs |
| **Dependencies** | `requirements.txt`, `package.json`, etc. | Package cross-reference against AI provider database |
| **Notebooks** | `.ipynb` | Cell extraction + Python scanner per cell |
| **Secrets** | All files | detect-secrets + 30+ AI-specific key patterns |
| **Dependency Graph** | All findings | networkx DiGraph with React Flow visualization |

## OWASP LLM Top 10 Coverage

| ID | Vulnerability | What ScanLLM Detects |
|----|--------------|---------------------|
| LLM01 | Prompt Injection | User input concatenated into prompts (f-strings, `.format()`) |
| LLM02 | Sensitive Info Disclosure | Credentials/PII in system prompts |
| LLM03 | Supply Chain | Unverified model sources, outdated AI packages |
| LLM05 | Improper Output Handling | `eval(llm_response)`, unsanitized output to SQL/shell |
| LLM06 | Excessive Agency | Broad agent tool access, missing human-in-the-loop |
| LLM07 | System Prompt Leakage | API keys in prompt templates |
| LLM08 | Vector/Embedding Weaknesses | Unauthenticated vector DB connections |
| LLM10 | Unbounded Consumption | Missing `max_tokens`, no rate limiting |

## API Reference

### Start a Scan

```bash
curl -X POST http://localhost:8001/api/v1/scans/github \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/openai/openai-python", "full_scan": true}'
```

### Get Scan Results

```bash
curl http://localhost:8001/api/v1/scans/{scan_id} \
  -H "Authorization: Bearer <token>"
```

### Generate AI-BOM

```bash
curl http://localhost:8001/api/v1/reports/{scan_id}/aibom \
  -H "Authorization: Bearer <token>"
```

### Export PDF Report

```bash
curl http://localhost:8001/api/v1/reports/{scan_id}/pdf \
  -H "Authorization: Bearer <token>" \
  -o report.pdf
```

Full API documentation available at `/docs` when running the backend.

## Configuration

### AI Signatures (`config/ai_signatures.yaml`)

Add custom detection patterns:

```yaml
providers:
  your_provider:
    display_name: "Your Provider"
    category: "llm_provider"
    python:
      imports: ["your_sdk", "from your_sdk import"]
      calls: ["client.generate"]
      models: ["your-model-v1"]
    env_vars: ["YOUR_API_KEY"]
```

### Scanner Settings (`config/settings.yml`)

```yaml
scan:
  file_extensions: [".py", ".js", ".ts", ".tsx", ".jsx", ".ipynb"]
  max_file_size_bytes: 500000
  exclude_paths: ["node_modules", ".git", "dist", "__pycache__"]
```

## Deployment

### Render (One-Click)

The included `render.yaml` provisions PostgreSQL, backend, and frontend automatically:

1. Connect your GitHub repo to Render
2. Create a **Blueprint** from `render.yaml`
3. Set secret environment variables: `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `ANTHROPIC_API_KEY`

### Docker Compose (Self-Hosted)

```bash
docker compose up -d
```

Services: PostgreSQL 16, FastAPI backend, React frontend. Data persists via named volume.

## Development

```bash
# Run tests
cd backend && pytest tests/ -v

# Format code
ruff format backend/ && ruff check backend/ --fix

# Frontend dev server (hot reload)
cd frontend && npm start
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI, SQLAlchemy, PostgreSQL, GitPython, networkx |
| **Frontend** | React 19, Tailwind CSS, shadcn/ui, React Flow, Recharts |
| **Scanning** | Python AST, PyYAML, detect-secrets, CycloneDX |
| **Auth** | GitHub OAuth, JWT sessions, encrypted token storage |
| **Infra** | Docker, Render, GitHub Actions |

## Why ScanLLM?

| | ScanLLM | Cycode/Noma | Snyk | Promptfoo |
|---|---------|-------------|------|-----------|
| Code-level AI discovery | Yes | Partial | Limited | No |
| Dependency graph | Yes | No | No | No |
| OWASP LLM mapping | Yes | Yes | No | Partial |
| AI-BOM (CycloneDX) | Yes | No | No | No |
| Open source CLI | Yes | No | No | Yes |
| Zero-config setup | Yes | No | No | Yes |
| Price | Free / Team tier | $50K+/yr | $25K+/yr | Free |

## Contributing

Contributions are welcome. See the [config/ai_signatures.yaml](config/ai_signatures.yaml) file — adding detection patterns for new AI frameworks is the highest-impact contribution.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes
4. Open a Pull Request

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Links

- **Live Demo:** [scanllm.ai](https://scanllm.ai)
- **Book a Demo:** [calendly.com/sunildec1991/30min](https://calendly.com/sunildec1991/30min)
- **Email:** hello@scanllm.ai
- **Issues:** [GitHub Issues](https://github.com/isunilsharma/ScanLLM/issues)

---

Built for engineering teams who need to know what AI is in their code.
