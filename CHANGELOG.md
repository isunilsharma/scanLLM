# Changelog

All notable changes to ScanLLM will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.4.0] - 2026-09-25

### Changed

- **Risk scores and grades will move on upgrade.** Several high-severity
  detections were false positives that inflated scores. Repositories will
  generally grade better than before. Teams with CI thresholds, saved
  baselines, or trend dashboards should expect a step change and re-baseline.
  Measured on public repos: `mckaywrigley/chatbot-ui` F (100) to B (30),
  `langchain-ai/langserve` B (30) to A (10).

### Fixed

- Secret scanning no longer reports identifier assignments as credentials. The
  generic `api_key = "..."` rule matched `api_key` as a substring of any
  identifier and accepted any 8+ character value, so a TypeScript enum of key
  *names* (`OPENAI_API_KEY = "OPENAI_API_KEY"`) was reported as eight hardcoded
  secrets. Values are now checked for plausibility (env-var-name shapes,
  interpolation, paths, prose, and low entropy are rejected).
- Prompt-injection detection no longer fires on every JavaScript template
  literal. The rule matched any `${...}` containing a word like "message" or
  "request", flagging `${error.message}` and `${request.status}` as LLM01. It
  is now gated on file-level prompt context and skips error formatting and UI
  plumbing. Measured: keeps 3/3 true positives, drops 10/10 false positives.
- `scan --severity` now filters results instead of being ignored.
- Scans are reproducible. `.scanllm/` was not excluded from the file walk, so
  each scan re-ingested the previous scan's saved output: findings inflated
  81 to 108 and the saved artifact grew 97KB to 1.5MB over four runs.
- `doctor` remediation hints keep their extras. Rich parsed `[server]` as a
  style tag and deleted it, rendering `pip install 'scanllm'`.
- Installing no longer warns about the `typer[all]` extra, which typer dropped
  in 0.13.
- Every finding now carries `severity` and `finding_type`. Consumers reading
  `findings[].severity` previously got `null`. `risk.severity_counts` and
  `summary.severities` contradicted each other and are now derived from one
  shared counter.
- The hosted backend produced different results from the CLI. It carried
  byte-identical copies of every scanner and scoring module, so none of the
  above fixes reached it. All are now thin re-exports over `core`, removing
  roughly 3,400 lines of duplication.

### Added

- `scan --fail-on <grade|severity>` exits 1 when a threshold is breached, so
  scans can gate CI. A bare `scan` still exits 0, unchanged.
- The findings table collapses duplicate rows with occurrence counts, caps
  output, and stays readable at 80 columns. A file emitting 18 identical
  import rows now shows one row with a count.
- `tests/e2e-install/`, a clean-room harness that pip installs the package the
  way a new user would, scans pinned open-source repos, and asserts on
  detection quality. Run `./run.sh --source local` before tagging and
  `--source pypi==<version>` after publishing.

## [2.3.0] - 2026-04-02

### Added

- Enterprise 8-tab interactive CLI dashboard (`scanllm ui`) with Overview, Findings, Risk, OWASP, Graph, Policies, History, and Export tabs
- Admin RBAC system — `ADMIN_EMAILS` env var bootstraps admin users via GitHub OAuth
- Admin telemetry dashboard at `/app/telemetry` (frontend, admin-only)
- Telemetry auto-collection after scan, score, and export commands
- Provider popularity tracking in telemetry events
- CLI telemetry management: `scanllm telemetry on/off/status`
- `SCANLLM_TELEMETRY` env var for global opt-out
- `get_admin_user` permission dependency for securing admin endpoints

### Changed

- Telemetry stats and feedback endpoints now require admin authentication
- CLI dashboard upgraded from 5-metric card to full 8-tab enterprise dashboard
- CycloneDX output uses dynamic version from `core.__version__`

### Removed

- Architecture page hidden from public navigation
- Hardcoded version numbers removed from homepage and CLI banner

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
