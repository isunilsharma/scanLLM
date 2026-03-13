"""Tests for the OWASP LLM Top 10 mapper.

Verifies correct mapping of scanner findings to OWASP categories
and coverage tracking.
"""

import re
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


def _load_signatures() -> dict:
    sig_path = BACKEND_DIR.parent / "ai_signatures.yaml"
    if not sig_path.exists():
        sig_path = BACKEND_DIR / "app" / "scanner" / "signatures" / "ai_signatures.yaml"
    if not sig_path.exists():
        pytest.skip("ai_signatures.yaml not found")
    with open(sig_path) as f:
        return yaml.safe_load(f)


# OWASP mapping based on signatures and rules
OWASP_MAPPINGS = {
    "LLM01": {
        "name": "Prompt Injection",
        "patterns": [r"f['\"].*\{(?:user_input|request|query|message|prompt)\}.*['\"]"],
        "severity": "high",
    },
    "LLM02": {
        "name": "Sensitive Information Disclosure",
        "patterns": [],  # Detected via secret scanner
        "severity": "high",
    },
    "LLM03": {
        "name": "Supply Chain Vulnerabilities",
        "patterns": [],  # Detected via dependency scanner
        "severity": "critical",
    },
    "LLM05": {
        "name": "Improper Output Handling",
        "patterns": [
            r"eval\(.*(?:response|result|output|completion|message)",
            r"exec\(.*(?:response|result|output|completion|message)",
        ],
        "severity": "critical",
    },
    "LLM06": {
        "name": "Excessive Agency",
        "patterns": [
            r"tools=\[",
            r"allow_delegation=True",
            r"code_execution_config",
        ],
        "severity": "high",
    },
    "LLM07": {
        "name": "System Prompt Leakage",
        "patterns": [r"(sk-[a-zA-Z0-9]{20,}|sk-proj-[a-zA-Z0-9-_]{20,})"],
        "severity": "medium",
    },
    "LLM10": {
        "name": "Unbounded Consumption",
        "patterns": [],  # Detected via absent max_tokens
        "severity": "low",
    },
}


def map_finding_to_owasp(finding: dict) -> list[str]:
    """Map a scanner finding to OWASP LLM Top 10 categories.

    Returns a list of OWASP IDs that the finding matches.
    """
    matched = []
    line_text = finding.get("line_text", "")

    for owasp_id, mapping in OWASP_MAPPINGS.items():
        for pattern in mapping["patterns"]:
            if re.search(pattern, line_text):
                matched.append(owasp_id)
                break

    # Also respect explicit owasp tag from signatures
    if finding.get("owasp"):
        if finding["owasp"] not in matched:
            matched.append(finding["owasp"])

    return matched


def compute_owasp_coverage(findings: list[dict]) -> dict:
    """Compute which OWASP categories are covered by findings.

    Returns a dict of {owasp_id: count}.
    """
    coverage = {oid: 0 for oid in OWASP_MAPPINGS}
    for finding in findings:
        mapped = map_finding_to_owasp(finding)
        for oid in mapped:
            if oid in coverage:
                coverage[oid] += 1
    return coverage


class TestPromptInjectionMapping:
    """Test LLM01 - Prompt Injection mapping."""

    def test_maps_prompt_injection_to_llm01(self):
        finding = {
            "line_text": 'prompt = f"You are a helper. {user_input}"',
            "owasp": "LLM01",
        }
        owasp_ids = map_finding_to_owasp(finding)
        assert "LLM01" in owasp_ids

    def test_fstring_with_request_maps_to_llm01(self):
        finding = {
            "line_text": 'query = f"Search for: {request}"',
        }
        owasp_ids = map_finding_to_owasp(finding)
        assert "LLM01" in owasp_ids

    def test_fstring_with_query_maps_to_llm01(self):
        finding = {
            "line_text": 'prompt = f"Answer the question: {query}"',
        }
        owasp_ids = map_finding_to_owasp(finding)
        assert "LLM01" in owasp_ids


class TestImproperOutputMapping:
    """Test LLM05 - Improper Output Handling."""

    def test_maps_eval_to_llm05(self):
        finding = {
            "line_text": "eval(result.choices[0].message.content)",
            "owasp": "LLM05",
        }
        owasp_ids = map_finding_to_owasp(finding)
        assert "LLM05" in owasp_ids

    def test_maps_exec_to_llm05(self):
        finding = {
            "line_text": "exec(response.text)",
        }
        owasp_ids = map_finding_to_owasp(finding)
        assert "LLM05" in owasp_ids


class TestExcessiveAgencyMapping:
    """Test LLM06 - Excessive Agency."""

    def test_maps_agent_tools_to_llm06(self):
        finding = {
            "line_text": "tools=[search_tool, web_tool]",
        }
        owasp_ids = map_finding_to_owasp(finding)
        assert "LLM06" in owasp_ids

    def test_maps_allow_delegation_to_llm06(self):
        finding = {
            "line_text": "allow_delegation=True",
        }
        owasp_ids = map_finding_to_owasp(finding)
        assert "LLM06" in owasp_ids

    def test_maps_code_execution_config_to_llm06(self):
        finding = {
            "line_text": 'code_execution_config={"work_dir": "coding"}',
        }
        owasp_ids = map_finding_to_owasp(finding)
        assert "LLM06" in owasp_ids


class TestSystemPromptLeakageMapping:
    """Test LLM07 - System Prompt Leakage (hardcoded keys)."""

    def test_maps_hardcoded_key_to_llm07(self):
        finding = {
            "line_text": 'api_key = "sk-1234567890abcdef1234567890abcdef"',
        }
        owasp_ids = map_finding_to_owasp(finding)
        assert "LLM07" in owasp_ids


class TestOWASPCoverage:
    """Test OWASP coverage computation."""

    def test_coverage_count(self):
        findings = [
            {"line_text": 'prompt = f"Answer: {user_input}"', "owasp": "LLM01"},
            {"line_text": "eval(result.content)", "owasp": "LLM05"},
            {"line_text": "tools=[tool1]"},
            {"line_text": 'key = "sk-abcdefghijklmnopqrstuvwxyz1234567890"'},
        ]

        coverage = compute_owasp_coverage(findings)
        assert coverage["LLM01"] >= 1, "Should have LLM01 coverage"
        assert coverage["LLM05"] >= 1, "Should have LLM05 coverage"
        assert coverage["LLM06"] >= 1, "Should have LLM06 coverage"
        assert coverage["LLM07"] >= 1, "Should have LLM07 coverage"

    def test_empty_findings_no_coverage(self):
        coverage = compute_owasp_coverage([])
        for owasp_id, count in coverage.items():
            assert count == 0, f"{owasp_id} should have 0 coverage with no findings"

    def test_owasp_ids_in_rules_yaml(self):
        """Verify that rules.yaml contains the OWASP IDs we map to."""
        rules = _load_rules()
        owasp_section = rules.get("owasp", {})

        for owasp_id in ("LLM01", "LLM05", "LLM06", "LLM07", "LLM10"):
            assert owasp_id in owasp_section, f"{owasp_id} should be in rules.yaml"

    def test_owasp_risk_patterns_in_signatures(self):
        """Verify ai_signatures.yaml has the risk patterns we expect."""
        sigs = _load_signatures()
        risk_patterns = sigs.get("risk_patterns", {})

        assert "hardcoded_api_key" in risk_patterns
        assert "eval_llm_output" in risk_patterns
        assert "unsanitized_fstring_prompt" in risk_patterns
        assert "missing_max_tokens" in risk_patterns
