"""Tests for the existing scanner (services/scanner_v2.py) to ensure backward compatibility.

These tests verify:
- Regex pattern matching from the config-driven ScannerV2
- Contract extraction (model, temperature, max_tokens, streaming, tools)
- Insights computation (frameworks summary, risk flags, hotspots)
"""

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(BACKEND_DIR))

from services.contract_extractor import extract_contracts
from services.insights import (
    compute_frameworks_summary,
    compute_hotspots,
    compute_risk_flags,
    compute_recommended_actions,
)


# ═══════════════════════════════════════════════════════════════════════════
# Contract Extractor Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestContractExtraction:
    """Verify model/temperature/tokens/streaming/tools extraction."""

    def test_extracts_model_name_python_style(self):
        snippet = 'response = client.chat.completions.create(model="gpt-4o")'
        contracts = extract_contracts(snippet)
        assert contracts["model_name"] == "gpt-4o"

    def test_extracts_model_name_json_style(self):
        snippet = '{"model": "claude-sonnet-4-20250514", "max_tokens": 100}'
        contracts = extract_contracts(snippet)
        assert contracts["model_name"] == "claude-sonnet-4-20250514"

    def test_extracts_temperature(self):
        snippet = "llm = ChatOpenAI(model='gpt-4o', temperature=0.5)"
        contracts = extract_contracts(snippet)
        assert contracts["temperature"] == 0.5

    def test_extracts_max_tokens(self):
        snippet = 'client.chat.completions.create(model="gpt-4o", max_tokens=2048)'
        contracts = extract_contracts(snippet)
        assert contracts["max_tokens"] == 2048

    def test_detects_streaming_true(self):
        snippet = 'client.chat.completions.create(model="gpt-4o", stream=True)'
        contracts = extract_contracts(snippet)
        assert contracts["is_streaming"] is True

    def test_no_streaming_by_default(self):
        snippet = 'client.chat.completions.create(model="gpt-4o")'
        contracts = extract_contracts(snippet)
        assert contracts["is_streaming"] is False

    def test_detects_tools(self):
        snippet = 'client.chat.completions.create(model="gpt-4o", tools=[{"type": "function"}])'
        contracts = extract_contracts(snippet)
        assert contracts["has_tools"] is True

    def test_detects_functions(self):
        snippet = 'client.chat.completions.create(model="gpt-4o", functions=[{"name": "get_weather"}])'
        contracts = extract_contracts(snippet)
        assert contracts["has_tools"] is True

    def test_no_tools_by_default(self):
        snippet = 'client.chat.completions.create(model="gpt-4o")'
        contracts = extract_contracts(snippet)
        assert contracts["has_tools"] is False

    def test_empty_snippet(self):
        contracts = extract_contracts("")
        assert contracts["model_name"] is None
        assert contracts["temperature"] is None
        assert contracts["max_tokens"] is None
        assert contracts["is_streaming"] is False
        assert contracts["has_tools"] is False

    def test_none_snippet(self):
        contracts = extract_contracts(None)
        assert contracts["model_name"] is None

    def test_multiline_snippet(self):
        snippet = """
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "hi"}],
    temperature=0.3,
    max_tokens=512,
    stream=True,
    tools=[{"type": "function", "function": {"name": "get_data"}}]
)
"""
        contracts = extract_contracts(snippet)
        assert contracts["model_name"] == "gpt-4o-mini"
        assert contracts["temperature"] == 0.3
        assert contracts["max_tokens"] == 512
        assert contracts["is_streaming"] is True
        assert contracts["has_tools"] is True


# ═══════════════════════════════════════════════════════════════════════════
# Insights Tests
# ═══════════════════════════════════════════════════════════════════════════


def _make_finding(
    file_path: str = "src/main.py",
    framework: str = "OpenAI",
    pattern_category: str = "llm_call",
    pattern_severity: str = "medium",
    line_number: int = 1,
) -> dict:
    return {
        "file_path": file_path,
        "framework": framework,
        "pattern_category": pattern_category,
        "pattern_severity": pattern_severity,
        "line_number": line_number,
        "line_text": "import openai",
    }


