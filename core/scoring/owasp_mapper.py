"""
OWASP LLM Top 10 (2025) mapper for ScanLLM.

Maps scanner findings to the relevant OWASP LLM Top 10 categories,
producing a coverage report that shows which risks have been detected
in the scanned repository.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_RULES_PATH = Path(__file__).parent / "rules.yaml"


def _load_owasp_rules(path: Path | None = None) -> dict[str, dict[str, str]]:
    """Load OWASP category definitions from rules.yaml."""
    rules_file = path or _RULES_PATH
    try:
        with open(rules_file, "r") as fh:
            data = yaml.safe_load(fh) or {}
            return data.get("owasp", {})
    except FileNotFoundError:
        logger.warning("Rules file not found at %s", rules_file)
        return {}


# ---------------------------------------------------------------------------
# Pattern-category → OWASP-ID mapping
# ---------------------------------------------------------------------------
# Scanner findings carry a ``pattern_category`` (and sometimes an explicit
# ``owasp_id``).  This table maps known pattern categories to the OWASP
# category they indicate.

_CATEGORY_TO_OWASP: dict[str, str] = {
    # LLM01 — Prompt Injection
    "prompt_injection": "LLM01",
    "user_input_in_prompt": "LLM01",
    "unsanitized_prompt": "LLM01",
    "f_string_prompt": "LLM01",
    "format_string_prompt": "LLM01",
    "string_concat_prompt": "LLM01",
    # LLM02 — Sensitive Information Disclosure
    "sensitive_info_disclosure": "LLM02",
    "pii_in_prompt": "LLM02",
    "credentials_in_prompt": "LLM02",
    # LLM03 — Supply Chain
    "supply_chain": "LLM03",
    "outdated_package": "LLM03",
    "vulnerable_package": "LLM03",
    "unverified_model": "LLM03",
    "phantom_dependency": "LLM03",
    # LLM05 — Improper Output Handling
    "improper_output_handling": "LLM05",
    "eval_llm_output": "LLM05",
    "exec_llm_output": "LLM05",
    "unsanitized_output_to_sql": "LLM05",
    "unsanitized_output_to_shell": "LLM05",
    "unsanitized_output_to_html": "LLM05",
    # LLM06 — Excessive Agency
    "excessive_agency": "LLM06",
    "broad_tool_access": "LLM06",
    "missing_human_in_loop": "LLM06",
    # LLM07 — System Prompt Leakage
    "system_prompt_leakage": "LLM07",
    "secret_in_prompt": "LLM07",
    "api_key_in_prompt": "LLM07",
    # LLM08 — Vector/Embedding Weaknesses
    "vector_db_weakness": "LLM08",
    "unauthenticated_vector_db": "LLM08",
    "no_vector_db_acl": "LLM08",
    # LLM10 — Unbounded Consumption
    "unbounded_consumption": "LLM10",
    "missing_max_tokens": "LLM10",
    "missing_rate_limit": "LLM10",
    "missing_timeout": "LLM10",
}

# Component-type based heuristics: if no explicit pattern_category matches,
# fall back to component_type signals.
_COMPONENT_TO_OWASP: dict[str, str] = {
    "secret": "LLM07",
}


class OwaspMapper:
    """Maps scanner findings to the OWASP LLM Top 10 (2025) categories."""

    def __init__(self, rules_path: Path | None = None) -> None:
        self._owasp_rules = _load_owasp_rules(rules_path)

    def map_findings(self, findings: list[dict[str, Any]]) -> dict[str, Any]:
        """Map *findings* to OWASP LLM Top 10 categories.

        Parameters
        ----------
        findings:
            List of finding dicts from the scanner.  Relevant keys:
            ``pattern_category``, ``component_type``, ``owasp_id``,
            ``severity``, ``file_path``, ``line_number``, ``message``.

        Returns
        -------
        dict
            ``categories`` — list of per-OWASP-ID status dicts.
            ``coverage`` — summary counts of detected / not_detected.
        """
        # Build empty buckets for every known OWASP category.
        buckets: dict[str, list[dict[str, Any]]] = {
            oid: [] for oid in self._owasp_rules
        }

        for finding in findings:
            owasp_id = self._resolve_owasp_id(finding)
            if owasp_id and owasp_id in buckets:
                buckets[owasp_id].append(self._finding_ref(finding))

        categories = self._build_categories(buckets)

        detected = sum(1 for c in categories if c["status"] == "detected")
        partially = sum(1 for c in categories if c["status"] == "partially_mitigated")
        not_detected = sum(1 for c in categories if c["status"] == "not_detected")

        result: dict[str, Any] = {
            "categories": categories,
            "coverage": {
                "detected": detected,
                "partially_mitigated": partially,
                "not_detected": not_detected,
                "total": len(categories),
            },
        }

        logger.info(
            "OWASP mapping: %d detected, %d not detected out of %d categories",
            detected,
            not_detected,
            len(categories),
        )
        return result

    # ------------------------------------------------------------------
    # Resolution helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_owasp_id(finding: dict[str, Any]) -> str | None:
        """Determine the OWASP ID for a single finding.

        Priority:
        1. Explicit ``owasp_id`` on the finding.
        2. ``pattern_category`` lookup in the mapping table.
        3. ``component_type`` fallback.
        """
        # 1. Explicit
        explicit = (finding.get("owasp_id") or "").upper()
        if explicit:
            return explicit

        # 2. Pattern category
        cat = (finding.get("pattern_category") or "").lower()
        if cat in _CATEGORY_TO_OWASP:
            return _CATEGORY_TO_OWASP[cat]

        # 3. Component type fallback
        comp = (finding.get("component_type") or "").lower()
        if comp in _COMPONENT_TO_OWASP:
            return _COMPONENT_TO_OWASP[comp]

        return None

    @staticmethod
    def _finding_ref(finding: dict[str, Any]) -> dict[str, Any]:
        """Create a compact reference to a finding for inclusion in the report."""
        return {
            "file_path": finding.get("file_path", ""),
            "line_number": finding.get("line_number"),
            "message": finding.get("message", ""),
            "severity": finding.get("severity", "info"),
            "pattern_category": finding.get("pattern_category", ""),
        }

    def _build_categories(
        self,
        buckets: dict[str, list[dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        """Build the per-category status list."""
        categories: list[dict[str, Any]] = []

        for owasp_id in sorted(buckets):
            rule = self._owasp_rules.get(owasp_id, {})
            matched = buckets[owasp_id]
            count = len(matched)

            if count == 0:
                status = "not_detected"
            else:
                status = "detected"

            categories.append({
                "id": owasp_id,
                "name": rule.get("name", owasp_id),
                "description": rule.get("description", ""),
                "remediation": rule.get("remediation", ""),
                "severity": rule.get("severity", "medium"),
                "status": status,
                "findings_count": count,
                "findings": matched,
            })

        return categories
