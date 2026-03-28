# Changelog

All notable changes to ScanLLM will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-03-28

### Added

- Core engine extraction -- shared `core/` package usable by CLI, backend, and integrations
- Typer-based CLI with 8 commands: `scan`, `init`, `policy`, `diff`, `ui`, `watch`, `report`, `fix`
- Policy-as-code engine with configurable YAML rules for CI/CD gating
- Scan diffing and drift detection (`scanllm diff`)
- SARIF output format for GitHub Code Scanning integration
- CycloneDX 1.6 AI-BOM export (`scanllm report aibom`)
- Local dashboard server (`scanllm ui`) with interactive dependency graph
- Pre-commit hook support (`scanllm-policy-check`, `scanllm-secret-check`)
- GitHub Action for CI/CD (`isunilsharma/scanllm@v2`)
- Enterprise API endpoints: org dashboard, cost insights, audit log
- Auto-fix suggestions for all finding types (`scanllm fix`)
- File watch mode for continuous scanning during development (`scanllm watch`)
- Demo project for onboarding and testing (`demo/sample_project/`)

### Changed

- CLI rewritten from monolithic argparse script to modular Typer commands
- Scanner engine extracted from backend into shared `core/` package
- Signature loading works across all deployment contexts (pip install, Docker, dev mode)
- Landing page redesigned with dark theme and animated terminal demo

### Fixed

- Signature file resolution across pip, Docker, and editable install contexts
- Python AST scanner handles syntax errors in scanned files gracefully
- JS/TS scanner no longer flags commented-out imports as findings

## [1.0.0] - 2026-01-15

### Added

- Initial release
- 7 specialized scanners: Python AST, JS/TS, config, dependency, notebook, secret, dependency graph
- 200+ AI detection patterns across 30+ providers
- Interactive dependency graph visualization with React Flow
- Risk scoring (0-100) with A-F letter grades
- OWASP LLM Top 10 mapping for 8 vulnerability categories
- PDF executive reports via Jinja2 + xhtml2pdf
- CycloneDX AI-BOM generation
- GitHub OAuth authentication
- Organization and team management
- LLM-powered scan analysis via Claude API
- Docker Compose deployment (PostgreSQL + FastAPI + React)
- One-click Render deployment via `render.yaml`
- 145+ tests across all modules
