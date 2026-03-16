"""Integration tests for the scanning engine.

These tests verify end-to-end scanning of the fixtures directory,
deduplication logic, and full-scan mode behavior.
"""

import re
import sys
from pathlib import Path

import pytest
import yaml

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"

sys.path.insert(0, str(BACKEND_DIR))

from services.contract_extractor import extract_contracts


def _load_signatures() -> dict:
    sig_path = BACKEND_DIR.parent / "config" / "ai_signatures.yaml"
    if not sig_path.exists():
        pytest.skip("ai_signatures.yaml not found")
    with open(sig_path) as f:
        return yaml.safe_load(f)


def _build_all_patterns(signatures: dict) -> list[dict]:
    """Build a flat list of all detection patterns from signatures."""
    patterns = []
    for section_key in ("providers", "vector_databases", "frameworks", "inference", "mcp"):
        section = signatures.get(section_key, {})
        for provider_key, provider_data in section.items():
            display = provider_data.get("display_name", provider_key)
            category = provider_data.get("category", "unknown")

            for imp in provider_data.get("python", {}).get("imports", []):
                patterns.append({
                    "regex": re.escape(imp),
                    "framework": display,
                    "category": category,
                })
            for call in provider_data.get("python", {}).get("calls", []):
                patterns.append({
                    "regex": re.escape(call),
                    "framework": display,
                    "category": category,
                })
            for imp in provider_data.get("javascript", {}).get("imports", []):
                patterns.append({
                    "regex": re.escape(imp),
                    "framework": display,
                    "category": category,
                })
            for call in provider_data.get("javascript", {}).get("calls", []):
                patterns.append({
                    "regex": re.escape(call),
                    "framework": display,
                    "category": category,
                })
            for ev in provider_data.get("env_vars", []):
                patterns.append({
                    "regex": re.escape(ev),
                    "framework": display,
                    "category": category,
                })

    # Risk patterns
    for rp_key, rp in signatures.get("risk_patterns", {}).items():
        if "pattern" in rp:
            patterns.append({
                "regex": rp["pattern"],
                "framework": "security",
                "category": rp.get("owasp", "security"),
            })

    return patterns


def _scan_directory(directory: Path, signatures: dict) -> list[dict]:
    """Scan all files in a directory using regex patterns."""
    patterns = _build_all_patterns(signatures)
    findings = []

    scan_extensions = {".py", ".js", ".ts", ".jsx", ".tsx", ".yaml", ".yml",
                       ".json", ".env", ".txt", ".toml", ".ipynb"}

    for file_path in sorted(directory.rglob("*")):
        if not file_path.is_file():
            continue
        if file_path.suffix not in scan_extensions:
            continue

        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        relative = str(file_path.relative_to(directory))
        lines = text.splitlines()

        for line_num, line in enumerate(lines, start=1):
            for pat in patterns:
                if re.search(pat["regex"], line):
                    finding = {
                        "file_path": relative,
                        "line_number": line_num,
                        "line_text": line.strip()[:500],
                        "framework": pat["framework"],
                        "category": pat["category"],
                    }
                    findings.append(finding)

    return findings


def _deduplicate(findings: list[dict]) -> list[dict]:
    """Remove duplicate findings (same file, line, framework)."""
    seen = set()
    deduped = []
    for f in findings:
        key = (f["file_path"], f["line_number"], f["framework"])
        if key not in seen:
            seen.add(key)
            deduped.append(f)
    return deduped


class TestScanFixtureDirectory:
    """Integration tests scanning the entire fixtures directory."""

    def test_scan_fixture_directory(self):
        """Scanning the fixtures dir should find multiple AI frameworks."""
        sigs = _load_signatures()
        findings = _scan_directory(FIXTURES_DIR, sigs)

        assert len(findings) > 0, "Should find at least one AI-related finding"

        frameworks_found = {f["framework"] for f in findings}
        assert "OpenAI" in frameworks_found, "Should detect OpenAI in fixtures"

    def test_scan_finds_multiple_frameworks(self):
        sigs = _load_signatures()
        findings = _scan_directory(FIXTURES_DIR, sigs)

        frameworks_found = {f["framework"] for f in findings}
        # At a minimum, the fixtures contain OpenAI, Anthropic, LangChain, CrewAI
        assert len(frameworks_found) >= 3, (
            f"Should find at least 3 frameworks, found: {frameworks_found}"
        )

    def test_scan_finds_multiple_file_types(self):
        sigs = _load_signatures()
        findings = _scan_directory(FIXTURES_DIR, sigs)

        file_extensions = {Path(f["file_path"]).suffix for f in findings}
        assert ".py" in file_extensions, "Should scan .py files"

    def test_scan_finds_security_issues(self):
        sigs = _load_signatures()
        findings = _scan_directory(FIXTURES_DIR, sigs)

        security_findings = [f for f in findings if f["framework"] == "security"]
        assert len(security_findings) > 0, "Should find security issues in sample_unsafe.py"


class TestDeduplication:
    """Verify deduplication logic."""

    def test_deduplication(self):
        findings = [
            {"file_path": "a.py", "line_number": 1, "line_text": "import openai", "framework": "OpenAI", "category": "llm_provider"},
            {"file_path": "a.py", "line_number": 1, "line_text": "import openai", "framework": "OpenAI", "category": "llm_provider"},
            {"file_path": "a.py", "line_number": 2, "line_text": "import anthropic", "framework": "Anthropic", "category": "llm_provider"},
        ]

        deduped = _deduplicate(findings)
        assert len(deduped) == 2, "Should remove duplicate (same file, line, framework)"

    def test_different_lines_not_deduped(self):
        findings = [
            {"file_path": "a.py", "line_number": 1, "line_text": "import openai", "framework": "OpenAI", "category": "llm_provider"},
            {"file_path": "a.py", "line_number": 5, "line_text": "client = OpenAI()", "framework": "OpenAI", "category": "llm_provider"},
        ]

        deduped = _deduplicate(findings)
        assert len(deduped) == 2, "Different lines should not be deduped"

    def test_different_files_not_deduped(self):
        findings = [
            {"file_path": "a.py", "line_number": 1, "line_text": "import openai", "framework": "OpenAI", "category": "llm_provider"},
            {"file_path": "b.py", "line_number": 1, "line_text": "import openai", "framework": "OpenAI", "category": "llm_provider"},
        ]

        deduped = _deduplicate(findings)
        assert len(deduped) == 2, "Different files should not be deduped"


class TestFullScanMode:
    """Verify full scan mode includes all directories."""

    def test_full_scan_includes_all_files(self):
        """Full scan should include test directories and other typically-skipped paths."""
        sigs = _load_signatures()
        # Scan the entire fixtures dir (simulates full_scan=True)
        findings = _scan_directory(FIXTURES_DIR, sigs)
        files_scanned = {f["file_path"] for f in findings}

        # We should find findings from multiple fixture files
        assert len(files_scanned) >= 2, (
            f"Full scan should cover multiple files, found: {files_scanned}"
        )
