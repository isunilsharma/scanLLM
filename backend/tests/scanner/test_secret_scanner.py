"""Tests for the AI-specific secret scanner.

Verifies detection of hardcoded API keys, env var references,
and proper severity classification.
"""

import re
import sys
from pathlib import Path

import pytest
import yaml

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"

sys.path.insert(0, str(BACKEND_DIR))


def _load_signatures() -> dict:
    sig_path = BACKEND_DIR.parent / "ai_signatures.yaml"
    if not sig_path.exists():
        sig_path = BACKEND_DIR / "app" / "scanner" / "signatures" / "ai_signatures.yaml"
    if not sig_path.exists():
        pytest.skip("ai_signatures.yaml not found")
    with open(sig_path) as f:
        return yaml.safe_load(f)


# Patterns for secret detection based on ai_signatures.yaml risk_patterns
OPENAI_KEY_PATTERN = r"(sk-[a-zA-Z0-9]{20,}|sk-proj-[a-zA-Z0-9-_]{20,})"
ANTHROPIC_KEY_PATTERN = r"sk-ant-[a-zA-Z0-9]{10,}"

# Env var reference patterns from signatures
AI_ENV_VARS = [
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "PINECONE_API_KEY",
    "HF_TOKEN", "GOOGLE_API_KEY", "COHERE_API_KEY",
    "MISTRAL_API_KEY", "GROQ_API_KEY",
]


def _scan_secrets(text: str, signatures: dict) -> list[dict]:
    """Scan for hardcoded secrets and env var references."""
    findings = []
    lines = text.splitlines()

    # Get the hardcoded key pattern from signatures
    risk_patterns = signatures.get("risk_patterns", {})
    hardcoded_pattern = risk_patterns.get("hardcoded_api_key", {}).get("pattern", OPENAI_KEY_PATTERN)

    # Collect all env vars from signatures
    all_env_vars = set()
    for section_key in ("providers", "vector_databases", "frameworks", "inference", "mcp"):
        section = signatures.get(section_key, {})
        for _, data in section.items():
            for ev in data.get("env_vars", []):
                all_env_vars.add(ev)

    for line_num, line in enumerate(lines, start=1):
        # Check for hardcoded API keys
        key_match = re.search(hardcoded_pattern, line)
        if key_match:
            # Distinguish: is this an assignment with a value, or just a variable reference?
            is_hardcoded = bool(re.search(r'[=:]\s*["\']?' + re.escape(key_match.group(0)), line))
            # Also treat bare key values as hardcoded
            if not is_hardcoded:
                is_hardcoded = key_match.group(0) == line.strip() or "=" in line

            findings.append({
                "line_number": line_num,
                "line_text": line.strip(),
                "kind": "hardcoded_key" if is_hardcoded else "key_reference",
                "severity": "critical" if is_hardcoded else "medium",
                "pattern": "openai_key",
                "owasp": "LLM07",
            })

        # Check for Anthropic key pattern
        ant_match = re.search(ANTHROPIC_KEY_PATTERN, line)
        if ant_match:
            findings.append({
                "line_number": line_num,
                "line_text": line.strip(),
                "kind": "hardcoded_key",
                "severity": "critical",
                "pattern": "anthropic_key",
                "owasp": "LLM07",
            })

        # Check for env var references
        for ev in all_env_vars:
            if ev in line:
                # Determine if this is a reference (os.getenv) or a hardcoded value
                is_value_assignment = bool(re.search(ev + r'\s*=\s*\S', line))
                findings.append({
                    "line_number": line_num,
                    "line_text": line.strip(),
                    "kind": "env_var_value" if is_value_assignment else "env_var_reference",
                    "severity": "high" if is_value_assignment else "info",
                    "env_var": ev,
                })

    return findings


def _read_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text()


