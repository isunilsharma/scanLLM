#!/usr/bin/env python3
"""ScanLLM CLI — AI Dependency Intelligence Scanner.

Scan codebases for AI/LLM dependencies, generate risk scores, and OWASP mapping.

Usage:
    scanllm scan <repo-url-or-local-path> [options]

Examples:
    scanllm scan ./my-project
    scanllm scan https://github.com/org/repo
    scanllm scan . --output json
    scanllm scan ./src --severity high --full-scan
    scanllm scan . --output cyclonedx > ai-bom.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# ANSI colour helpers (no external dependency)
# ---------------------------------------------------------------------------

_NO_COLOR = os.environ.get("NO_COLOR") is not None or not sys.stdout.isatty()


def _ansi(code: str) -> str:
    return "" if _NO_COLOR else code


class _C:
    """ANSI colour codes."""
    RESET = _ansi("\033[0m")
    BOLD = _ansi("\033[1m")
    DIM = _ansi("\033[2m")
    RED = _ansi("\033[91m")
    GREEN = _ansi("\033[92m")
    YELLOW = _ansi("\033[93m")
    BLUE = _ansi("\033[94m")
    MAGENTA = _ansi("\033[95m")
    CYAN = _ansi("\033[96m")
    WHITE = _ansi("\033[97m")
    BG_RED = _ansi("\033[41m")
    BG_GREEN = _ansi("\033[42m")
    BG_YELLOW = _ansi("\033[43m")
    BG_BLUE = _ansi("\033[44m")


_SEVERITY_COLORS = {
    "critical": _C.BG_RED + _C.WHITE,
    "high": _C.RED,
    "medium": _C.YELLOW,
    "low": _C.BLUE,
    "info": _C.DIM,
}

_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}

_GRADE_COLORS = {
    "A": _C.GREEN,
    "B": _C.GREEN,
    "C": _C.YELLOW,
    "D": _C.RED,
    "F": _C.BG_RED + _C.WHITE,
}

# ---------------------------------------------------------------------------
# Lightweight local scanner (self-contained — no import of backend modules)
# ---------------------------------------------------------------------------

# AI package patterns for dependency file scanning
_AI_PACKAGES_PYTHON = {
    "openai", "anthropic", "langchain", "langchain-core", "langchain-openai",
    "langchain-anthropic", "langchain-community", "langgraph", "llama-index",
    "llamaindex", "chromadb", "pinecone-client", "faiss-cpu", "faiss-gpu",
    "qdrant-client", "weaviate-client", "pymilvus", "crewai", "autogen",
    "dspy-ai", "haystack-ai", "transformers", "torch", "tensorflow",
    "keras", "huggingface-hub", "sentence-transformers", "tiktoken",
    "tokenizers", "vllm", "litellm", "guidance", "instructor", "mcp",
    "google-generativeai", "cohere", "replicate", "together", "groq",
    "mistralai", "ollama", "mlflow", "wandb", "bentoml",
}

_AI_PACKAGES_JS = {
    "openai", "@anthropic-ai/sdk", "langchain", "@langchain/core",
    "@langchain/openai", "@langchain/anthropic", "@langchain/community",
    "llamaindex", "ai", "@ai-sdk/openai", "@ai-sdk/anthropic",
    "@modelcontextprotocol/sdk", "ollama-ai-provider", "chromadb",
    "@pinecone-database/pinecone", "cohere-ai", "@google/generative-ai",
    "replicate", "together-ai", "@huggingface/inference",
}

# Import patterns (regex)
_PYTHON_IMPORT_RE = re.compile(
    r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))", re.MULTILINE
)
_JS_IMPORT_RE = re.compile(
    r"""(?:import\s+.*?\s+from\s+['"]([^'"]+)['"]|require\s*\(\s*['"]([^'"]+)['"]\s*\))""",
    re.MULTILINE,
)

# API call patterns
_API_CALL_PATTERNS = [
    (r"client\.chat\.completions\.create", "LLM API Call", "llm_provider", "medium"),
    (r"client\.messages\.create", "LLM API Call", "llm_provider", "medium"),
    (r"client\.completions\.create", "LLM API Call", "llm_provider", "medium"),
    (r"client\.embeddings\.create", "Embedding API Call", "embedding_service", "low"),
    (r"openai\.ChatCompletion\.create", "LLM API Call (legacy)", "llm_provider", "medium"),
    (r"generateText\s*\(", "AI SDK generateText", "llm_provider", "medium"),
    (r"streamText\s*\(", "AI SDK streamText", "llm_provider", "medium"),
    (r"new\s+OpenAI\s*\(", "OpenAI client init", "llm_provider", "low"),
    (r"ChatOpenAI\s*\(", "LangChain ChatOpenAI", "orchestration_framework", "medium"),
    (r"ChatAnthropic\s*\(", "LangChain ChatAnthropic", "orchestration_framework", "medium"),
    (r"RetrievalQA", "LangChain RetrievalQA", "orchestration_framework", "medium"),
    (r"Agent\s*\(", "Agent instantiation", "agent_tool", "high"),
    (r"Crew\s*\(", "CrewAI Crew", "agent_tool", "high"),
]

# Risk patterns (OWASP-mapped)
_RISK_PATTERNS = [
    (r"""f['"](.*?\{.*?(user|input|query|prompt|message).*?\}.*?)['"]""",
     "Potential prompt injection — user input in f-string prompt", "LLM01", "high"),
    (r"""\.format\s*\(.*?(user|input|query|prompt)""",
     "Potential prompt injection — .format() with user input", "LLM01", "high"),
    (r"""eval\s*\(.*?(response|result|output|completion|llm|chat)""",
     "Unsafe eval() of LLM output", "LLM05", "critical"),
    (r"""exec\s*\(.*?(response|result|output|completion|llm|chat)""",
     "Unsafe exec() of LLM output", "LLM05", "critical"),
    (r"""subprocess.*?(response|result|output|completion|llm)""",
     "LLM output passed to subprocess", "LLM05", "critical"),
    (r"""tools\s*=\s*\[""",
     "Agent with tool access — verify least-privilege", "LLM06", "medium"),
    (r"""(OPENAI_API_KEY|ANTHROPIC_API_KEY|GOOGLE_API_KEY)\s*=\s*['"][^'"]{8,}""",
     "Hardcoded API key detected", "LLM02", "critical"),
]

