"""
Policy rule definitions, violation tracking, and evaluation result.

Rules use a generic condition system with operators (equals, in, not_in,
contains, greater_than, etc.) so that new policies can be expressed in
YAML without touching Python code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Condition evaluation helpers
# ---------------------------------------------------------------------------

def _resolve_field(data: dict[str, Any], field_name: str) -> Any:
    """Resolve a possibly-nested field name (dot-separated) from a dict."""
    parts = field_name.split(".")
    current: Any = data
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def _evaluate_condition(condition: dict[str, Any], data: dict[str, Any]) -> bool:
    """Evaluate a single condition against a data dict.

    Supported operators:
        equals, not_equals, in, not_in, contains, not_contains,
        greater_than, less_than, exists, not_exists
    """
    field_name: str = condition.get("field", "")
    operator: str = condition.get("operator", "equals")
    expected: Any = condition.get("value")

    actual = _resolve_field(data, field_name)

    if operator == "exists":
        return actual is not None and actual != "" and actual != []

    if operator == "not_exists":
        return actual is None or actual == "" or actual == []

    # Normalise strings for comparison
    actual_norm = actual.lower() if isinstance(actual, str) else actual
    expected_norm: Any
    if isinstance(expected, str):
        expected_norm = expected.lower()
    elif isinstance(expected, list):
        expected_norm = [v.lower() if isinstance(v, str) else v for v in expected]
    else:
        expected_norm = expected

    if operator == "equals":
        return actual_norm == expected_norm

    if operator == "not_equals":
        return actual_norm != expected_norm

    if operator == "in":
        # actual value is in the expected list
        if not isinstance(expected_norm, list):
            return False
        return actual_norm in expected_norm

    if operator == "not_in":
        # actual value is NOT in the expected list
        if not isinstance(expected_norm, list):
            return True
        return actual_norm not in expected_norm

    if operator == "contains":
        # actual string contains expected substring
        if actual_norm is None:
            return False
        return str(expected_norm) in str(actual_norm)

    if operator == "not_contains":
        if actual_norm is None:
            return True
        return str(expected_norm) not in str(actual_norm)

    if operator == "greater_than":
        if actual is None or expected is None:
            return False
        try:
            return float(actual) > float(expected)
        except (ValueError, TypeError):
            return False

    if operator == "less_than":
        if actual is None or expected is None:
            return False
        try:
            return float(actual) < float(expected)
        except (ValueError, TypeError):
            return False

    # Unknown operator — do not match
    return False


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class PolicyRule:
    """A single policy rule definition."""

    name: str
    description: str
    severity: str  # "error", "warning", "info"
    conditions: list[dict[str, Any]]
    type: str = "finding_level"  # "finding_level" or "scan_level"

    def matches_finding(self, finding: dict[str, Any]) -> bool:
        """Check if a finding matches ALL conditions of this rule (AND logic)."""
        if not self.conditions:
            return False
        return all(_evaluate_condition(c, finding) for c in self.conditions)

    def matches_scan(self, scan_summary: dict[str, Any]) -> bool:
        """Check if scan-level conditions are met."""
        if not self.conditions:
            return False
        return all(_evaluate_condition(c, scan_summary) for c in self.conditions)

    # -- Serialization helpers -----------------------------------------------

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PolicyRule:
        """Parse a policy rule from a YAML/dict representation."""
        return cls(
            name=data.get("name", "unnamed"),
            description=data.get("description", ""),
            severity=data.get("severity", "warning"),
            conditions=data.get("conditions", []),
            type=data.get("type", "finding_level"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a dict suitable for YAML output."""
        d: dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "severity": self.severity,
            "conditions": self.conditions,
        }
        if self.type != "finding_level":
            d["type"] = self.type
        return d


@dataclass
class PolicyViolation:
    """A single policy violation instance."""

    rule_name: str
    rule_description: str
    severity: str
    finding: dict[str, Any] | None = None  # None for scan-level rules
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "rule_name": self.rule_name,
            "rule_description": self.rule_description,
            "severity": self.severity,
            "message": self.message,
        }
        if self.finding is not None:
            result["file_path"] = self.finding.get("file_path", "")
            result["line_number"] = self.finding.get("line_number")
            result["pattern_name"] = self.finding.get("pattern_name", "")
        return result


@dataclass
class PolicyResult:
    """Aggregated result of evaluating all policy rules."""

    violations: list[PolicyViolation] = field(default_factory=list)
    passed_rules: list[str] = field(default_factory=list)

    @property
    def is_passing(self) -> bool:
        """True if there are no error-severity violations."""
        return not any(v.severity == "error" for v in self.violations)

    @property
    def error_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "warning")

    @property
    def info_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "info")

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON output."""
        return {
            "is_passing": self.is_passing,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "total_violations": len(self.violations),
            "passed_rules": self.passed_rules,
            "violations": [v.to_dict() for v in self.violations],
        }
