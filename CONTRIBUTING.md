# Contributing to ScanLLM

Thanks for your interest in contributing to ScanLLM! This guide covers everything you need to get started.

## Table of Contents

- [Development Setup](#development-setup)
- [Running Tests](#running-tests)
- [Adding AI Signatures](#adding-ai-signatures)
- [Code Style](#code-style)
- [Pull Request Guidelines](#pull-request-guidelines)
- [Where to Contribute](#where-to-contribute)

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Git

### Clone and Install

```bash
git clone https://github.com/isunilsharma/scanllm.git
cd scanllm

# Install CLI + core in editable mode with dev dependencies
pip install -e ".[dev]"

# Install backend dependencies
cd backend && pip install -r requirements.txt && cd ..

# Install frontend dependencies
cd frontend && npm install --legacy-peer-deps && cd ..
```

### Running Locally

```bash
# CLI (available immediately after pip install -e)
scanllm scan ./demo/sample_project

# Backend API server
cd backend && uvicorn app.main:app --reload --port 8001

# Frontend dev server
cd frontend && npm start
```

## Running Tests

### Backend / Core

```bash
cd backend && pytest tests/ -v

# Run only scanner tests
pytest tests/scanner/ -v

# Run with coverage
pytest tests/ --cov=app --cov=core -v
```

### Frontend

```bash
cd frontend && npm test
```

## Adding AI Signatures

This is the single highest-impact contribution you can make. The detection patterns in `config/ai_signatures.yaml` power all scanning.

### Signature Format

```yaml
providers:
  your_provider:
    display_name: "Your Provider"
    category: "llm_provider"        # or: vector_db, orchestration_framework, agent_tool, mcp_server
    python:
      imports: ["your_sdk", "from your_sdk import"]
      calls: ["client.generate", "client.chat"]
      models: ["your-model-v1", "your-model-v2"]
    javascript:
      imports: ["from 'your-sdk'", "require('your-sdk')"]
      calls: ["new YourSDK"]
    env_vars: ["YOUR_API_KEY", "YOUR_SECRET_KEY"]
    risk_weight: 1.0
```

### Categories

| Category | Use for |
|----------|---------|
| `llm_provider` | LLM API providers (OpenAI, Anthropic, Cohere, etc.) |
| `vector_db` | Vector databases (ChromaDB, Pinecone, Qdrant, etc.) |
| `orchestration_framework` | Orchestration layers (LangChain, LlamaIndex, Haystack, etc.) |
| `agent_tool` | Agent frameworks (CrewAI, AutoGen, etc.) |
| `mcp_server` | Model Context Protocol servers |

### Steps

1. Open `config/ai_signatures.yaml`
2. Add your provider/tool under the appropriate section
3. Include at least: `display_name`, `category`, and one detection method (`python.imports`, `env_vars`, etc.)
4. Run the scanner tests to verify detection: `cd backend && pytest tests/scanner/ -v`
5. Submit a PR with a brief description of what the provider/tool does

### Tips

- Check the existing entries for formatting examples
- For Python packages, look at the actual import paths (e.g., `langchain_openai` not `langchain-openai`)
- For JS packages, use the npm package name exactly as it appears in import statements
- Add model names when the provider has well-known model identifiers

## Code Style

### Python

- **Formatter/linter:** ruff
- **Type hints:** required on all function signatures
- **Models:** Pydantic for all API request/response schemas
- **Logging:** structlog (never use `print()` for operational output)
- **Error handling:** never swallow exceptions silently

```bash
# Format and lint
ruff format backend/ core/ cli/
ruff check backend/ core/ cli/ --fix
```

### Frontend (React/TypeScript)

- Functional components with hooks (no class components)
- shadcn/ui for all UI components
- Tailwind CSS for styling
- TypeScript strict mode

### General

- Keep functions focused and small
- Write docstrings for public functions
- Add type hints to all function parameters and return values

## Pull Request Guidelines

### Branch Naming

```
feature/add-mistral-signatures
fix/python-scanner-import-parsing
docs/update-contributing-guide
```

### Commit Messages

Use clear, descriptive commit messages:

```
Add Mistral AI detection signatures

- Added python imports, calls, and model patterns
- Added MISTRAL_API_KEY env var detection
- Added JS/TS import patterns for @mistralai/mistralai
```

### PR Checklist

- [ ] Tests pass (`pytest tests/ -v`)
- [ ] Code is formatted (`ruff format . && ruff check .`)
- [ ] Type hints on all new functions
- [ ] Docstrings on public functions
- [ ] For signature changes: verified detection works against a sample file
- [ ] PR description explains the "why" not just the "what"

### Review Process

1. Open a PR against `main`
2. Ensure CI checks pass
3. A maintainer will review and provide feedback
4. Once approved, the PR will be squash-merged

## Where to Contribute

Contributions are welcome everywhere, but these areas have the most impact:

### High Impact

- **New AI provider signatures** — every new provider helps the entire community
- **New language scanners** — Go, Rust, Java, C# support
- **Detection accuracy** — false positive/negative fixes in existing scanners

### Medium Impact

- **Documentation** — usage examples, tutorials, FAQ
- **OWASP detection rules** — new static analysis patterns for LLM vulnerabilities
- **Output formats** — new report formats or integrations

### Good First Issues

Look for issues labeled [`good first issue`](https://github.com/isunilsharma/scanllm/labels/good%20first%20issue) in the issue tracker. These are scoped, well-described tasks suitable for new contributors.

## Questions?

- Open a [GitHub issue](https://github.com/isunilsharma/scanllm/issues) for bugs or feature requests
- Email [hello@scanllm.ai](mailto:hello@scanllm.ai) for general questions

Thank you for helping make AI systems more transparent and secure!