# Model name patterns
_MODEL_NAMES_RE = re.compile(
    r"""(?:['"])(gpt-4o(?:-mini)?|gpt-4-turbo|gpt-3\.5-turbo|o[134]-(?:mini|pro)|"""
    r"""claude-(?:sonnet|opus|haiku)-[\w.-]+|claude-[\d.]+-[\w]+|"""
    r"""llama-?[23][\w.-]*|mistral[\w.-]*|gemini[\w.-]*|"""
    r"""command-r[\w.-]*|text-embedding[\w.-]*)(?:['"])""",
    re.IGNORECASE,
)

# Env var patterns for secrets
_SECRET_ENV_PATTERNS = [
    (r"""(OPENAI_API_KEY|ANTHROPIC_API_KEY|GOOGLE_API_KEY|PINECONE_API_KEY|"""
     r"""HF_TOKEN|HUGGINGFACE_TOKEN|LANGCHAIN_API_KEY|COHERE_API_KEY|"""
     r"""REPLICATE_API_TOKEN|TOGETHER_API_KEY|GROQ_API_KEY|MISTRAL_API_KEY|"""
     r"""AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY|AZURE_OPENAI_API_KEY|"""
     r"""AZURE_OPENAI_ENDPOINT)\s*=\s*['"]?([^'"\s]{8,})""",
     "Exposed API key / secret", "LLM02", "critical"),
]

