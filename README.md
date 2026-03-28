<p align="center">
  <h1 align="center">ScanLLM</h1>
  <p align="center"><strong>Know every AI dependency. Enforce every policy.</strong></p>
</p>

<p align="center">
  <a href="https://pypi.org/project/scanllm/"><img src="https://img.shields.io/pypi/v/scanllm?color=blue&label=PyPI" alt="PyPI version"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.11+-3776AB.svg?logo=python&logoColor=white" alt="Python 3.11+"></a>
  <a href="https://github.com/isunilsharma/scanllm"><img src="https://img.shields.io/github/stars/isunilsharma/scanllm?style=social" alt="GitHub stars"></a>
  <a href="https://github.com/isunilsharma/scanllm/actions"><img src="https://img.shields.io/github/actions/workflow/status/isunilsharma/scanllm/ci.yml?label=CI" alt="CI status"></a>
</p>

<p align="center">
  <a href="https://scanllm.ai">Website</a> &middot;
  <a href="https://docs.scanllm.ai">Docs</a> &middot;
  <a href="#quick-start">Quick Start</a> &middot;
  <a href="https://github.com/isunilsharma/scanllm/issues">Issues</a>
</p>

---

ScanLLM scans your codebase to discover every AI/LLM dependency — SDK imports, model references, API keys, agent configs, vector databases — and maps them into an interactive dependency graph with risk scores and OWASP LLM Top 10 coverage.

Think **"Snyk for AI systems."** No six-figure contract required.

## Quick Start

```bash
pip install scanllm
scanllm scan .
scanllm ui          # launch local dashboard
```

That's it. Three commands, zero config.

## What It Finds

- **30+ AI providers** — OpenAI, Anthropic, Google, Cohere, Mistral, AWS Bedrock, Azure OpenAI, and more
- **200+ detection patterns** — imports, SDK calls, model parameters, config references, env vars
- **OWASP LLM Top 10** — prompt injection, excessive agency, supply chain, sensitive data disclosure
- **Hardcoded secrets** — AI API keys across 30+ providers (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, ...)
- **Agent risks** — overprivileged tools, missing human-in-the-loop, broad MCP server configs

## Features

| Feature | Description |
|---------|-------------|
| **AI Dependency Discovery** | AST-level Python analysis, JS/TS scanning, config/dependency/notebook/secret detection across 7 specialized scanners |
| **Interactive Dependency Graph** | Visualize how LLM providers, vector DBs, frameworks, and agents connect — powered by React Flow |
| **Risk Scoring** | 0-100 score with A-F grades based on secrets, OWASP findings, provider concentration, and safety gaps |
| **Policy as Code** | YAML rules that run in CI/CD — exit code 1 means the build fails |
| **AI-BOM** | CycloneDX 1.6 ML-BOM export for SOC 2, EU AI Act, and NIST AI RMF compliance |
| **Drift Detection** | Compare scans over time to catch new AI dependencies before they reach production |
| **Auto-Fix Suggestions** | Remediation guidance for every finding |
| **Local Dashboard** | `scanllm ui` launches an interactive web UI on localhost |
| **SARIF Output** | Upload results to GitHub Code Scanning |

## CLI Commands

```
scanllm scan <path>          Scan a repo or directory for AI dependencies
scanllm init                 Initialize a .scanllm.yaml config in your project
scanllm policy check         Validate against policy rules (CI/CD gate)
scanllm diff <a> <b>         Compare two scan results for drift detection
scanllm report pdf <scan>    Generate PDF executive report
scanllm report aibom <scan>  Export CycloneDX AI-BOM (JSON)
scanllm ui                   Launch local web dashboard
scanllm watch                Watch for file changes and re-scan automatically
scanllm fix                  Show auto-fix suggestions for findings
```

### Scan Options