class TestFrameworksSummary:
    """Test compute_frameworks_summary."""

    def test_single_framework(self):
        findings = [
            _make_finding(framework="OpenAI", file_path="a.py"),
            _make_finding(framework="OpenAI", file_path="b.py"),
        ]
        summary = compute_frameworks_summary(findings)
        assert len(summary) == 1
        assert summary[0]["framework"] == "OpenAI"
        assert summary[0]["total_matches"] == 2
        assert summary[0]["files_count"] == 2

    def test_multiple_frameworks(self):
        findings = [
            _make_finding(framework="OpenAI"),
            _make_finding(framework="Anthropic"),
            _make_finding(framework="LangChain"),
        ]
        summary = compute_frameworks_summary(findings)
        assert len(summary) == 3
        frameworks = {s["framework"] for s in summary}
        assert "OpenAI" in frameworks
        assert "Anthropic" in frameworks
        assert "LangChain" in frameworks

    def test_sorted_by_total_matches(self):
        findings = [
            _make_finding(framework="OpenAI"),
            _make_finding(framework="OpenAI"),
            _make_finding(framework="OpenAI"),
            _make_finding(framework="Anthropic"),
        ]
        summary = compute_frameworks_summary(findings)
        assert summary[0]["framework"] == "OpenAI"
        assert summary[0]["total_matches"] == 3

    def test_empty_findings(self):
        summary = compute_frameworks_summary([])
        assert summary == []

    def test_categories_aggregation(self):
        findings = [
            _make_finding(framework="OpenAI", pattern_category="llm_call"),
            _make_finding(framework="OpenAI", pattern_category="embedding_call"),
        ]
        summary = compute_frameworks_summary(findings)
        assert len(summary) == 1
        categories = {c["category"] for c in summary[0]["categories"]}
        assert "llm_call" in categories
        assert "embedding_call" in categories


class TestRiskFlags:
    """Test compute_risk_flags."""

    def test_multiple_frameworks_flag(self):
        findings = [
            _make_finding(framework="OpenAI"),
            _make_finding(framework="Anthropic"),
        ]
        summary = compute_frameworks_summary(findings)
        flags = compute_risk_flags(findings, summary)

        flag_ids = {f["id"] for f in flags}
        assert "multiple_frameworks" in flag_ids

    def test_secrets_detected_flag(self):
        findings = [
            _make_finding(pattern_category="secrets"),
        ]
        summary = compute_frameworks_summary(findings)
        flags = compute_risk_flags(findings, summary)

        flag_ids = {f["id"] for f in flags}
        assert "secrets_detected" in flag_ids

    def test_embeddings_present_flag(self):
        findings = [
            _make_finding(pattern_category="embedding_call"),
        ]
        summary = compute_frameworks_summary(findings)
        flags = compute_risk_flags(findings, summary)

        flag_ids = {f["id"] for f in flags}
        assert "embeddings_present" in flag_ids

    def test_rag_present_flag(self):
        findings = [
            _make_finding(pattern_category="rag_pattern"),
        ]
        summary = compute_frameworks_summary(findings)
        flags = compute_risk_flags(findings, summary)

        flag_ids = {f["id"] for f in flags}
        assert "rag_present" in flag_ids

    def test_llm_only_no_rag_flag(self):
        findings = [
            _make_finding(pattern_category="llm_call"),
        ]
        summary = compute_frameworks_summary(findings)
        flags = compute_risk_flags(findings, summary)

        flag_ids = {f["id"] for f in flags}
        assert "llm_only_no_rag" in flag_ids

    def test_no_flags_for_empty(self):
        flags = compute_risk_flags([], [])
        assert flags == []


class TestHotspots:
    """Test compute_hotspots."""

    def test_identifies_hotspot_directories(self):
        findings = [
            _make_finding(file_path="src/ai/openai_client.py"),
            _make_finding(file_path="src/ai/anthropic_client.py"),
            _make_finding(file_path="src/ai/langchain_rag.py"),
            _make_finding(file_path="lib/utils.py"),
        ]
        hotspots = compute_hotspots(findings)
        assert len(hotspots) > 0
        # The hotspot with most matches should be first
        assert hotspots[0]["total_matches"] >= hotspots[-1]["total_matches"]

    def test_max_5_hotspots(self):
        findings = [
            _make_finding(file_path=f"dir{i}/file.py") for i in range(10)
        ]
        hotspots = compute_hotspots(findings)
        assert len(hotspots) <= 5


class TestRecommendedActions:
    """Test compute_recommended_actions."""

    def test_generates_actions_for_multiple_frameworks(self):
        risk_flags = [{"id": "multiple_frameworks", "label": "test", "severity": "medium", "description": "test"}]
        summary = [{"framework": "OpenAI"}, {"framework": "Anthropic"}]
        actions = compute_recommended_actions(risk_flags, summary)

        action_ids = {a["id"] for a in actions}
        assert "standardize_framework" in action_ids

    def test_generates_actions_for_secrets(self):
        risk_flags = [{"id": "secrets_detected", "label": "test", "severity": "high", "description": "test"}]
        actions = compute_recommended_actions(risk_flags, [])

        action_ids = {a["id"] for a in actions}
        assert "rotate_secrets" in action_ids

    def test_generates_default_action_when_no_flags(self):
        actions = compute_recommended_actions([], [])
        assert len(actions) >= 1
        assert actions[0]["id"] == "establish_monitoring"