# File extensions to scan
_SCAN_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs",
}
_CONFIG_EXTENSIONS = {
    ".yaml", ".yml", ".json", ".toml", ".env",
}
_DEP_FILES = {
    "requirements.txt", "pyproject.toml", "Pipfile", "Pipfile.lock",
    "setup.cfg", "setup.py", "poetry.lock",
    "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
}
_NOTEBOOK_EXT = {".ipynb"}

# Directories to skip (unless --full-scan)
_SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv", "env",
    ".tox", ".mypy_cache", ".pytest_cache", "dist", "build",
    ".next", ".nuxt", "coverage",
}
_SKIP_DIRS_FULL = {
    "node_modules", ".git", "__pycache__",
}


def _walk_files(root: Path, full_scan: bool) -> list[Path]:
    """Walk the directory tree and collect scannable files."""
    skip = _SKIP_DIRS_FULL if full_scan else _SKIP_DIRS
    files: list[Path] = []

    for dirpath, dirnames, filenames in os.walk(root):
        # Prune skipped directories
        dirnames[:] = [d for d in dirnames if d not in skip]
        for fname in filenames:
            fp = Path(dirpath) / fname
            suffix = fp.suffix.lower()
            if suffix in _SCAN_EXTENSIONS | _CONFIG_EXTENSIONS | _NOTEBOOK_EXT:
                files.append(fp)
            elif fname in _DEP_FILES:
                files.append(fp)
            elif fname.startswith(".env"):
                files.append(fp)
    return files


def _scan_file(
    file_path: Path,
    root: Path,
) -> list[dict[str, Any]]:
    """Scan a single file and return findings."""
    findings: list[dict[str, Any]] = []
    rel = str(file_path.relative_to(root))
    suffix = file_path.suffix.lower()
    name = file_path.name

    try:
        # Size guard
        if file_path.stat().st_size > 2_000_000:  # 2 MB
            return findings

        if suffix == ".ipynb":
            return _scan_notebook(file_path, root)

        content = file_path.read_text(errors="ignore")
        lines = content.split("\n")
    except (OSError, UnicodeDecodeError):
        return findings

    # --- Dependency files ---
    if name in _DEP_FILES:
        findings.extend(_scan_dependency_file(name, content, rel))
        return findings

    # --- Env files ---
    if name.startswith(".env"):
        findings.extend(_scan_env_file(content, rel))
        return findings

    # --- Source code ---
    if suffix in _SCAN_EXTENSIONS:
        is_python = suffix == ".py"

        # Imports
        if is_python:
            for m in _PYTHON_IMPORT_RE.finditer(content):
                module = m.group(1) or m.group(2)
                pkg = module.split(".")[0]
                if pkg in _AI_PACKAGES_PYTHON or module in _AI_PACKAGES_PYTHON:
                    line_no = content[: m.start()].count("\n") + 1
                    findings.append({
                        "file": rel, "line": line_no,
                        "component": pkg, "type": "ai_package",
                        "severity": "info", "owasp": "",
                        "message": f"AI package import: {module}",
                    })
        else:
            for m in _JS_IMPORT_RE.finditer(content):
                module = m.group(1) or m.group(2)
                if module in _AI_PACKAGES_JS:
                    line_no = content[: m.start()].count("\n") + 1
                    findings.append({
                        "file": rel, "line": line_no,
                        "component": module, "type": "ai_package",
                        "severity": "info", "owasp": "",
                        "message": f"AI package import: {module}",
                    })

        # API call patterns
        for pattern, desc, comp_type, severity in _API_CALL_PATTERNS:
            for m in re.finditer(pattern, content):
                line_no = content[: m.start()].count("\n") + 1
                findings.append({
                    "file": rel, "line": line_no,
                    "component": desc, "type": comp_type,
                    "severity": severity, "owasp": "",
                    "message": f"{desc}: {m.group(0)[:60]}",
                })

        # Risk patterns (OWASP)
        for pattern, desc, owasp, severity in _RISK_PATTERNS:
            for m in re.finditer(pattern, content):
                line_no = content[: m.start()].count("\n") + 1
                findings.append({
                    "file": rel, "line": line_no,
                    "component": owasp, "type": "risk",
                    "severity": severity, "owasp": owasp,
                    "message": desc,
                })

        # Model name references
        for m in _MODEL_NAMES_RE.finditer(content):
            line_no = content[: m.start()].count("\n") + 1
            model_name = m.group(1)
            findings.append({
                "file": rel, "line": line_no,
                "component": model_name, "type": "llm_provider",
                "severity": "info", "owasp": "",
                "message": f"Model reference: {model_name}",
            })

    # --- Config files ---
    if suffix in _CONFIG_EXTENSIONS:
        findings.extend(_scan_config_file(content, rel))

    return findings


