"""
Regex-based JavaScript/TypeScript scanner for detecting AI/LLM dependencies,
usage patterns, and security risks in JS/TS source files.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Compiled regex patterns ──────────────────────────────────────────────────

# Import patterns: ES module imports
_RE_IMPORT_FROM = re.compile(
    r"""import\s+(?:[\w{},\s*]+)\s+from\s+['"]([^'"]+)['"]""",
    re.MULTILINE,
)
# Import patterns: require()
_RE_REQUIRE = re.compile(
    r"""(?:const|let|var)\s+[\w{},\s]+\s*=\s*require\(\s*['"]([^'"]+)['"]\s*\)""",
    re.MULTILINE,
)
# Dynamic import()
_RE_DYNAMIC_IMPORT = re.compile(
    r"""import\(\s*['"]([^'"]+)['"]\s*\)""",
    re.MULTILINE,
)

# Constructor / factory calls
_RE_NEW_CALL = re.compile(
    r"""new\s+(OpenAI|Anthropic|GoogleGenerativeAI|Groq|Mistral|McpServer|Pinecone|QdrantClient|ChromaClient)\s*\(""",
    re.MULTILINE,
)

# Function calls
_RE_FUNC_CALL = re.compile(
    r"""\b(generateText|streamText|generateObject|streamObject|embed|embedMany)\s*\(""",
    re.MULTILINE,
)

# model: "..." in object literals / function args
_RE_MODEL_PARAM = re.compile(
    r"""model\s*:\s*['"]([^'"]+)['"]""",
    re.MULTILINE,
)

# Template literal prompt injection: `...${userInput}...`
_RE_TEMPLATE_INJECTION = re.compile(
    r"""`[^`]*\$\{[^}]*(user[_]?input|request|query|message|prompt|body|payload|req\.body|req\.query|req\.params)[^}]*\}[^`]*`""",
    re.IGNORECASE | re.MULTILINE,
)

# MCP server.tool() / server.resource() calls
_RE_MCP_SERVER_CALL = re.compile(
    r"""server\.(tool|resource)\s*\(""",
    re.MULTILINE,
)


def _make_finding(
    *,
    file_path: str,
    line_number: int,
    line_text: str = "",
    framework: str = "",
    pattern_name: str = "",
    pattern_category: str = "",
    pattern_severity: str = "info",
    pattern_description: str = "",
    snippet: str = "",
    model_name: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    is_streaming: bool = False,
    has_tools: bool = False,
    component_type: str = "",
    provider: str = "",
    owasp_id: str | None = None,
) -> dict[str, Any]:
    return {
        "file_path": file_path,
        "line_number": line_number,
        "line_text": line_text,
        "framework": framework,
        "pattern_name": pattern_name,
        "pattern_category": pattern_category,
        "pattern_severity": pattern_severity,
        "pattern_description": pattern_description,
        "snippet": snippet,
        "model_name": model_name,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "is_streaming": is_streaming,
        "has_tools": has_tools,
        "component_type": component_type,
        "provider": provider,
        "owasp_id": owasp_id,
    }


def _get_snippet(lines: list[str], lineno: int, context: int = 2) -> str:
    start = max(0, lineno - 1 - context)
    end = min(len(lines), lineno + context)
    return "\n".join(lines[start:end])


class _JSSignatureIndex:
    """Pre-processed lookup tables built from the raw signatures dict for JS/TS."""

    def __init__(self, signatures: dict[str, Any]) -> None:
        # JS import string fragment -> (provider_key, category, display_name)
        self.import_map: dict[str, tuple[str, str, str]] = {}
        # JS call pattern -> (provider_key, category, display_name)
        self.call_map: dict[str, tuple[str, str, str]] = {}
        # model name -> provider_key
        self.model_map: dict[str, str] = {}
        self.model_names: set[str] = set()

        for section_key in ("providers", "vector_databases", "frameworks",
                            "agents", "inference", "mcp"):
            section = signatures.get(section_key, {})
            if not isinstance(section, dict):
                continue
            for provider_key, info in section.items():
                if not isinstance(info, dict):
                    continue
                category = info.get("category", section_key)
                display_name = info.get("display_name", provider_key)
                js = info.get("javascript", {})
                if isinstance(js, dict):
                    for imp in js.get("imports", []):
                        # Normalise: strip from/require wrappers, keep the package spec
                        clean = self._clean_import_sig(imp)
                        if clean:
                            self.import_map[clean] = (provider_key, category, display_name)
                    for call in js.get("calls", []):
                        self.call_map[call.rstrip("(")] = (provider_key, category, display_name)
                # Also collect models from python section (they are language-agnostic)
                py = info.get("python", {})
                if isinstance(py, dict):
                    for model in py.get("models", []):
                        self.model_names.add(model.lower())
                        self.model_map[model.lower()] = provider_key

    @staticmethod
    def _clean_import_sig(sig: str) -> str:
        """Extract bare package specifier from signature strings like `from 'openai'`."""
        # Handles: from 'pkg', from "pkg", require('pkg'), require("pkg")
        m = re.search(r"""['"]([^'"]+)['"]""", sig)
        return m.group(1) if m else sig.strip()


class JSScanner:
    """Scan a single JS/TS file using regex-based analysis."""

    def scan_file(
        self,
        file_path: Path,
        relative_path: str,
        signatures: dict[str, Any],
    ) -> list[dict[str, Any]]:
        try:
            source = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            logger.warning("Failed to read %s: %s", file_path, exc)
            return []

        lines = source.splitlines()
        idx = _JSSignatureIndex(signatures)
        findings: list[dict[str, Any]] = []

        self._scan_imports(lines, relative_path, idx, findings)
        self._scan_calls(lines, relative_path, idx, findings)
        self._scan_model_params(lines, relative_path, idx, findings)
        self._scan_template_injection(lines, relative_path, findings)
        self._scan_mcp_calls(lines, relative_path, findings)

        return findings

    # ── Import scanning ──────────────────────────────────────────────

    def _scan_imports(
        self,
        lines: list[str],
        relative_path: str,
        idx: _JSSignatureIndex,
        findings: list[dict[str, Any]],
    ) -> None:
        for i, line in enumerate(lines, start=1):
            # ES module imports
            for m in _RE_IMPORT_FROM.finditer(line):
                pkg = m.group(1)
                self._match_import(pkg, i, line, lines, relative_path, idx, findings)
            # require() imports
            for m in _RE_REQUIRE.finditer(line):
                pkg = m.group(1)
                self._match_import(pkg, i, line, lines, relative_path, idx, findings)
            # Dynamic imports
            for m in _RE_DYNAMIC_IMPORT.finditer(line):
                pkg = m.group(1)
                self._match_import(pkg, i, line, lines, relative_path, idx, findings)

    def _match_import(
        self,
        pkg: str,
        lineno: int,
        line_text: str,
        lines: list[str],
        relative_path: str,
        idx: _JSSignatureIndex,
        findings: list[dict[str, Any]],
    ) -> None:
        for sig_pkg, (prov, cat, display) in idx.import_map.items():
            if pkg == sig_pkg or pkg.startswith(sig_pkg + "/"):
                findings.append(_make_finding(
                    file_path=relative_path,
                    line_number=lineno,
                    line_text=line_text.rstrip(),
                    framework=display,
                    pattern_name=f"import:{pkg}",
                    pattern_category="import",
                    pattern_severity="info",
                    pattern_description=f"Import of {display} package '{pkg}' detected",
                    snippet=_get_snippet(lines, lineno),
                    component_type=cat,
                    provider=prov,
                ))
                return

    # ── Constructor / function call scanning ─────────────────────────

    def _scan_calls(
        self,
        lines: list[str],
        relative_path: str,
        idx: _JSSignatureIndex,
        findings: list[dict[str, Any]],
    ) -> None:
        for i, line in enumerate(lines, start=1):
            # new Foo(...) calls
            for m in _RE_NEW_CALL.finditer(line):
                call_name = f"new {m.group(1)}"
                for sig_call, (prov, cat, display) in idx.call_map.items():
                    if call_name.startswith(sig_call):
                        findings.append(_make_finding(
                            file_path=relative_path,
                            line_number=i,
                            line_text=line.rstrip(),
                            framework=display,
                            pattern_name=f"call:{call_name}",
                            pattern_category="api_call",
                            pattern_severity="info",
                            pattern_description=f"Instantiation of {display} client detected",
                            snippet=_get_snippet(lines, i),
                            component_type=cat,
                            provider=prov,
                        ))
                        break

            # Function calls (generateText, streamText, etc.)
            for m in _RE_FUNC_CALL.finditer(line):
                func_name = m.group(1)
                for sig_call, (prov, cat, display) in idx.call_map.items():
                    if func_name == sig_call.rstrip("("):
                        is_streaming = "stream" in func_name.lower()
                        findings.append(_make_finding(
                            file_path=relative_path,
                            line_number=i,
                            line_text=line.rstrip(),
                            framework=display,
                            pattern_name=f"call:{func_name}",
                            pattern_category="api_call",
                            pattern_severity="info",
                            pattern_description=f"Call to {display} function '{func_name}' detected",
                            snippet=_get_snippet(lines, i),
                            is_streaming=is_streaming,
                            component_type=cat,
                            provider=prov,
                        ))
                        break

    # ── Model parameter extraction ───────────────────────────────────

    def _scan_model_params(
        self,
        lines: list[str],
        relative_path: str,
        idx: _JSSignatureIndex,
        findings: list[dict[str, Any]],
    ) -> None:
        for i, line in enumerate(lines, start=1):
            for m in _RE_MODEL_PARAM.finditer(line):
                model_name = m.group(1)
                if model_name.lower() in idx.model_names:
                    provider = idx.model_map.get(model_name.lower(), "")
                    findings.append(_make_finding(
                        file_path=relative_path,
                        line_number=i,
                        line_text=line.rstrip(),
                        framework="",
                        pattern_name=f"model_ref:{model_name}",
                        pattern_category="model_reference",
                        pattern_severity="info",
                        pattern_description=f"Model name '{model_name}' referenced",
                        snippet=_get_snippet(lines, i),
                        model_name=model_name,
                        component_type="llm_provider",
                        provider=provider,
                    ))

    # ── Template literal prompt injection ────────────────────────────

    def _scan_template_injection(
        self,
        lines: list[str],
        relative_path: str,
        findings: list[dict[str, Any]],
    ) -> None:
        for i, line in enumerate(lines, start=1):
            if _RE_TEMPLATE_INJECTION.search(line):
                findings.append(_make_finding(
                    file_path=relative_path,
                    line_number=i,
                    line_text=line.rstrip(),
                    framework="",
                    pattern_name="prompt_injection:template_literal",
                    pattern_category="security",
                    pattern_severity="high",
                    pattern_description=(
                        "User input interpolated into template literal — "
                        "prompt injection risk"
                    ),
                    snippet=_get_snippet(lines, i),
                    component_type="llm_provider",
                    provider="",
                    owasp_id="LLM01",
                ))

    # ── MCP server calls ─────────────────────────────────────────────

    def _scan_mcp_calls(
        self,
        lines: list[str],
        relative_path: str,
        findings: list[dict[str, Any]],
    ) -> None:
        for i, line in enumerate(lines, start=1):
            if _RE_MCP_SERVER_CALL.search(line):
                findings.append(_make_finding(
                    file_path=relative_path,
                    line_number=i,
                    line_text=line.rstrip(),
                    framework="MCP Server",
                    pattern_name="mcp:server_registration",
                    pattern_category="api_call",
                    pattern_severity="info",
                    pattern_description="MCP server tool/resource registration detected",
                    snippet=_get_snippet(lines, i),
                    component_type="mcp_server",
                    provider="mcp_server",
                ))
