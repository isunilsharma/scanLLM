"""
AST-based Python scanner for detecting AI/LLM dependencies, usage patterns,
and security risks in Python source files.
"""

from __future__ import annotations

import ast
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Variables names commonly tied to user-controlled input
_USER_INPUT_VARS = frozenset({
    "user_input", "request", "query", "message", "prompt",
    "user_message", "user_query", "input_text", "question",
    "user_prompt", "body", "payload", "data", "content",
})

# Known LLM output variable fragments
_LLM_OUTPUT_VARS = frozenset({
    "response", "result", "output", "completion", "message",
    "answer", "generated", "reply", "text",
})


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
    """Construct a normalised Finding dict."""
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


def _get_source_line(source_lines: list[str], lineno: int) -> str:
    """Safely retrieve a source line (1-indexed)."""
    if 1 <= lineno <= len(source_lines):
        return source_lines[lineno - 1].rstrip()
    return ""


def _get_snippet(source_lines: list[str], lineno: int, context: int = 2) -> str:
    """Return a few lines of context around *lineno* (1-indexed)."""
    start = max(0, lineno - 1 - context)
    end = min(len(source_lines), lineno + context)
    return "\n".join(source_lines[start:end])


def _dotted_name(node: ast.expr) -> str:
    """Recursively build a dotted name string from an AST node."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _dotted_name(node.value)
        if parent:
            return f"{parent}.{node.attr}"
        return node.attr
    return ""


class _SignatureIndex:
    """Pre-processed lookup tables built from the raw signatures dict."""

    def __init__(self, signatures: dict[str, Any]) -> None:
        # import string -> (provider_key, category, display_name)
        self.import_map: dict[str, tuple[str, str, str]] = {}
        # call pattern fragment -> (provider_key, category, display_name)
        self.call_map: dict[str, tuple[str, str, str]] = {}
        # model name -> provider_key
        self.model_map: dict[str, str] = {}
        # All known model name strings (lowered) for fast membership test
        self.model_names: set[str] = set()
        # Risk patterns from the signatures YAML
        self.risk_patterns: list[dict[str, Any]] = []

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
                py = info.get("python", {})
                if isinstance(py, dict):
                    for imp in py.get("imports", []):
                        self.import_map[imp] = (provider_key, category, display_name)
                    for call in py.get("calls", []):
                        self.call_map[call] = (provider_key, category, display_name)
                    for model in py.get("models", []):
                        self.model_names.add(model.lower())
                        self.model_map[model.lower()] = provider_key
                # Provider-level risk patterns
                for rp in info.get("risk_patterns", []):
                    if isinstance(rp, dict):
                        self.risk_patterns.append({**rp, "_provider": provider_key, "_category": category})

        # Top-level risk_patterns section
        rp_section = signatures.get("risk_patterns", {})
        if isinstance(rp_section, dict):
            for rp_key, rp_val in rp_section.items():
                if isinstance(rp_val, dict):
                    self.risk_patterns.append({**rp_val, "_name": rp_key})


class PythonScanner:
    """Scan a single Python source file using AST analysis."""

    def scan_file(
        self,
        file_path: Path,
        relative_path: str,
        signatures: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Parse *file_path* and return a list of Finding dicts."""
        try:
            source = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            logger.warning("Failed to read %s: %s", file_path, exc)
            return []

        try:
            tree = ast.parse(source, filename=str(file_path))
        except SyntaxError as exc:
            logger.debug("Syntax error in %s: %s", file_path, exc)
            return []

        source_lines = source.splitlines()
        idx = _SignatureIndex(signatures)
        visitor = _ASTVisitor(relative_path, source_lines, idx)
        visitor.visit(tree)
        return visitor.findings

    # Convenience helper used by notebook_scanner to scan already-read source
    def scan_source(
        self,
        source: str,
        relative_path: str,
        signatures: dict[str, Any],
        line_offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Like scan_file but accepts source text directly."""
        try:
            tree = ast.parse(source, filename=relative_path)
        except SyntaxError as exc:
            logger.debug("Syntax error in %s: %s", relative_path, exc)
            return []

        source_lines = source.splitlines()
        idx = _SignatureIndex(signatures)
        visitor = _ASTVisitor(relative_path, source_lines, idx, line_offset=line_offset)
        visitor.visit(tree)
        return visitor.findings


class _ASTVisitor(ast.NodeVisitor):
    """Walk an AST tree and populate *findings*."""

    def __init__(
        self,
        relative_path: str,
        source_lines: list[str],
        idx: _SignatureIndex,
        line_offset: int = 0,
    ) -> None:
        self.relative_path = relative_path
        self.source_lines = source_lines
        self.idx = idx
        self.line_offset = line_offset
        self.findings: list[dict[str, Any]] = []

        # Track variable assignments so we can resolve simple names later
        # e.g. model = "gpt-4o"
        self._assigned_models: dict[str, str] = {}

    # ── helpers ──────────────────────────────────────────────────────

    def _lineno(self, node: ast.AST) -> int:
        return getattr(node, "lineno", 0) + self.line_offset

    def _line_text(self, node: ast.AST) -> str:
        return _get_source_line(self.source_lines, getattr(node, "lineno", 0))

    def _snippet(self, node: ast.AST) -> str:
        return _get_snippet(self.source_lines, getattr(node, "lineno", 0))

    def _add(self, **kwargs: Any) -> None:
        kwargs.setdefault("file_path", self.relative_path)
        self.findings.append(_make_finding(**kwargs))

    # ── Import / ImportFrom ──────────────────────────────────────────

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self._check_import(alias.name, node)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        self._check_import(module, node)
        # Also try "from <module> import" form
        self._check_import(f"from {module} import", node)
        self.generic_visit(node)

    def _check_import(self, import_str: str, node: ast.AST) -> None:
        for sig_import, (prov, cat, display) in self.idx.import_map.items():
            if import_str == sig_import or import_str.startswith(sig_import.rstrip(".")):
                self._add(
                    line_number=self._lineno(node),
                    line_text=self._line_text(node),
                    framework=display,
                    pattern_name=f"import:{sig_import}",
                    pattern_category="import",
                    pattern_severity="info",
                    pattern_description=f"Import of {display} detected",
                    snippet=self._snippet(node),
                    component_type=cat,
                    provider=prov,
                )
                return  # first match wins

    # ── Call nodes ───────────────────────────────────────────────────

    def visit_Call(self, node: ast.Call) -> None:
        call_name = _dotted_name(node.func)
        if call_name:
            self._check_call(call_name, node)
            self._check_prompt_injection_in_call(call_name, node)
            self._check_eval_exec(call_name, node)
            self._check_missing_max_tokens(call_name, node)
            self._check_tools_kwarg(call_name, node)
        self.generic_visit(node)

    def _check_call(self, call_name: str, node: ast.Call) -> None:
        for sig_call, (prov, cat, display) in self.idx.call_map.items():
            # Strip trailing paren in signature for matching
            sig_clean = sig_call.rstrip("()")
            if call_name == sig_clean or call_name.endswith(sig_clean):
                # Extract kwargs of interest
                model_name = self._extract_kwarg_str(node, "model")
                temperature = self._extract_kwarg_num(node, "temperature")
                max_tokens = self._extract_kwarg_int(node, "max_tokens")
                is_streaming = self._extract_kwarg_bool(node, "stream")
                has_tools = self._has_kwarg(node, "tools")

                self._add(
                    line_number=self._lineno(node),
                    line_text=self._line_text(node),
                    framework=display,
                    pattern_name=f"call:{sig_call}",
                    pattern_category="api_call",
                    pattern_severity="info",
                    pattern_description=f"Call to {display} API detected",
                    snippet=self._snippet(node),
                    model_name=model_name,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    is_streaming=is_streaming,
                    has_tools=has_tools,
                    component_type=cat,
                    provider=prov,
                )
                return

    # ── model= keyword argument extraction ───────────────────────────

    def _extract_kwarg_str(self, node: ast.Call, kwarg: str) -> str | None:
        for kw in node.keywords:
            if kw.arg == kwarg:
                if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                    return kw.value.value
                if isinstance(kw.value, ast.Name):
                    return self._assigned_models.get(kw.value.id)
        return None

    def _extract_kwarg_num(self, node: ast.Call, kwarg: str) -> float | None:
        for kw in node.keywords:
            if kw.arg == kwarg:
                if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, (int, float)):
                    return float(kw.value.value)
        return None

    def _extract_kwarg_int(self, node: ast.Call, kwarg: str) -> int | None:
        for kw in node.keywords:
            if kw.arg == kwarg:
                if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, int):
                    return kw.value.value
        return None

    def _extract_kwarg_bool(self, node: ast.Call, kwarg: str) -> bool:
        for kw in node.keywords:
            if kw.arg == kwarg:
                if isinstance(kw.value, ast.Constant):
                    return bool(kw.value.value)
        return False

    def _has_kwarg(self, node: ast.Call, kwarg: str) -> bool:
        return any(kw.arg == kwarg for kw in node.keywords)

    # ── Prompt injection: f-strings / .format() with user input ──────

    def _check_prompt_injection_in_call(self, call_name: str, node: ast.Call) -> None:
        """Flag user-controlled variables inside prompt strings passed to LLM calls."""
        # Only care about calls that look like they send prompts
        prompt_call_fragments = (
            "create", "generate", "chat", "complete", "send",
            "invoke", "run", "predict",
        )
        if not any(f in call_name.lower() for f in prompt_call_fragments):
            return

        for arg in (*node.args, *(kw.value for kw in node.keywords)):
            if self._has_user_input_in_fstring(arg):
                self._add(
                    line_number=self._lineno(node),
                    line_text=self._line_text(node),
                    framework="",
                    pattern_name="prompt_injection:fstring",
                    pattern_category="security",
                    pattern_severity="high",
                    pattern_description=(
                        "User input directly interpolated into prompt via f-string "
                        "— prompt injection risk"
                    ),
                    snippet=self._snippet(node),
                    component_type="llm_provider",
                    provider="",
                    owasp_id="LLM01",
                )
                return
            if self._has_user_input_in_format_call(arg):
                self._add(
                    line_number=self._lineno(node),
                    line_text=self._line_text(node),
                    framework="",
                    pattern_name="prompt_injection:format",
                    pattern_category="security",
                    pattern_severity="high",
                    pattern_description=(
                        "User input passed via .format() into prompt "
                        "— prompt injection risk"
                    ),
                    snippet=self._snippet(node),
                    component_type="llm_provider",
                    provider="",
                    owasp_id="LLM01",
                )
                return

    def _has_user_input_in_fstring(self, node: ast.expr) -> bool:
        """Check whether an f-string (JoinedStr) contains user-input variable names."""
        if isinstance(node, ast.JoinedStr):
            for value in node.values:
                if isinstance(value, ast.FormattedValue):
                    name = _dotted_name(value.value) if isinstance(value.value, (ast.Name, ast.Attribute)) else ""
                    parts = set(name.lower().split("."))
                    if parts & _USER_INPUT_VARS:
                        return True
        return False

    def _has_user_input_in_format_call(self, node: ast.expr) -> bool:
        """Check for `"...".format(user_input)`."""
        if isinstance(node, ast.Call):
            func_name = _dotted_name(node.func)
            if func_name.endswith(".format"):
                for arg in node.args:
                    if isinstance(arg, ast.Name) and arg.id.lower() in _USER_INPUT_VARS:
                        return True
                for kw in node.keywords:
                    if isinstance(kw.value, ast.Name) and kw.value.id.lower() in _USER_INPUT_VARS:
                        return True
        return False

    # ── eval() / exec() on LLM output ───────────────────────────────

    def _check_eval_exec(self, call_name: str, node: ast.Call) -> None:
        if call_name not in ("eval", "exec"):
            return
        for arg in node.args:
            arg_name = _dotted_name(arg) if isinstance(arg, (ast.Name, ast.Attribute)) else ""
            parts = set(arg_name.lower().split("."))
            if parts & _LLM_OUTPUT_VARS:
                self._add(
                    line_number=self._lineno(node),
                    line_text=self._line_text(node),
                    framework="",
                    pattern_name=f"dangerous_call:{call_name}",
                    pattern_category="security",
                    pattern_severity="critical",
                    pattern_description=(
                        f"{call_name}() called on likely LLM output variable "
                        f"— critical injection / code-execution risk"
                    ),
                    snippet=self._snippet(node),
                    component_type="llm_provider",
                    provider="",
                    owasp_id="LLM05",
                )

    # ── Missing max_tokens ───────────────────────────────────────────

    def _check_missing_max_tokens(self, call_name: str, node: ast.Call) -> None:
        completion_fragments = ("completions.create", "messages.create",
                                "generate_content", "chat.complete")
        if not any(call_name.endswith(f) for f in completion_fragments):
            return
        if not self._has_kwarg(node, "max_tokens") and not self._has_kwarg(node, "max_completion_tokens"):
            self._add(
                line_number=self._lineno(node),
                line_text=self._line_text(node),
                framework="",
                pattern_name="missing_max_tokens",
                pattern_category="security",
                pattern_severity="low",
                pattern_description=(
                    "LLM call without max_tokens — risk of unbounded token consumption"
                ),
                snippet=self._snippet(node),
                component_type="llm_provider",
                provider="",
                owasp_id="LLM10",
            )

    # ── tools= kwarg → excessive agency ──────────────────────────────

    def _check_tools_kwarg(self, call_name: str, node: ast.Call) -> None:
        agent_call_fragments = ("Agent(", "Crew(", "AssistantAgent(", "UserProxyAgent(")
        is_agent = any(call_name.endswith(f.rstrip("(")) for f in agent_call_fragments)
        if not is_agent:
            return
        if self._has_kwarg(node, "tools"):
            self._add(
                line_number=self._lineno(node),
                line_text=self._line_text(node),
                framework="",
                pattern_name="excessive_agency:tools",
                pattern_category="security",
                pattern_severity="medium",
                pattern_description=(
                    "Agent with tool access — verify tools follow least-privilege principle"
                ),
                snippet=self._snippet(node),
                component_type="agent_tool",
                provider="",
                owasp_id="LLM06",
            )
        # Check allow_delegation=True
        for kw in node.keywords:
            if kw.arg == "allow_delegation":
                if isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    self._add(
                        line_number=self._lineno(node),
                        line_text=self._line_text(node),
                        framework="",
                        pattern_name="excessive_agency:delegation",
                        pattern_category="security",
                        pattern_severity="high",
                        pattern_description=(
                            "Agent delegation enabled — verify delegation scope is appropriate"
                        ),
                        snippet=self._snippet(node),
                        component_type="agent_tool",
                        provider="",
                        owasp_id="LLM06",
                    )
            if kw.arg == "code_execution_config":
                self._add(
                    line_number=self._lineno(node),
                    line_text=self._line_text(node),
                    framework="",
                    pattern_name="excessive_agency:code_execution",
                    pattern_category="security",
                    pattern_severity="critical",
                    pattern_description=(
                        "Agent with code execution capability — high risk for arbitrary code execution"
                    ),
                    snippet=self._snippet(node),
                    component_type="agent_tool",
                    provider="",
                    owasp_id="LLM06",
                )

    # ── Assign nodes: track model="…" assignments ────────────────────

    def visit_Assign(self, node: ast.Assign) -> None:
        # Track simple name = "model-string" assignments
        if (
            len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            val = node.value.value
            name = node.targets[0].id
            if val.lower() in self.idx.model_names:
                self._assigned_models[name] = val
                provider = self.idx.model_map.get(val.lower(), "")
                self._add(
                    line_number=self._lineno(node),
                    line_text=self._line_text(node),
                    framework="",
                    pattern_name=f"model_ref:{val}",
                    pattern_category="model_reference",
                    pattern_severity="info",
                    pattern_description=f"Model name '{val}' assigned to variable '{name}'",
                    snippet=self._snippet(node),
                    model_name=val,
                    component_type="llm_provider",
                    provider=provider,
                )
        self.generic_visit(node)

    # ── String constants: detect model names in literals ─────────────

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, str) and node.value.lower() in self.idx.model_names:
            # Avoid duplicate reports if already captured as Assign
            provider = self.idx.model_map.get(node.value.lower(), "")
            self._add(
                line_number=self._lineno(node),
                line_text=self._line_text(node),
                framework="",
                pattern_name=f"model_literal:{node.value}",
                pattern_category="model_reference",
                pattern_severity="info",
                pattern_description=f"Model name '{node.value}' found in string literal",
                snippet=self._snippet(node),
                model_name=node.value,
                component_type="llm_provider",
                provider=provider,
            )
        self.generic_visit(node)

    # ── Regex-based risk patterns from signatures ────────────────────

    def visit_Module(self, node: ast.Module) -> None:
        """After the regular AST walk, run regex risk patterns across the source."""
        self.generic_visit(node)
        self._run_regex_risk_patterns()

    def _run_regex_risk_patterns(self) -> None:
        full_source = "\n".join(self.source_lines)
        for rp in self.idx.risk_patterns:
            pattern_str = rp.get("pattern")
            if not pattern_str:
                continue
            try:
                regex = re.compile(pattern_str)
            except re.error:
                continue
            for i, line in enumerate(self.source_lines, start=1):
                if regex.search(line):
                    self._add(
                        line_number=i + self.line_offset,
                        line_text=line.rstrip(),
                        framework="",
                        pattern_name=f"risk_pattern:{rp.get('_name', rp.get('_provider', 'unknown'))}",
                        pattern_category="security",
                        pattern_severity=rp.get("severity", "medium"),
                        pattern_description=rp.get("message", "Risk pattern matched"),
                        snippet=_get_snippet(self.source_lines, i),
                        component_type=rp.get("_category", ""),
                        provider=rp.get("_provider", ""),
                        owasp_id=rp.get("owasp"),
                    )