def _scan_dependency_file(
    name: str,
    content: str,
    rel: str,
) -> list[dict[str, Any]]:
    """Scan dependency manifest files."""
    findings: list[dict[str, Any]] = []

    if name in ("requirements.txt", "setup.cfg"):
        for i, line in enumerate(content.split("\n"), 1):
            pkg = re.split(r"[>=<!\[;#]", line.strip())[0].strip().lower()
            if pkg in _AI_PACKAGES_PYTHON:
                findings.append({
                    "file": rel, "line": i,
                    "component": pkg, "type": "ai_package",
                    "severity": "info", "owasp": "LLM03",
                    "message": f"AI dependency declared: {line.strip()[:80]}",
                })

    elif name == "package.json":
        try:
            pkg_data = json.loads(content)
            all_deps = {}
            all_deps.update(pkg_data.get("dependencies", {}))
            all_deps.update(pkg_data.get("devDependencies", {}))
            for dep_name, version in all_deps.items():
                if dep_name in _AI_PACKAGES_JS:
                    findings.append({
                        "file": rel, "line": 0,
                        "component": dep_name, "type": "ai_package",
                        "severity": "info", "owasp": "LLM03",
                        "message": f"AI dependency: {dep_name}@{version}",
                    })
        except json.JSONDecodeError:
            pass

    elif name in ("pyproject.toml", "Pipfile"):
        # Simple regex scan for TOML-based files
        for i, line in enumerate(content.split("\n"), 1):
            for pkg in _AI_PACKAGES_PYTHON:
                if pkg in line.lower():
                    findings.append({
                        "file": rel, "line": i,
                        "component": pkg, "type": "ai_package",
                        "severity": "info", "owasp": "LLM03",
                        "message": f"AI dependency declared: {line.strip()[:80]}",
                    })

    return findings


def _scan_env_file(content: str, rel: str) -> list[dict[str, Any]]:
    """Scan .env files for AI-related secrets."""
    findings: list[dict[str, Any]] = []
    for pattern, desc, owasp, severity in _SECRET_ENV_PATTERNS:
        for m in re.finditer(pattern, content):
            line_no = content[: m.start()].count("\n") + 1
            key_name = m.group(1)
            findings.append({
                "file": rel, "line": line_no,
                "component": key_name, "type": "secret",
                "severity": severity, "owasp": owasp,
                "message": f"{desc}: {key_name}",
            })
    return findings


def _scan_config_file(content: str, rel: str) -> list[dict[str, Any]]:
    """Scan config files for model references, endpoints, etc."""
    findings: list[dict[str, Any]] = []

    # Model names
    for m in _MODEL_NAMES_RE.finditer(content):
        line_no = content[: m.start()].count("\n") + 1
        findings.append({
            "file": rel, "line": line_no,
            "component": m.group(1), "type": "config_reference",
            "severity": "info", "owasp": "",
            "message": f"Model reference in config: {m.group(1)}",
        })

    # API endpoints
    endpoint_re = re.compile(
        r"""(api\.openai\.com|api\.anthropic\.com|generativelanguage\.googleapis\.com|"""
        r"""api\.cohere\.ai|api\.together\.xyz|api\.groq\.com|api\.mistral\.ai|"""
        r"""api\.replicate\.com)""",
        re.IGNORECASE,
    )
    for m in endpoint_re.finditer(content):
        line_no = content[: m.start()].count("\n") + 1
        findings.append({
            "file": rel, "line": line_no,
            "component": m.group(1), "type": "config_reference",
            "severity": "low", "owasp": "",
            "message": f"AI API endpoint in config: {m.group(1)}",
        })

    return findings


