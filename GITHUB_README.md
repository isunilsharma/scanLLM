# ScanLLM.ai - AI Dependency Scanner

> **Analyze GitHub repositories and identify every AI/LLM integration—giving platform and infra teams a clear, accurate view of their real AI footprint.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.0+-blue.svg)](https://reactjs.org/)

## 🎯 Overview

ScanLLM.ai scans GitHub repositories to detect AI/LLM framework usage across your codebase. Built for engineering teams who need visibility into their AI surface area, it identifies:

- **Direct SDK calls** (OpenAI, Anthropic, etc.)
- **Framework usage** (LangChain, LlamaIndex, Transformers, vLLM)
- **RAG patterns** (vector stores, retrievers, embeddings)
- **Potential security risks** (hard-coded API keys)
- **AI hotspots** (directories with highest AI concentration)

## ✨ Features

### Core Capabilities
- 🔍 **Configurable Pattern Detection** - Regex-based scanning with 28+ built-in patterns
- 📊 **Executive Insights** - Key findings, risk flags, and recommended actions
- 🗺️ **AI Hotspots** - Identify which directories have the most AI usage
- 📈 **Framework Analytics** - Usage breakdown by category (LLM calls, embeddings, RAG)
- 💡 **Actionable Recommendations** - Tailored next steps for platform teams
- 🎨 **Interactive UI** - Filterable results, charts, and code snippet highlighting

### Advanced Features
- **Code Snippet Extraction** - See context around each match (3 lines before/after)
- **Severity Levels** - High/medium/low risk classification
- **Category Tagging** - llm_call, embedding_call, rag_pattern, secrets, etc.
- **Download Results** - Export scan data as JSON for integration
- **Multi-Framework Support** - Detect 7 major AI frameworks simultaneously

## 🏗️ Tech Stack

**Backend:**
- FastAPI (Python 3.11+)
- SQLAlchemy + SQLite
- GitPython for repository cloning
- PyYAML for configuration

**Frontend:**
- React 19
- Tailwind CSS + shadcn/ui components
- Recharts for data visualization
- Axios for API calls

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Node.js 18+ and Yarn
- Git

### Installation

1. **Clone the repository**
\`\`\`bash
git clone https://github.com/isunilsharma/iGraphCodeLLM.git
cd iGraphCodeLLM
\`\`\`

2. **Backend Setup**
\`\`\`bash
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Initialize the database
python -c "from core.database import init_db; init_db()"

# Start the backend server
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
\`\`\`

3. **Frontend Setup**

Open a new terminal:

\`\`\`bash
cd frontend

# Install dependencies
yarn install

# Create .env file
echo "REACT_APP_BACKEND_URL=http://localhost:8001" > .env

# Start the frontend
yarn start
\`\`\`

4. **Access the application**

Open your browser and navigate to: \`http://localhost:3000\`

## 📖 Usage

### Web Interface

1. **Enter a GitHub Repository URL**
   - Example: \`https://github.com/openai/openai-python\`
   - Only public repositories are currently supported

2. **Click "Start Scan"**
   - The scanner clones the repo, scans all code files, and detects AI/LLM patterns
   - Scan typically completes in 30-90 seconds depending on repository size

3. **Review Results**

   **Overview Tab:**
   - Key Insights summary
   - Risk Flags (security and complexity alerts)
   - Framework Usage Breakdown
   - AI Hotspots (directory concentration)
   - Recommended Actions
   - Interactive charts

   **Files Tab:**
   - Searchable/filterable file list
   - Click any file to see detailed occurrences
   - View code snippets with highlighted matches
   - Severity badges and pattern descriptions

   **Raw Data Tab:**
   - Full JSON response
   - Download or copy to clipboard

### API Usage

#### Start a Scan

\`\`\`bash
curl -X POST http://localhost:8001/api/scans \\
  -H "Content-Type: application/json" \\
  -d '{"repo_url": "https://github.com/openai/openai-python"}'
\`\`\`

**Response:**
\`\`\`json
{
  "scan_id": "uuid-string",
  "status": "SUCCESS",
  "repo_url": "https://github.com/openai/openai-python",
  "total_occurrences": 304,
  "files_count": 100,
  "frameworks_summary": [
    {
      "framework": "openai",
      "total_matches": 280,
      "files_count": 95,
      "categories": [
        {"category": "client_init", "count": 150},
        {"category": "llm_call", "count": 100},
        {"category": "embedding_call", "count": 30}
      ]
    }
  ],
  "hotspots": [
    {
      "directory": "examples/",
      "files_with_ai": 45,
      "total_matches": 180
    }
  ],
  "risk_flags": [
    {
      "id": "llm_only_no_rag",
      "label": "Only direct LLM calls (no RAG)",
      "severity": "low",
      "description": "This repository uses LLM calls but no embeddings or RAG patterns. Migration is likely simpler."
    }
  ],
  "recommended_actions": [
    {
      "id": "establish_monitoring",
      "title": "Establish AI usage monitoring",
      "description": "Consider adding observability around LLM calls: latency tracking, token usage monitoring, and error rate tracking.",
      "related_risk_flags": []
    }
  ],
  "files": [...]
}
\`\`\`

#### Retrieve a Scan

\`\`\`bash
curl -X GET http://localhost:8001/api/scans/{scan_id}
\`\`\`

#### Get Pattern Configuration

\`\`\`bash
curl -X GET http://localhost:8001/api/config/patterns
\`\`\`

## ⚙️ Configuration

### Pattern Configuration (\`config/patterns.yml\`)

Define custom patterns to detect specific AI/LLM usage:

\`\`\`yaml
frameworks:
  openai:
    description: "Direct usage of OpenAI client SDK"
    patterns:
      - name: "openai_chat_completion_new"
        regex: "\\\\bclient\\\\.chat\\\\.completions\\\\.create\\\\b"
        enabled: true
        category: "llm_call"
        severity: "low"
        description: "OpenAI chat completion (modern client)"
        tags:
          - "chat"
          - "llm"
\`\`\`

**Pattern Fields:**
- \`name\`: Unique identifier
- \`regex\`: Python regex pattern
- \`enabled\`: true/false
- \`category\`: llm_call, embedding_call, client_init, rag_pattern, secrets, gateway_bypass, misc
- \`severity\`: low, medium, high
- \`description\`: Human-readable description
- \`tags\`: Optional list of tags

### Scanner Settings (\`config/settings.yml\`)

\`\`\`yaml
scan:
  file_extensions:
    - ".py"
    - ".js"
    - ".ts"
    - ".tsx"
    - ".jsx"
    - ".ipynb"
  max_file_size_bytes: 500000
  exclude_paths:
    - "node_modules"
    - ".git"
    - "dist"
    - "build"
    - "__pycache__"

git:
  shallow_clone: true
  depth: 1
\`\`\`

## 📊 Supported Frameworks

| Framework | Patterns | Detection Types |
|-----------|----------|-----------------|
| **OpenAI** | 7 patterns | Chat, Embeddings, Images, Client Init, Secrets |
| **Anthropic** | 3 patterns | Messages, Client Init |
| **LangChain** | 6 patterns | Chains, Chat Models, Retrievers, VectorStores |
| **Transformers** | 3 patterns | Pipelines, AutoModels, Imports |
| **vLLM** | 2 patterns | Local Model Initialization |
| **RAG (Generic)** | 5 patterns | VectorStores, Retrievers, FAISS, Chroma, Pinecone |
| **LlamaIndex** | 2 patterns | Imports, ServiceContext |

## 🔬 Architecture

\`\`\`
┌─────────────────────────────────────────────────────────────┐
│                       Frontend (React)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   Home   │  │   Blog   │  │  About   │  │ How It   │   │
│  │          │  │          │  │          │  │  Works    │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│         │                                                    │
│         └─────────► Scan Results (3 Tabs)                   │
│                     Overview│Files│Raw Data                 │
└─────────────────────────────┼──────────────────────────────┘
                              │
                              │ REST API
                              │
┌─────────────────────────────┼──────────────────────────────┐
│                       Backend (FastAPI)                      │
│  ┌──────────────────────────▼─────────────────────────┐    │
│  │  POST /api/scans  │  GET /api/scans/{id}          │    │
│  └──────────────────────────┬─────────────────────────┘    │
│                              │                               │
│  ┌──────────────────────────▼─────────────────────────┐    │
│  │           Scanner Service                           │    │
│  │  1. Clone repo (GitPython)                         │    │
│  │  2. Scan files (Regex matching)                    │    │
│  │  3. Extract snippets                               │    │
│  │  4. Compute insights                               │    │
│  └──────────────────────────┬─────────────────────────┘    │
│                              │                               │
│  ┌──────────────────────────▼─────────────────────────┐    │
│  │           Insights Engine                           │    │
│  │  - Framework Summary                               │    │
│  │  - Hotspot Detection                               │    │
│  │  - Risk Flag Analysis                              │    │
│  │  - Action Recommendations                          │    │
│  └──────────────────────────┬─────────────────────────┘    │
│                              │                               │
│  ┌──────────────────────────▼─────────────────────────┐    │
│  │         Database (SQLite)                           │    │
│  │  Tables: scan_jobs, findings                       │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
\`\`\`

## 🧪 Development

### Project Structure

\`\`\`
iGraphCodeLLM/
├── backend/
│   ├── core/
│   │   ├── config.py          # Configuration loader
│   │   └── database.py        # SQLAlchemy setup
│   ├── models/
│   │   ├── scan.py            # ScanJob model
│   │   └── finding.py         # Finding model
│   ├── services/
│   │   ├── scanner.py         # Core scanning logic
│   │   ├── git_utils.py       # Git operations
│   │   └── insights.py        # Analytics engine
│   ├── server.py              # FastAPI app & routes
│   ├── requirements.txt       # Python dependencies
│   └── app.db                 # SQLite database
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/            # shadcn/ui components
│   │   │   ├── Header.jsx
│   │   │   ├── Footer.jsx
│   │   │   ├── Logo.jsx
│   │   │   ├── KeyInsights.jsx
│   │   │   ├── RiskFlags.jsx
│   │   │   ├── AIHotspots.jsx
│   │   │   ├── UsageTypes.jsx
│   │   │   ├── RecommendedActions.jsx
│   │   │   ├── FileList.jsx
│   │   │   └── ScanResults.jsx
│   │   ├── pages/
│   │   │   ├── Home.jsx
│   │   │   ├── HowItWorks.jsx
│   │   │   ├── About.jsx
│   │   │   ├── Blog.jsx
│   │   │   └── BlogPost.jsx
│   │   ├── App.js
│   │   └── App.css
│   ├── package.json
│   └── .env
│
└── config/
    ├── patterns.yml           # Pattern definitions
    └── settings.yml           # Scanner configuration
\`\`\`

### Running Tests

**Backend Tests:**
\`\`\`bash
cd backend
python backend_test.py
\`\`\`

**Frontend Tests:**
\`\`\`bash
cd frontend
yarn test
\`\`\`

### Adding New Patterns

1. Edit \`config/patterns.yml\`:

\`\`\`yaml
frameworks:
  your_framework:
    description: "Your framework description"
    patterns:
      - name: "your_pattern_name"
        regex: "\\\\byour_regex_pattern\\\\b"
        enabled: true
        category: "llm_call"  # or embedding_call, rag_pattern, etc.
        severity: "medium"    # low, medium, or high
        description: "What this pattern detects"
        tags:
          - "your_tag"
\`\`\`

2. Restart the backend server to reload patterns

### Database Migrations

When updating models, recreate the database:

\`\`\`bash
cd backend
rm app.db
python -c "from core.database import init_db; init_db()"
\`\`\`

## 🐳 Docker Deployment

**Using Docker Compose:**

\`\`\`yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8001:8001"
    environment:
      - CORS_ORIGINS=*
    volumes:
      - ./config:/app/config
      - ./backend/app.db:/app/backend/app.db

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_BACKEND_URL=http://localhost:8001
    depends_on:
      - backend
\`\`\`

Run with:
\`\`\`bash
docker-compose up
\`\`\`

## 📝 API Documentation

### Endpoints

#### \`POST /api/scans\`
Start a new repository scan.

**Request:**
\`\`\`json
{
  "repo_url": "https://github.com/owner/repo"
}
\`\`\`

**Response:** Full scan results with insights (see Quick Start section above).

#### \`GET /api/scans/{scan_id}\`
Retrieve a completed scan by ID.

**Response:** Same structure as POST /api/scans.

#### \`GET /api/config/patterns\`
Get current pattern configuration.

**Response:**
\`\`\`json
{
  "frameworks": [
    {
      "name": "openai",
      "description": "Direct usage of OpenAI client SDK",
      "patterns": [
        {
          "name": "openai_chat_completion_new",
          "regex": "\\\\bclient\\\\.chat\\\\.completions\\\\.create\\\\b",
          "enabled": true,
          "category": "llm_call",
          "severity": "low",
          "description": "OpenAI chat completion (modern client)"
        }
      ]
    }
  ]
}
\`\`\`

#### \`GET /health\`
Health check endpoint.

## 🎨 Frontend Pages

- **Home** (\`/\`) - Main scanning interface
- **How It Works** (\`/how-it-works\`) - Product explanation
- **Blog** (\`/blog\`) - Articles about AI dependency management
- **About Us** (\`/about\`) - Company information with demo booking

## 🔧 Configuration Options

### File Extensions to Scan

Edit \`config/settings.yml\`:

\`\`\`yaml
scan:
  file_extensions:
    - ".py"
    - ".js"
    - ".ts"
    - ".tsx"
    - ".jsx"
    - ".ipynb"
\`\`\`

### Exclude Paths

\`\`\`yaml
scan:
  exclude_paths:
    - "node_modules"
    - ".git"
    - "dist"
    - "build"
    - "__pycache__"
    - ".venv"
    - "venv"
\`\`\`

### Max File Size

\`\`\`yaml
scan:
  max_file_size_bytes: 500000  # 500 KB
\`\`\`

### Git Clone Settings

\`\`\`yaml
git:
  shallow_clone: true
  depth: 1
\`\`\`

## 📊 Supported Frameworks

| Framework | Patterns | Detection Types |
|-----------|----------|-----------------|
| **OpenAI** | 7 patterns | Chat, Embeddings, Images, Client Init, Secrets |
| **Anthropic** | 3 patterns | Messages, Client Init |
| **LangChain** | 6 patterns | Chains, Chat Models, Retrievers, VectorStores |
| **Transformers** | 3 patterns | Pipelines, AutoModels, Imports |
| **vLLM** | 2 patterns | Local Model Initialization |
| **RAG (Generic)** | 5 patterns | VectorStores, Retrievers, FAISS, Chroma, Pinecone |
| **LlamaIndex** | 2 patterns | Imports, ServiceContext |

## 🛡️ Security Considerations

- **Public Repos Only**: Currently supports only public GitHub repositories
- **Temporary Storage**: Cloned repos are stored in temp directories and deleted after scanning
- **No Code Persistence**: Source code is never stored in the database
- **API Key Detection**: Scanner can detect potential hard-coded API keys (severity: high)

## 🐛 Troubleshooting

### Backend Won't Start

\`\`\`bash
# Check if port 8001 is available
lsof -i :8001

# Verify database
python -c "from core.database import init_db; init_db()"

# Check dependencies
pip install -r requirements.txt
\`\`\`

### Frontend Build Errors

\`\`\`bash
# Clear cache and reinstall
rm -rf node_modules yarn.lock
yarn install

# Check environment variables
cat .env
\`\`\`

### Scan Fails

**Common issues:**
- Invalid GitHub URL → Ensure it's a public repository
- Repo too large → Increase \`max_file_size_bytes\` in settings.yml
- Network timeout → Check internet connectivity
- Git not installed → Install Git on your system

## 📈 Roadmap

- [ ] Private repository support (GitHub OAuth)
- [ ] CI/CD integration (GitHub Actions, GitLab CI)
- [ ] Multi-repo aggregation and comparison
- [ ] Slack/email notifications for scan completion
- [ ] Custom pattern templates
- [ ] AST-based analysis (beyond regex)
- [ ] Cost estimation based on detected LLM usage
- [ ] Drift detection (compare scans over time)
- [ ] Enterprise features (SSO, role-based access)

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (\`git checkout -b feature/your-feature\`)
3. Commit your changes (\`git commit -m 'Add your feature'\`)
4. Push to the branch (\`git push origin feature/your-feature\`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 for Python code
- Use ESLint/Prettier for JavaScript/React
- Add tests for new features
- Update documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 💬 Support

- **Website**: [scanllm.ai](https://scanllm.ai)
- **Email**: hello@scanllm.ai
- **Book a Demo**: [https://calendly.com/sunildec1991/30min](https://calendly.com/sunildec1991/30min)
- **Issues**: [GitHub Issues](https://github.com/isunilsharma/iGraphCodeLLM/issues)

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- UI components from [shadcn/ui](https://ui.shadcn.com/)
- Charts powered by [Recharts](https://recharts.org/)
- Icons from [Lucide React](https://lucide.dev/)

## 📸 Screenshots

### Scan Results - Overview Tab
![Overview Tab](docs/screenshots/overview.png)

### Scan Results - Files Tab with Code Snippets
![Files Tab](docs/screenshots/files.png)

### Key Insights & Risk Flags
![Insights](docs/screenshots/insights.png)

---

**Built for modern AI engineering teams.**

© 2025 ScanLLM.ai