```bash
scanllm scan . --output json           # JSON output
scanllm scan . --output sarif          # SARIF for GitHub Code Scanning
scanllm scan . --output cyclonedx      # CycloneDX AI-BOM
scanllm scan . --severity high         # Only high+ severity findings
scanllm scan . --full-scan             # Include all file types
```

## Why Not Snyk / Cycode / Promptfoo?

| | ScanLLM | Cycode / Noma | Snyk | Promptfoo |
|---|---------|--------------|------|-----------|
| Code-level AI discovery | Yes | Partial | Limited | No |
| Interactive dependency graph | Yes | No | No | No |
| OWASP LLM Top 10 mapping | Yes | Yes | No | Partial |
| AI-BOM (CycloneDX) | Yes | No | No | No |
| Open source CLI | Yes | No | No | Yes |
| Zero-config setup | Yes | No | No | Yes |
| Price | **Free** / Team tier | $50K+/yr | $25K+/yr | Free |

Snyk found only 10/26 LLM-specific vulnerabilities in independent testing. Cycode and Noma require six-figure contracts. Promptfoo tests prompts but does not scan codebases. ScanLLM does code-level discovery, dependency graphing, and OWASP mapping in one tool.

## CI/CD Integration

### GitHub Actions

```yaml
name: ScanLLM AI Security
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  scanllm:
    runs-on: ubuntu-latest
    permissions:
      security-events: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
      - uses: isunilsharma/scanllm@v2
        with:
          severity_threshold: medium
          fail_on_policy_violation: true
          upload_sarif: true
```

### Pre-commit

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/isunilsharma/scanllm
    rev: v2.0.0
    hooks:
      - id: scanllm-policy-check
      - id: scanllm-secret-check
```

## OWASP LLM Top 10 Coverage

| ID | Vulnerability | What ScanLLM Detects |
|----|--------------|---------------------|
| LLM01 | Prompt Injection | User input in f-strings/`.format()` passed to LLM calls |
| LLM02 | Sensitive Info Disclosure | Credentials and PII in system prompts |
| LLM03 | Supply Chain | Unverified model sources, outdated AI packages |
| LLM05 | Improper Output Handling | `eval(llm_response)`, unsanitized output to SQL/shell |
| LLM06 | Excessive Agency | Broad agent tool access, missing human-in-the-loop |
| LLM07 | System Prompt Leakage | API keys in prompt templates |
| LLM08 | Vector/Embedding Weaknesses | Unauthenticated vector DB connections |
| LLM10 | Unbounded Consumption | Missing `max_tokens`, no rate limiting |

## Try It on a Demo Project

```bash
git clone https://github.com/isunilsharma/scanllm.git
cd scanllm/demo/sample_project
pip install scanllm
scanllm scan .
```

The demo project contains intentional AI security issues to showcase detection capabilities. See [`demo/`](demo/) for details.

## For Teams (Cloud)

The free CLI covers individual and single-repo use. For teams that need organizational visibility:

- **Multi-repo scanning** with a unified dashboard
- **Historical trend tracking** and drift alerts
- **Compliance reports** (PDF, AI-BOM) for auditors
- **Policy enforcement** across all repositories
- **SSO and team management**

Learn more at [scanllm.ai](https://scanllm.ai).

## Self-Hosted Setup

### Docker Compose

```bash
git clone https://github.com/isunilsharma/scanllm.git
cd scanllm
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/docs

### Manual

```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001

# Frontend
cd frontend && npm install --legacy-peer-deps && npm start
```

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions, coding standards, and PR guidelines.

**Highest-impact contributions:** adding AI detection patterns to [`config/ai_signatures.yaml`](config/ai_signatures.yaml). Every new AI framework, model, or tool you add helps the entire community.

## License

[MIT](LICENSE)

---

<p align="center">
  <a href="https://scanllm.ai">scanllm.ai</a> &middot;
  <a href="mailto:hello@scanllm.ai">hello@scanllm.ai</a> &middot;
  <a href="https://github.com/isunilsharma/scanllm/issues">Report a Bug</a>
</p>