def _scan_notebook(file_path: Path, root: Path) -> list[dict[str, Any]]:
    """Extract code cells from .ipynb and scan them."""
    rel = str(file_path.relative_to(root))
    findings: list[dict[str, Any]] = []

    try:
        nb = json.loads(file_path.read_text(errors="ignore"))
    except (json.JSONDecodeError, OSError):
        return findings

    cells = nb.get("cells", [])
    cell_offset = 0
    for cell in cells:
        if cell.get("cell_type") != "code":
            source_lines = cell.get("source", [])
            cell_offset += len(source_lines) if isinstance(source_lines, list) else source_lines.count("\n") + 1
            continue

        source = cell.get("source", [])
        if isinstance(source, list):
            code = "".join(source)
            num_lines = len(source)
        else:
            code = source
            num_lines = code.count("\n") + 1

        # Scan as Python
        for m in _PYTHON_IMPORT_RE.finditer(code):
            module = m.group(1) or m.group(2)
            pkg = module.split(".")[0]
            if pkg in _AI_PACKAGES_PYTHON:
                line_no = cell_offset + code[: m.start()].count("\n") + 1
                findings.append({
                    "file": rel, "line": line_no,
                    "component": pkg, "type": "ai_package",
                    "severity": "info", "owasp": "",
                    "message": f"AI import in notebook: {module}",
                })

        for pattern, desc, comp_type, severity in _API_CALL_PATTERNS:
            for m in re.finditer(pattern, code):
                line_no = cell_offset + code[: m.start()].count("\n") + 1
                findings.append({
                    "file": rel, "line": line_no,
                    "component": desc, "type": comp_type,
                    "severity": severity, "owasp": "",
                    "message": f"{desc} in notebook",
                })

        for pattern, desc, owasp, severity in _RISK_PATTERNS:
            for m in re.finditer(pattern, code):
                line_no = cell_offset + code[: m.start()].count("\n") + 1
                findings.append({
                    "file": rel, "line": line_no,
                    "component": owasp, "type": "risk",
                    "severity": severity, "owasp": owasp,
                    "message": desc,
                })

        cell_offset += num_lines

    return findings


# ---------------------------------------------------------------------------
# Risk scoring (standalone)
# ---------------------------------------------------------------------------


