"""Tests for the dependency file scanner.

Verifies detection of AI packages in requirements.txt and package.json,
version extraction, and correct exclusion of non-AI packages.
"""

import json
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


def _collect_ai_package_names(signatures: dict) -> set[str]:
    """Build set of known AI package names from signatures."""
    packages = set()
    for section_key in ("providers", "vector_databases", "frameworks", "inference", "mcp"):
        section = signatures.get(section_key, {})
        for key, data in section.items():
            # Python imports often match package names
            for imp in data.get("python", {}).get("imports", []):
                # Take first token (e.g. "from openai import" -> "openai")
                parts = imp.replace("from ", "").split()
                if parts:
                    pkg = parts[0].split(".")[0]
                    packages.add(pkg)
            # JS imports
            for imp in data.get("javascript", {}).get("imports", []):
                # Extract package name from import string
                for quote_char in ("'", '"'):
                    if quote_char in imp:
                        pkg_name = imp.split(quote_char)[1] if quote_char in imp else None
                        if pkg_name:
                            packages.add(pkg_name)
    return packages


def _scan_requirements(text: str, ai_packages: set[str]) -> list[dict]:
    """Scan requirements.txt for AI packages."""
    findings = []
    for line_num, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Parse package==version or package>=version etc.
        match = re.match(r'^([a-zA-Z0-9_-]+)\s*([><=!~]+)?\s*([\d.]+)?', line)
        if not match:
            continue

        pkg_name = match.group(1).lower()
        version = match.group(3)

        # Check if package name (or normalized variant) matches AI packages
        is_ai = False
        normalized = pkg_name.replace("-", "_").replace(".", "_")
        for ai_pkg in ai_packages:
            ai_normalized = ai_pkg.lower().replace("-", "_").replace(".", "_")
            if normalized == ai_normalized or normalized.startswith(ai_normalized):
                is_ai = True
                break

        if is_ai:
            findings.append({
                "package": pkg_name,
                "version": version,
                "line_number": line_num,
                "source": "requirements.txt",
                "is_ai": True,
            })

    return findings


def _scan_package_json(text: str, ai_packages: set[str]) -> list[dict]:
    """Scan package.json for AI packages."""
    findings = []
    data = json.loads(text)

    for dep_section in ("dependencies", "devDependencies"):
        deps = data.get(dep_section, {})
        for pkg_name, version in deps.items():
            is_ai = pkg_name in ai_packages or any(
                ai_pkg in pkg_name for ai_pkg in ai_packages
            )
            if is_ai:
                findings.append({
                    "package": pkg_name,
                    "version": version,
                    "source": "package.json",
                    "section": dep_section,
                    "is_ai": True,
                })

    return findings


def _read_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text()


class TestRequirementsTxt:
    """Tests for requirements.txt scanning."""

    def test_detects_ai_packages_in_requirements(self):
        sigs = _load_signatures()
        ai_packages = _collect_ai_package_names(sigs)
        text = _read_fixture("sample_requirements.txt")
        findings = _scan_requirements(text, ai_packages)

        found_packages = {f["package"] for f in findings}
        assert "openai" in found_packages, "Should detect openai"
        assert "anthropic" in found_packages, "Should detect anthropic"
        assert "langchain" in found_packages, "Should detect langchain"

    def test_detects_chromadb(self):
        sigs = _load_signatures()
        ai_packages = _collect_ai_package_names(sigs)
        text = _read_fixture("sample_requirements.txt")
        findings = _scan_requirements(text, ai_packages)

        found_packages = {f["package"] for f in findings}
        assert "chromadb" in found_packages, "Should detect chromadb"

    def test_detects_transformers(self):
        sigs = _load_signatures()
        ai_packages = _collect_ai_package_names(sigs)
        text = _read_fixture("sample_requirements.txt")
        findings = _scan_requirements(text, ai_packages)

        found_packages = {f["package"] for f in findings}
        assert "transformers" in found_packages, "Should detect transformers"

    def test_ignores_non_ai_packages(self):
        sigs = _load_signatures()
        ai_packages = _collect_ai_package_names(sigs)
        text = _read_fixture("sample_requirements.txt")
        findings = _scan_requirements(text, ai_packages)

        found_packages = {f["package"] for f in findings}
        assert "flask" not in found_packages, "Should NOT detect flask as AI package"
        assert "requests" not in found_packages, "Should NOT detect requests as AI package"

    def test_extracts_version(self):
        sigs = _load_signatures()
        ai_packages = _collect_ai_package_names(sigs)
        text = _read_fixture("sample_requirements.txt")
        findings = _scan_requirements(text, ai_packages)

        openai_finding = next((f for f in findings if f["package"] == "openai"), None)
        assert openai_finding is not None
        assert openai_finding["version"] == "1.12.0", "Should extract version 1.12.0"

    def test_empty_requirements(self):
        sigs = _load_signatures()
        ai_packages = _collect_ai_package_names(sigs)
        findings = _scan_requirements("", ai_packages)
        assert findings == []

    def test_comments_ignored(self):
        sigs = _load_signatures()
        ai_packages = _collect_ai_package_names(sigs)
        text = "# openai==1.0.0\n# This is a comment"
        findings = _scan_requirements(text, ai_packages)
        assert findings == [], "Comments should be ignored"


class TestPackageJson:
    """Tests for package.json scanning."""

    def test_detects_ai_packages_in_package_json(self):
        sigs = _load_signatures()
        ai_packages = _collect_ai_package_names(sigs)
        text = _read_fixture("sample_package.json")
        findings = _scan_package_json(text, ai_packages)

        found_packages = {f["package"] for f in findings}
        assert "openai" in found_packages, "Should detect openai"

    def test_detects_anthropic_sdk(self):
        sigs = _load_signatures()
        ai_packages = _collect_ai_package_names(sigs)
        text = _read_fixture("sample_package.json")
        findings = _scan_package_json(text, ai_packages)

        found_packages = {f["package"] for f in findings}
        assert "@anthropic-ai/sdk" in found_packages, "Should detect @anthropic-ai/sdk"

    def test_detects_mcp_sdk(self):
        sigs = _load_signatures()
        ai_packages = _collect_ai_package_names(sigs)
        text = _read_fixture("sample_package.json")
        findings = _scan_package_json(text, ai_packages)

        found_packages = {f["package"] for f in findings}
        assert "@modelcontextprotocol/sdk" in found_packages, "Should detect @modelcontextprotocol/sdk"

    def test_ignores_non_ai_packages(self):
        sigs = _load_signatures()
        ai_packages = _collect_ai_package_names(sigs)
        text = _read_fixture("sample_package.json")
        findings = _scan_package_json(text, ai_packages)

        found_packages = {f["package"] for f in findings}
        assert "express" not in found_packages, "Should NOT detect express as AI"
        assert "react" not in found_packages, "Should NOT detect react as AI"

    def test_extracts_version(self):
        sigs = _load_signatures()
        ai_packages = _collect_ai_package_names(sigs)
        text = _read_fixture("sample_package.json")
        findings = _scan_package_json(text, ai_packages)

        openai_finding = next((f for f in findings if f["package"] == "openai"), None)
        assert openai_finding is not None
        assert openai_finding["version"] == "^4.47.1"
