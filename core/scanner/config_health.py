"""Configuration health checker for AI/LLM best practices."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any


class ConfigHealthScanner:
    """Check AI configurations for best practices."""

    # Best practices to check for in LLM API calls
    RECOMMENDED_PARAMS = {
        "max_tokens": {
            "severity": "medium",
            "owasp": "LLM10",
            "message": "LLM call without max_tokens — unbounded token usage and cost risk",
            "fix": "Add max_tokens parameter to limit response length and costs",
        },
        "temperature": {
            "severity": "info",
            "owasp": "",
            "message": "LLM call without explicit temperature — non-deterministic by default",
            "fix": "Set temperature=0 for deterministic outputs, or specify desired value",
        },
        "timeout": {
            "severity": "low",
            "owasp": "LLM10",
            "message": "LLM call without timeout — may hang indefinitely",
            "fix": "Add timeout parameter or wrap in asyncio.wait_for()",
        },
    }

    # API call patterns that should have error handling
    LLM_CALL_PATTERNS = [
        "chat.completions.create",
        "messages.create",
        "completions.create",
        "embeddings.create",
        "generate",
        "generateText",
        "streamText",
    ]

    def scan(self, file_path: Path, content: str) -> list[dict[str, Any]]:
        """Scan a Python file for configuration health issues."""
        findings: list[dict[str, Any]] = []

        if file_path.suffix != ".py":
            return findings

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return findings

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            call_name = self._get_call_name(node)
            if not call_name:
                continue

            is_llm_call = any(p in call_name for p in self.LLM_CALL_PATTERNS)
            if not is_llm_call:
                continue

            # Check for recommended parameters
            kwarg_names = {kw.arg for kw in node.keywords if kw.arg}

            for param, info in self.RECOMMENDED_PARAMS.items():
                if param not in kwarg_names:
                    findings.append({
                        "file_path": str(file_path),
                        "line_number": node.lineno,
                        "pattern_name": f"missing-{param}",
                        "pattern_category": f"missing_{param}",
                        "provider": "",
                        "component_type": "config_health",
                        "severity": info["severity"],
                        "owasp_id": info["owasp"],
                        "message": info["message"],
                        "fix_suggestion": info["fix"],
                    })

            # Check for error handling (is the call inside a try block?)
            if not self._is_inside_try(tree, node):
                findings.append({
                    "file_path": str(file_path),
                    "line_number": node.lineno,
                    "pattern_name": "no-error-handling",
                    "pattern_category": "no_error_handling",
                    "provider": "",
                    "component_type": "config_health",
                    "severity": "low",
                    "owasp_id": "",
                    "message": "LLM call without try/except — API errors will crash",
                    "fix_suggestion": "Wrap in try/except to handle API errors gracefully",
                })

        return findings

    def _get_call_name(self, node: ast.Call) -> str:
        """Extract the full call name from an AST Call node."""
        parts: list[str] = []
        current = node.func
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return ".".join(reversed(parts))

    def _is_inside_try(self, tree: ast.AST, target_node: ast.AST) -> bool:
        """Check if a node is inside a try/except block."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                for child in ast.walk(node):
                    if child is target_node:
                        return True
        return False