def _compute_risk_score(findings: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute a simplified risk score from findings."""
    secrets = sum(1 for f in findings if f["type"] == "secret")
    owasp_critical = sum(1 for f in findings if f.get("owasp") and f["severity"] == "critical")
    owasp_high = sum(1 for f in findings if f.get("owasp") and f["severity"] == "high")

    # Provider concentration
    providers = {f["component"] for f in findings if f["type"] == "llm_provider"}
    concentration = 10 if len(providers) == 1 and providers else 0

    # Missing safety
    has_max_tokens = any("max_tokens" in f.get("message", "") for f in findings)
    missing_safety = 0 if has_max_tokens else 3

    raw = (
        secrets * 25
        + owasp_critical * 20
        + owasp_high * 10
        + concentration
        + missing_safety
    )
    max_possible = max(raw, 100)
    overall = min(100, int(raw / max_possible * 100)) if max_possible > 0 else 0

    if overall < 20:
        grade = "A"
    elif overall < 40:
        grade = "B"
    elif overall < 60:
        grade = "C"
    elif overall < 80:
        grade = "D"
    else:
        grade = "F"

    return {
        "overall_score": overall,
        "grade": grade,
        "breakdown": {
            "secrets_found": {"label": "Hardcoded Secrets", "score": secrets * 25, "count": secrets},
            "owasp_critical": {"label": "OWASP Critical", "score": owasp_critical * 20, "count": owasp_critical},
            "owasp_high": {"label": "OWASP High", "score": owasp_high * 10, "count": owasp_high},
            "provider_concentration": {"label": "Provider Concentration", "score": concentration},
            "missing_safety": {"label": "Missing Safety Configs", "score": missing_safety},
        },
        "max_possible_score": max_possible,
    }


def _compute_owasp(findings: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute OWASP LLM Top 10 coverage."""
    categories: dict[str, dict[str, Any]] = {}
    for f in findings:
        owasp = f.get("owasp", "")
        if not owasp:
            continue
        if owasp not in categories:
            categories[owasp] = {"count": 0, "max_severity": "info"}
        categories[owasp]["count"] += 1
        if _SEVERITY_ORDER.get(f["severity"], 4) < _SEVERITY_ORDER.get(categories[owasp]["max_severity"], 4):
            categories[owasp]["max_severity"] = f["severity"]
    return {"categories": categories}


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------


def _format_table(
    findings: list[dict[str, Any]],
    risk_score: dict[str, Any],
    owasp: dict[str, Any],
) -> str:
    """Format findings as a coloured ASCII table."""
    lines: list[str] = []

    # Header banner
    lines.append("")
    lines.append(f"{_C.BOLD}{_C.CYAN}  ScanLLM — AI Dependency Intelligence Scanner{_C.RESET}")
    lines.append(f"{_C.DIM}  {'─' * 60}{_C.RESET}")
    lines.append("")

    if not findings:
        lines.append(f"  {_C.GREEN}No AI/LLM dependencies found.{_C.RESET}")
        lines.append("")
        return "\n".join(lines)

    # Column widths
    w_file = 35
    w_line = 5
    w_comp = 20
    w_type = 16
    w_sev = 10
    w_owasp = 6

    # Table header
    header = (
        f"  {_C.BOLD}"
        f"{'FILE':<{w_file}} "
        f"{'LINE':>{w_line}} "
        f"{'COMPONENT':<{w_comp}} "
        f"{'TYPE':<{w_type}} "
        f"{'SEVERITY':<{w_sev}} "
        f"{'OWASP':<{w_owasp}}"
        f"{_C.RESET}"
    )
    lines.append(header)
    lines.append(f"  {'─' * (w_file + w_line + w_comp + w_type + w_sev + w_owasp + 5)}")

    for f in findings:
        sev = f["severity"]
        sev_color = _SEVERITY_COLORS.get(sev, "")
        owasp_str = f.get("owasp", "") or ""

        file_str = f["file"]
        if len(file_str) > w_file:
            file_str = "..." + file_str[-(w_file - 3):]

        comp_str = f["component"][:w_comp]
        type_str = f["type"].replace("_", " ").title()[:w_type]

        row = (
            f"  {file_str:<{w_file}} "
            f"{str(f['line']):>{w_line}} "
            f"{comp_str:<{w_comp}} "
            f"{type_str:<{w_type}} "
            f"{sev_color}{sev.upper():<{w_sev}}{_C.RESET} "
            f"{_C.MAGENTA}{owasp_str:<{w_owasp}}{_C.RESET}"
        )
        lines.append(row)

    # Summary
    lines.append("")
    lines.append(f"  {'─' * 60}")

    overall = risk_score["overall_score"]
    grade = risk_score["grade"]
    grade_c = _GRADE_COLORS.get(grade, "")

    lines.append(
        f"  {_C.BOLD}Risk Score:{_C.RESET} {overall}/100  "
        f"{grade_c}{_C.BOLD}Grade: {grade}{_C.RESET}"
    )
    lines.append(f"  {_C.BOLD}Total Findings:{_C.RESET} {len(findings)}")

    # Severity breakdown
    sev_counts: dict[str, int] = {}
    for f in findings:
        sev_counts[f["severity"]] = sev_counts.get(f["severity"], 0) + 1
    sev_parts = []
    for sev in ("critical", "high", "medium", "low", "info"):
        count = sev_counts.get(sev, 0)
        if count > 0:
            sev_parts.append(f"{_SEVERITY_COLORS.get(sev, '')}{count} {sev}{_C.RESET}")
    if sev_parts:
        lines.append(f"  {_C.BOLD}By Severity:{_C.RESET} {' | '.join(sev_parts)}")

    # OWASP coverage
    owasp_cats = owasp.get("categories", {})
    if owasp_cats:
        owasp_ids = sorted(owasp_cats.keys())
        lines.append(f"  {_C.BOLD}OWASP LLM Top 10:{_C.RESET} {', '.join(owasp_ids)}")

    lines.append("")
    return "\n".join(lines)


def _format_json(
    findings: list[dict[str, Any]],
    risk_score: dict[str, Any],
    owasp: dict[str, Any],
    scan_meta: dict[str, Any],
) -> str:
    """Format output as JSON."""
    output = {
        "scan": scan_meta,
        "risk_score": risk_score,
        "owasp": owasp,
        "total_findings": len(findings),
        "findings": findings,
    }
    return json.dumps(output, indent=2)


def _format_cyclonedx(
    findings: list[dict[str, Any]],
    scan_meta: dict[str, Any],
) -> str:
    """Format output as CycloneDX AI-BOM JSON."""
    # Try to use the full generator if available
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
        from app.reports.aibom_generator import AIBOMGenerator

        gen = AIBOMGenerator()
        scan_data = {
            "repo_name": scan_meta.get("target", "unknown"),
            "components": [],
            "findings": findings,
        }
        bom = gen.generate(scan_data, findings)
        return json.dumps(bom, indent=2)
    except ImportError:
        pass

    # Fallback: minimal CycloneDX output
    import uuid as _uuid
    from datetime import datetime as _dt, timezone as _tz

    components = []
    seen: set[str] = set()
    for f in findings:
        name = f.get("component", "")
        if not name or name in seen or f["type"] in ("risk", "secret"):
            continue
        seen.add(name)
        components.append({
            "type": "library",
            "name": name,
            "bom-ref": name,
            "properties": [
                {"name": "scanllm:category", "value": f["type"]},
                {"name": "scanllm:severity", "value": f["severity"]},
            ],
        })

    bom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "serialNumber": f"urn:uuid:{_uuid.uuid4()}",
        "version": 1,
        "metadata": {
            "timestamp": _dt.now(_tz.utc).isoformat(),
            "tools": {"components": [{"type": "application", "name": "ScanLLM", "version": "1.0.0"}]},
        },
        "components": components,
        "dependencies": [],
    }
    return json.dumps(bom, indent=2)


