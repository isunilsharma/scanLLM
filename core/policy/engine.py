"""
Policy engine for ScanLLM.

Evaluates scan findings and scan-level metrics against user-defined
policy rules loaded from YAML. Rules use a generic condition/operator
system so new policies can be expressed without code changes.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from core.policy.defaults import DEFAULT_POLICIES_YAML
from core.policy.rules import PolicyResult, PolicyRule, PolicyViolation

logger = logging.getLogger(__name__)


class PolicyEngine:
    """Evaluate scan results against policy rules.

    Policies are defined in YAML and can operate at two levels:

    - **finding_level** — evaluated against each individual finding.
      A violation is emitted for every finding that matches ALL conditions.
    - **scan_level** — evaluated once against the scan summary dict
      (risk_score, total findings, etc.).
    """

    def __init__(self, policies_path: Path | str | None = None) -> None:
        self.rules: list[PolicyRule] = []
        if policies_path is not None:
            self.load(Path(policies_path))
        else:
            self.load_defaults()

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load(self, path: Path) -> None:
        """Load policy rules from a YAML file."""
        if not path.exists():
            logger.warning("Policy file not found: %s", path)
            return

        try:
            with open(path, encoding="utf-8") as fh:
                data = yaml.safe_load(fh) or {}
        except Exception:
            logger.exception("Failed to load policies from %s", path)
            return

        raw_policies = data.get("policies", [])
        self.rules = [
            PolicyRule.from_dict(p) for p in raw_policies if isinstance(p, dict)
        ]
        logger.info("Loaded %d policy rules from %s", len(self.rules), path)

    def load_yaml(self, yaml_string: str) -> None:
        """Load policy rules from a YAML string."""
        try:
            data = yaml.safe_load(yaml_string) or {}
        except Exception:
            logger.exception("Failed to parse policies YAML string")
            return

        raw_policies = data.get("policies", [])
        self.rules = [
            PolicyRule.from_dict(p) for p in raw_policies if isinstance(p, dict)
        ]
        logger.info("Loaded %d policy rules from YAML string", len(self.rules))

    def load_defaults(self) -> None:
        """Load the built-in default policy rules."""
        self.load_yaml(DEFAULT_POLICIES_YAML)
        logger.info("Loaded %d default policy rules", len(self.rules))

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def evaluate(
        self,
        findings: list[dict[str, Any]],
        scan_summary: dict[str, Any] | None = None,
    ) -> PolicyResult:
        """Evaluate all loaded policies against scan results.

        Parameters
        ----------
        findings:
            List of finding dicts from the scanner.
        scan_summary:
            Optional summary/metrics dict. Scan-level rules are evaluated
            against this dict (e.g. risk_score, total_findings).

        Returns
        -------
        PolicyResult with violations, passed rules, and aggregate counts.
        """
        result = PolicyResult()

        for rule in self.rules:
            violations = self._evaluate_rule(rule, findings, scan_summary or {})
            if violations:
                result.violations.extend(violations)
            else:
                result.passed_rules.append(rule.name)

        logger.info(
            "Policy evaluation: %d rules, %d errors, %d warnings, overall %s",
            len(self.rules),
            result.error_count,
            result.warning_count,
            "PASS" if result.is_passing else "FAIL",
        )
        return result

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _evaluate_rule(
        rule: PolicyRule,
        findings: list[dict[str, Any]],
        scan_summary: dict[str, Any],
    ) -> list[PolicyViolation]:
        """Evaluate a single rule. Returns a list of violations (empty if passes)."""

        violations: list[PolicyViolation] = []

        if rule.type == "scan_level":
            if rule.matches_scan(scan_summary):
                violations.append(
                    PolicyViolation(
                        rule_name=rule.name,
                        rule_description=rule.description,
                        severity=rule.severity,
                        finding=None,
                        message=_scan_violation_message(rule, scan_summary),
                    )
                )
        else:
            # finding_level — check every finding
            for finding in findings:
                if rule.matches_finding(finding):
                    violations.append(
                        PolicyViolation(
                            rule_name=rule.name,
                            rule_description=rule.description,
                            severity=rule.severity,
                            finding=finding,
                            message=_finding_violation_message(rule, finding),
                        )
                    )

        return violations

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @staticmethod
    def generate_default_policies() -> str:
        """Return the default policies YAML string."""
        return DEFAULT_POLICIES_YAML


# ---------------------------------------------------------------------------
# Message helpers
# ---------------------------------------------------------------------------

def _finding_violation_message(rule: PolicyRule, finding: dict[str, Any]) -> str:
    """Generate a human-readable message for a finding-level violation."""
    file_path = finding.get("file_path", "<unknown>")
    line = finding.get("line_number", "?")
    parts = [f"Policy '{rule.name}' violated"]

    detail_fields = ["model_name", "provider", "component_type", "pattern_name"]
    details = [
        f"{k}={finding[k]}"
        for k in detail_fields
        if finding.get(k)
    ]
    if details:
        parts.append(f"({', '.join(details)})")

    parts.append(f"in {file_path}:{line}")
    return " ".join(parts)


def _scan_violation_message(rule: PolicyRule, scan_summary: dict[str, Any]) -> str:
    """Generate a human-readable message for a scan-level violation."""
    parts = [f"Policy '{rule.name}' violated:"]
    for cond in rule.conditions:
        field = cond.get("field", "?")
        op = cond.get("operator", "?")
        expected = cond.get("value", "?")
        actual = scan_summary.get(field, "N/A")
        parts.append(f"{field}={actual} (expected {op} {expected})")
    return " ".join(parts)
