"""
Risk scoring engine for ScanLLM.

Produces a normalised 0-100 risk score from scan findings and optional
graph analysis results.  Scoring weights and grade thresholds are loaded
from ``rules.yaml`` so they can be tuned without code changes.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_RULES_PATH = Path(__file__).parent / "rules.yaml"

# OWASP severity → internal severity bucket
_SEVERITY_ORDER = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
    "info": 4,
}


def _load_rules(path: Path | None = None) -> dict[str, Any]:
    """Load and return the scoring rules from YAML."""
    rules_file = path or _RULES_PATH
    try:
        with open(rules_file, "r") as fh:
            return yaml.safe_load(fh) or {}
    except FileNotFoundError:
        logger.warning("Rules file not found at %s — using built-in defaults", rules_file)
        return {}


class RiskEngine:
    """Calculates a 0-100 risk score for a scanned repository.

    The score is composed of weighted sub-scores for secrets, OWASP
    findings, outdated packages, provider concentration, missing safety
    configurations, and excessive agent permissions.
    """

    def __init__(self, rules_path: Path | None = None) -> None:
        self._rules = _load_rules(rules_path)
        self._weights: dict[str, int] = self._rules.get("weights", {
            "secrets": 25,
            "owasp_critical": 20,
            "owasp_high": 10,
            "outdated_packages": 5,
            "provider_concentration": 10,
            "missing_safety_configs": 3,
            "excessive_agent_perms": 15,
        })
        self._grades: dict[str, list[int]] = self._rules.get("grades", {
            "A": [0, 20],
            "B": [21, 40],
            "C": [41, 60],
            "D": [61, 80],
            "F": [81, 100],
        })
        self._owasp_rules: dict[str, dict[str, str]] = self._rules.get("owasp", {})

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def score(
        self,
        findings: list[dict[str, Any]],
        graph_analysis: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Compute the risk score for a set of findings.

        Parameters
        ----------
        findings:
            List of finding dicts from the scanner engine.  Each finding
            should contain at least ``pattern_category``, ``severity``,
            ``component_type``, and optionally ``owasp_id``.
        graph_analysis:
            Optional output from :meth:`GraphAnalyzer.analyze`, used
            for provider concentration scoring.

        Returns
        -------
        dict
            ``overall_score`` (0-100), ``grade`` (A-F), ``breakdown``
            per category, and ``severity_counts``.
        """
        counts = self._count_factors(findings, graph_analysis)
        breakdown = self._compute_breakdown(counts)
        raw_score = sum(item["score"] for item in breakdown.values())

        # Normalise: cap at 100.
        overall = min(100, max(0, raw_score))
        grade = self._assign_grade(overall)

        severity_counts = self._count_severities(findings)

        result: dict[str, Any] = {
            "overall_score": overall,
            "grade": grade,
            "breakdown": breakdown,
            "severity_counts": severity_counts,
        }

        logger.info(
            "Risk score: %d (%s) — %s",
            overall,
            grade,
            ", ".join(f"{k}={v['count']}" for k, v in breakdown.items()),
        )
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _count_factors(
        self,
        findings: list[dict[str, Any]],
        graph_analysis: dict[str, Any] | None,
    ) -> dict[str, int]:
        """Extract raw factor counts from findings and graph analysis."""
        secrets = 0
        owasp_critical = 0
        owasp_high = 0
        outdated_packages = 0
        missing_safety = 0
        excessive_agent = 0

        for f in findings:
            cat = (f.get("pattern_category") or "").lower()
            comp = (f.get("component_type") or "").lower()
            severity = (f.get("severity") or "").lower()
            owasp_id = (f.get("owasp_id") or "").upper()

            # Secrets
            if comp == "secret" or cat == "secret":
                secrets += 1

            # OWASP classification
            if owasp_id:
                owasp_sev = self._owasp_severity(owasp_id)
                if owasp_sev == "critical":
                    owasp_critical += 1
                elif owasp_sev == "high":
                    owasp_high += 1
            elif severity == "critical":
                owasp_critical += 1
            elif severity == "high":
                owasp_high += 1

            # Outdated packages
            if cat in ("outdated_package", "vulnerable_package", "supply_chain"):
                outdated_packages += 1

            # Missing safety configs
            if cat in ("missing_max_tokens", "missing_rate_limit", "missing_timeout", "unbounded_consumption"):
                missing_safety += 1

            # Excessive agent permissions
            if cat in ("excessive_agency", "broad_tool_access", "missing_human_in_loop"):
                excessive_agent += 1

        # Provider concentration from graph analysis
        concentration = 0
        if graph_analysis:
            conc = graph_analysis.get("concentration_risk", {})
            if conc.get("is_concentrated", False):
                concentration = 1

        return {
            "secrets": secrets,
            "owasp_critical": owasp_critical,
            "owasp_high": owasp_high,
            "outdated_packages": outdated_packages,
            "provider_concentration": concentration,
            "missing_safety_configs": missing_safety,
            "excessive_agent_perms": excessive_agent,
        }

    def _compute_breakdown(self, counts: dict[str, int]) -> dict[str, dict[str, int]]:
        """Multiply each factor count by its configured weight."""
        breakdown: dict[str, dict[str, int]] = {}
        for factor, count in counts.items():
            weight = self._weights.get(factor, 0)
            breakdown[factor] = {
                "count": count,
                "weight": weight,
                "score": count * weight,
            }
        return breakdown

    def _assign_grade(self, score: int) -> str:
        """Map a 0-100 score to a letter grade."""
        for grade, (low, high) in self._grades.items():
            if low <= score <= high:
                return grade
        # Fallback for out-of-range (should not happen).
        return "F" if score > 80 else "A"

    def _owasp_severity(self, owasp_id: str) -> str:
        """Look up the severity for an OWASP ID from rules."""
        rule = self._owasp_rules.get(owasp_id, {})
        return (rule.get("severity") or "medium").lower()

    @staticmethod
    def _count_severities(findings: list[dict[str, Any]]) -> dict[str, int]:
        """Count findings by severity level."""
        counts: dict[str, int] = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0,
        }
        for f in findings:
            sev = (f.get("severity") or "info").lower()
            if sev in counts:
                counts[sev] += 1
            else:
                counts["info"] += 1
        return counts