# ---------------------------------------------------------------------------
# Main scan orchestration
# ---------------------------------------------------------------------------


def _run_scan(
    target: str,
    output_format: str = "table",
    full_scan: bool = False,
    severity_filter: str = "info",
) -> int:
    """Execute a scan and print results. Returns exit code."""
    target_path = Path(target).resolve()

    # Check if target is a URL
    if target.startswith("http://") or target.startswith("https://"):
        return _run_remote_scan(target, output_format, severity_filter)

    if not target_path.exists():
        print(f"{_C.RED}Error: Path does not exist: {target_path}{_C.RESET}", file=sys.stderr)
        return 1

    if not target_path.is_dir():
        print(f"{_C.RED}Error: Path is not a directory: {target_path}{_C.RESET}", file=sys.stderr)
        return 1

    if output_format == "table":
        print(f"\n{_C.DIM}  Scanning {target_path} ...{_C.RESET}", file=sys.stderr)

    start = time.monotonic()

    # Collect files
    files = _walk_files(target_path, full_scan)

    if output_format == "table":
        print(f"{_C.DIM}  Found {len(files)} file(s) to scan{_C.RESET}", file=sys.stderr)

    # Scan
    all_findings: list[dict[str, Any]] = []
    for fp in files:
        all_findings.extend(_scan_file(fp, target_path))

    elapsed = time.monotonic() - start

    # Filter by severity
    min_sev = _SEVERITY_ORDER.get(severity_filter, 4)
    filtered = [f for f in all_findings if _SEVERITY_ORDER.get(f["severity"], 4) <= min_sev]

    # Sort: severity desc, then file, then line
    filtered.sort(key=lambda f: (_SEVERITY_ORDER.get(f["severity"], 4), f["file"], f["line"]))

    # Compute scores
    risk_score = _compute_risk_score(all_findings)
    owasp = _compute_owasp(all_findings)

    scan_meta = {
        "target": str(target_path),
        "files_scanned": len(files),
        "scan_time_seconds": round(elapsed, 2),
        "full_scan": full_scan,
        "severity_filter": severity_filter,
    }

    # Output
    if output_format == "table":
        print(_format_table(filtered, risk_score, owasp))
        print(f"{_C.DIM}  Scanned {len(files)} files in {elapsed:.2f}s{_C.RESET}")
        print("")
    elif output_format == "json":
        print(_format_json(filtered, risk_score, owasp, scan_meta))
    elif output_format == "cyclonedx":
        print(_format_cyclonedx(filtered, scan_meta))
    else:
        print(f"{_C.RED}Unknown output format: {output_format}{_C.RESET}", file=sys.stderr)
        return 1

    return 0


