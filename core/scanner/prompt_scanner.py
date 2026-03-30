"""Prompt inventory scanner — extract and catalog all prompts in codebase."""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any


class PromptScanner:
    """Extract and catalog prompts from Python source files."""

    # Patterns that indicate a prompt string
    PROMPT_INDICATORS = [
        r"system[\s_]*prompt",
        r"user[\s_]*prompt",
        r"assistant[\s_]*prompt",
        r"(?:system|user|assistant)[\s]*[=:]",
        r"messages?\s*=\s*\[",
        r"(?:template|prompt)[\s]*=",
        r"\.format\(",
        r"f['\"].*\{",
        r"role['\"]?\s*:\s*['\"](?:system|user|assistant)",
    ]

    PROMPT_VARIABLE_NAMES = {
        "system_prompt", "user_prompt", "prompt", "prompt_template",
        "system_message", "user_message", "template", "instruction",
        "system_instructions", "context_prompt", "few_shot_prompt",
        "prefix", "suffix", "preamble",
    }

    def scan(self, file_path: Path, content: str) -> list[dict[str, Any]]:
        """Scan a Python file for prompts."""
        prompts: list[dict[str, Any]] = []

        if file_path.suffix != ".py":
            return prompts

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return prompts

        for node in ast.walk(tree):
            # String assignments that look like prompts
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.lower() in self.PROMPT_VARIABLE_NAMES:
                        value_str = self._extract_string_value(node.value)
                        if value_str and len(value_str) > 20:
                            has_user_input = "{" in value_str or ".format" in value_str
                            prompts.append({
                                "file_path": str(file_path),
                                "line_number": node.lineno,
                                "type": "prompt_assignment",
                                "variable_name": target.id,
                                "content_preview": value_str[:200] + ("..." if len(value_str) > 200 else ""),
                                "estimated_tokens": len(value_str) // 4,
                                "has_user_input": has_user_input,
                                "has_pii_risk": self._check_pii_risk(value_str),
                                "component_type": "prompt_template",
                                "pattern_name": f"prompt-{target.id}",
                                "severity": "high" if has_user_input else "info",
                                "owasp_id": "LLM01" if has_user_input else "",
                            })

            # Messages lists (OpenAI-style)
            if isinstance(node, ast.Call):
                for keyword in getattr(node, "keywords", []):
                    if keyword.arg == "messages" and isinstance(keyword.value, ast.List):
                        for elt in keyword.value.elts:
                            if isinstance(elt, ast.Dict):
                                role = None
                                content_val = None
                                for k, v in zip(elt.keys, elt.values):
                                    k_str = self._extract_string_value(k)
                                    if k_str == "role":
                                        role = self._extract_string_value(v)
                                    elif k_str == "content":
                                        content_val = self._extract_string_value(v)

                                if role and content_val and len(content_val) > 10:
                                    has_user_input = "{" in content_val
                                    prompts.append({
                                        "file_path": str(file_path),
                                        "line_number": node.lineno,
                                        "type": f"{role}_message",
                                        "variable_name": f"messages[{role}]",
                                        "content_preview": content_val[:200] + ("..." if len(content_val) > 200 else ""),
                                        "estimated_tokens": len(content_val) // 4,
                                        "has_user_input": has_user_input,
                                        "has_pii_risk": self._check_pii_risk(content_val),
                                        "component_type": "prompt_template",
                                        "pattern_name": f"prompt-{role}-message",
                                        "severity": "medium" if role == "system" else "info",
                                        "owasp_id": "LLM07" if role == "system" else "",
                                    })

        return prompts

    def _extract_string_value(self, node: Any) -> str | None:
        """Extract string value from an AST node."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.JoinedStr):  # f-string
            parts = []
            for val in node.values:
                if isinstance(val, ast.Constant):
                    parts.append(str(val.value))
                else:
                    parts.append("{...}")
            return "".join(parts)
        return None

    def _check_pii_risk(self, text: str) -> bool:
        """Check if prompt text might contain PII patterns."""
        pii_patterns = [
            r"(?:name|email|phone|address|ssn|social.security)",
            r"(?:credit.card|account.number|password)",
            r"(?:date.of.birth|dob|birthdate)",
        ]
        text_lower = text.lower()
        return any(re.search(p, text_lower) for p in pii_patterns)