class TestOpenAIKeyPattern:
    """Test OpenAI API key pattern detection."""

    def test_detects_openai_key_pattern(self):
        text = 'api_key = "sk-1234567890abcdef1234567890abcdef1234567890abcdefgh"'
        sigs = _load_signatures()
        findings = _scan_secrets(text, sigs)

        key_findings = [f for f in findings if f["kind"] == "hardcoded_key" and f["pattern"] == "openai_key"]
        assert len(key_findings) > 0, "Should detect sk-... pattern"

    def test_detects_sk_proj_pattern(self):
        text = 'OPENAI_API_KEY=sk-proj-abcdefghijklmnopqrstuvwx'
        sigs = _load_signatures()
        findings = _scan_secrets(text, sigs)

        key_findings = [f for f in findings if f["kind"] == "hardcoded_key"]
        assert len(key_findings) > 0, "Should detect sk-proj-... pattern"

    def test_flags_critical_severity_for_hardcoded(self):
        text = 'api_key = "sk-1234567890abcdef1234567890abcdef1234567890abcdefgh"'
        sigs = _load_signatures()
        findings = _scan_secrets(text, sigs)

        key_findings = [f for f in findings if f["kind"] == "hardcoded_key"]
        assert len(key_findings) > 0
        assert key_findings[0]["severity"] == "critical", "Hardcoded key should be critical severity"


class TestAnthropicKeyPattern:
    """Test Anthropic API key pattern detection."""

    def test_detects_anthropic_key_pattern(self):
        text = 'ANTHROPIC_API_KEY=sk-ant-abc123def456xyz'
        sigs = _load_signatures()
        findings = _scan_secrets(text, sigs)

        ant_findings = [f for f in findings if f.get("pattern") == "anthropic_key"]
        assert len(ant_findings) > 0, "Should detect sk-ant-... pattern"


class TestEnvVarReferences:
    """Test env var reference detection."""

    def test_detects_env_var_references(self):
        text = _read_fixture("sample.env")
        sigs = _load_signatures()
        findings = _scan_secrets(text, sigs)

        env_findings = [f for f in findings if f["kind"] in ("env_var_value", "env_var_reference")]
        env_vars_found = {f.get("env_var") for f in env_findings}

        assert "OPENAI_API_KEY" in env_vars_found
        assert "ANTHROPIC_API_KEY" in env_vars_found
        assert "PINECONE_API_KEY" in env_vars_found

    def test_distinguishes_reference_vs_hardcoded(self):
        """os.getenv('OPENAI_API_KEY') is a reference, not a hardcoded value."""
        sigs = _load_signatures()

        ref_text = 'api_key = os.getenv("OPENAI_API_KEY")'
        ref_findings = _scan_secrets(ref_text, sigs)
        ref_env = [f for f in ref_findings if f["kind"] == "env_var_reference"]
        assert len(ref_env) > 0, "os.getenv should be detected as reference"

        val_text = 'OPENAI_API_KEY=sk-abc123def456ghi789jkl012mno345pqr678stu901vwx234'
        val_findings = _scan_secrets(val_text, sigs)
        val_env = [f for f in val_findings if f["kind"] == "env_var_value"]
        assert len(val_env) > 0, "Assignment should be detected as value"


class TestSecretScannerInFixtures:
    """Test secret detection across fixture files."""

    def test_sample_env_detects_all_ai_keys(self):
        text = _read_fixture("sample.env")
        sigs = _load_signatures()
        findings = _scan_secrets(text, sigs)

        # Should find at least OPENAI, ANTHROPIC, PINECONE, HF keys
        env_vars_found = {f.get("env_var") for f in findings if f.get("env_var")}
        assert len(env_vars_found) >= 4, f"Should find at least 4 AI env vars, found: {env_vars_found}"

    def test_sample_unsafe_detects_hardcoded_key(self):
        text = _read_fixture("sample_unsafe.py")
        sigs = _load_signatures()
        findings = _scan_secrets(text, sigs)

        hardcoded = [f for f in findings if f["kind"] == "hardcoded_key"]
        assert len(hardcoded) > 0, "Should detect hardcoded key in sample_unsafe.py"


class TestEdgeCases:
    """Edge cases."""

    def test_empty_file(self):
        sigs = _load_signatures()
        findings = _scan_secrets("", sigs)
        assert findings == []

    def test_short_sk_prefix_not_matched(self):
        """A short 'sk-' prefix without enough chars should not match."""
        sigs = _load_signatures()
        text = 'key = "sk-short"'
        findings = _scan_secrets(text, sigs)
        key_findings = [f for f in findings if f["kind"] == "hardcoded_key"]
        assert len(key_findings) == 0, "Short sk- prefix should not be flagged"