def _run_remote_scan(url: str, output_format: str, severity_filter: str) -> int:
    """Clone a remote repo into a temp directory and scan it."""
    try:
        import subprocess
    except ImportError:
        print(f"{_C.RED}Error: subprocess module not available{_C.RESET}", file=sys.stderr)
        return 1

    if output_format == "table":
        print(f"\n{_C.DIM}  Cloning {url} ...{_C.RESET}", file=sys.stderr)

    with tempfile.TemporaryDirectory(prefix="scanllm_") as tmpdir:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", url, tmpdir],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            print(f"{_C.RED}Error cloning repository:{_C.RESET}", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            return 1

        return _run_scan(
            tmpdir,
            output_format=output_format,
            full_scan=False,
            severity_filter=severity_filter,
        )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="scanllm",
        description="ScanLLM — AI Dependency Intelligence Scanner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  scanllm scan .                        Scan current directory\n"
            "  scanllm scan ./src --output json       JSON output\n"
            "  scanllm scan . --output cyclonedx      CycloneDX AI-BOM\n"
            "  scanllm scan . --severity high         Show high+ findings only\n"
            "  scanllm scan https://github.com/o/r    Scan remote repo\n"
        ),
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # scan command
    scan_parser = subparsers.add_parser(
        "scan",
        help="Scan a repository or local directory for AI/LLM dependencies",
    )
    scan_parser.add_argument(
        "target",
        help="Repository URL or local directory path to scan",
    )
    scan_parser.add_argument(
        "--output",
        choices=["table", "json", "cyclonedx"],
        default="table",
        help="Output format (default: table)",
    )
    scan_parser.add_argument(
        "--full-scan",
        action="store_true",
        default=False,
        help="Include test and documentation directories in scan",
    )
    scan_parser.add_argument(
        "--severity",
        choices=["critical", "high", "medium", "low", "info"],
        default="info",
        help="Minimum severity level to display (default: info — show all)",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "scan":
        return _run_scan(
            target=args.target,
            output_format=args.output,
            full_scan=args.full_scan,
            severity_filter=args.severity,
        )

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
