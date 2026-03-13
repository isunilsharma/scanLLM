"""Tests for the risk scoring engine.

Verifies the 0-100 risk scoring formula, grade assignment,
and edge cases like no findings and score capping.
"""

import sys
from pathlib import Path

import pytest
import yaml

BACKEND_DIR = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(BACKEND_DIR))


def _load_rules() -> dict:
    rules_path = BACKEND_DIR / "app" / "scoring" / "rules.yaml"
    if not rules_path.exists():
        pytest.skip("rules.yaml not found")
    with open(rules_path) as f:
        return yaml.safe_load(f)


def compute_risk_score(
    secrets_found: int = 0,
    owasp_critical_count: int = 0,
    owasp_high_count: int = 0,
    outdated_packages: int = 0,
    provider_concentration: float = 0.0,
    missing_safety_configs: int = 0,
    excessive_agent_perms: int = 0,
    weights: dict | None = None,
) -> float:
    """Compute risk score based on the formula from CLAUDE.md.

    Returns a score capped at 0-100.
    """
    if weights is None:
        weights = {
            "secrets": 25,
            "owasp_critical": 20,
            "owasp_high": 10,
            "outdated_packages": 5,
            "provider_concentration": 10,
            "missing_safety_configs": 3,
            "excessive_agent_perms": 15,
        }

    raw = (
        secrets_found * weights["secrets"]
        + owasp_critical_count * weights["owasp_critical"]
        + owasp_high_count * weights["owasp_high"]
        + outdated_packages * weights["outdated_packages"]
        + provider_concentration * weights["provider_concentration"]
        + missing_safety_configs * weights["missing_safety_configs"]
        + excessive_agent_perms * weights["excessive_agent_perms"]
    )

    # Cap at 100
    return min(100.0, max(0.0, raw))


def assign_grade(score: float, grade_ranges: dict | None = None) -> str:
    """Assign a letter grade based on score.

    Default ranges from rules.yaml:
      A: [0, 20], B: [21, 40], C: [41, 60], D: [61, 80], F: [81, 100]
    """
    if grade_ranges is None:
        grade_ranges = {
            "A": [0, 20],
            "B": [21, 40],
            "C": [41, 60],
            "D": [61, 80],
            "F": [81, 100],
        }

    for grade, (low, high) in sorted(grade_ranges.items()):
        if low <= score <= high:
            return grade

    return "F"  # Default fallback for scores > 100


class TestRiskScoreComputation:
    """Test the risk score formula."""

    def test_score_with_no_findings(self):
        score = compute_risk_score()
        assert score == 0.0, "No findings should produce score of 0"

    def test_score_with_secrets(self):
        score = compute_risk_score(secrets_found=1)
        assert score == 25.0, "1 secret should add 25 to score"

    def test_score_with_multiple_secrets(self):
        score = compute_risk_score(secrets_found=3)
        assert score == 75.0, "3 secrets should add 75 to score"

    def test_score_with_critical_owasp(self):
        score = compute_risk_score(owasp_critical_count=1)
        assert score == 20.0, "1 critical OWASP should add 20"

    def test_score_with_high_owasp(self):
        score = compute_risk_score(owasp_high_count=2)
        assert score == 20.0, "2 high OWASP should add 20"

    def test_score_caps_at_100(self):
        score = compute_risk_score(
            secrets_found=5,       # 125
            owasp_critical_count=5, # 100
            owasp_high_count=5,     # 50
        )
        assert score == 100.0, "Score should cap at 100"

    def test_combined_score(self):
        score = compute_risk_score(
            secrets_found=1,            # 25
            owasp_critical_count=1,     # 20
            missing_safety_configs=2,   # 6
        )
        assert score == 51.0

    def test_provider_concentration(self):
        score = compute_risk_score(provider_concentration=1.0)
        assert score == 10.0

    def test_excessive_agent_perms(self):
        score = compute_risk_score(excessive_agent_perms=2)
        assert score == 30.0

    def test_uses_custom_weights(self):
        custom_weights = {
            "secrets": 50,
            "owasp_critical": 30,
            "owasp_high": 15,
            "outdated_packages": 10,
            "provider_concentration": 20,
            "missing_safety_configs": 5,
            "excessive_agent_perms": 25,
        }
        score = compute_risk_score(secrets_found=1, weights=custom_weights)
        assert score == 50.0

    def test_weights_match_rules_yaml(self):
        """Verify our default weights match what is in rules.yaml."""
        rules = _load_rules()
        yaml_weights = rules["weights"]
        assert yaml_weights["secrets"] == 25
        assert yaml_weights["owasp_critical"] == 20
        assert yaml_weights["owasp_high"] == 10
        assert yaml_weights["outdated_packages"] == 5
        assert yaml_weights["provider_concentration"] == 10
        assert yaml_weights["missing_safety_configs"] == 3
        assert yaml_weights["excessive_agent_perms"] == 15


class TestGradeAssignment:
    """Test letter grade assignment."""

    def test_grade_a(self):
        assert assign_grade(0) == "A"
        assert assign_grade(10) == "A"
        assert assign_grade(20) == "A"

    def test_grade_b(self):
        assert assign_grade(21) == "B"
        assert assign_grade(30) == "B"
        assert assign_grade(40) == "B"

    def test_grade_c(self):
        assert assign_grade(41) == "C"
        assert assign_grade(50) == "C"
        assert assign_grade(60) == "C"

    def test_grade_d(self):
        assert assign_grade(61) == "D"
        assert assign_grade(70) == "D"
        assert assign_grade(80) == "D"

    def test_grade_f(self):
        assert assign_grade(81) == "F"
        assert assign_grade(90) == "F"
        assert assign_grade(100) == "F"

    def test_grade_ranges_match_rules_yaml(self):
        rules = _load_rules()
        grades = rules["grades"]
        assert grades["A"] == [0, 20]
        assert grades["B"] == [21, 40]
        assert grades["C"] == [41, 60]
        assert grades["D"] == [61, 80]
        assert grades["F"] == [81, 100]
