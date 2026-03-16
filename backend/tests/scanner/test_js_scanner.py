"""Tests for the JS/TS regex-based scanner.

Verifies detection of JavaScript/TypeScript AI SDK imports and calls
in sample fixture files.
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
    sig_path = BACKEND_DIR.parent / "config" / "ai_signatures.yaml"
    if not sig_path.exists():
        pytest.skip("ai_signatures.yaml not found")
    with open(sig_path) as f:
        return yaml.safe_load(f)


def _js_scan(text: str, signatures: dict) -> list[dict]:
    """Regex scan against JavaScript/TypeScript patterns from ai_signatures."""
    findings = []
    lines = text.splitlines()

    patterns: list[dict] = []
    for section_key in ("providers", "frameworks", "mcp"):
        section = signatures.get(section_key, {})
        for provider_key, provider_data in section.items():
            display = provider_data.get("display_name", provider_key)
            category = provider_data.get("category", "unknown")

            for imp in provider_data.get("javascript", {}).get("imports", []):
                patterns.append({
                    "regex": re.escape(imp),
                    "framework": display,
                    "category": category,
                    "kind": "import",
                })

            for call in provider_data.get("javascript", {}).get("calls", []):
                patterns.append({
                    "regex": re.escape(call),
                    "framework": display,
                    "category": category,
                    "kind": "call",
                })

    for line_num, line in enumerate(lines, start=1):
        for pat in patterns:
            if re.search(pat["regex"], line):
                findings.append({
                    "file_path": "test_file.ts",
                    "line_number": line_num,
                    "line_text": line.strip(),
                    "framework": pat["framework"],
                    "category": pat["category"],
                    "kind": pat["kind"],
                })
    return findings


def _read_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text()


class TestJSOpenAI:
    """Verify OpenAI detection in JS/TS files."""

    def test_detects_openai_import(self):
        sigs = _load_signatures()
        text = _read_fixture("sample_js.ts")
        findings = _js_scan(text, sigs)

        openai_imports = [
            f for f in findings
            if f["framework"] == "OpenAI" and f["kind"] == "import"
        ]
        assert len(openai_imports) > 0, "Should detect import from 'openai'"

    def test_detects_new_openai_client(self):
        sigs = _load_signatures()
        text = _read_fixture("sample_js.ts")
        findings = _js_scan(text, sigs)

        new_openai = [
            f for f in findings
            if "new OpenAI" in f["line_text"]
        ]
        assert len(new_openai) > 0, "Should detect new OpenAI()"


class TestJSAnthropic:
    """Verify Anthropic detection in JS/TS files."""

    def test_detects_anthropic_import(self):
        sigs = _load_signatures()
        text = _read_fixture("sample_js.ts")
        findings = _js_scan(text, sigs)

        anthropic_imports = [
            f for f in findings
            if f["framework"] == "Anthropic" and f["kind"] == "import"
        ]
        assert len(anthropic_imports) > 0, "Should detect import from '@anthropic-ai/sdk'"


class TestVercelAISDK:
    """Verify Vercel AI SDK detection."""

    def test_detects_vercel_ai_sdk(self):
        sigs = _load_signatures()
        text = _read_fixture("sample_js.ts")
        findings = _js_scan(text, sigs)

        ai_sdk_findings = [
            f for f in findings
            if f["framework"] == "Vercel AI SDK"
        ]
        assert len(ai_sdk_findings) > 0, "Should detect Vercel AI SDK imports/calls"

    def test_detects_generate_text_call(self):
        sigs = _load_signatures()
        text = _read_fixture("sample_js.ts")
        findings = _js_scan(text, sigs)

        gen_text = [f for f in findings if "generateText" in f["line_text"]]
        assert len(gen_text) > 0, "Should detect generateText call"


class TestLangChainJS:
    """Verify LangChain JS detection."""

    def test_detects_langchain_js(self):
        sigs = _load_signatures()
        # Use the fixture from conftest that includes @langchain/openai
        text = """\
import { ChatOpenAI } from '@langchain/openai';
import { ChatAnthropic } from '@langchain/anthropic';
"""
        findings = _js_scan(text, sigs)

        lc_findings = [f for f in findings if f["framework"] == "LangChain"]
        assert len(lc_findings) > 0, "Should detect @langchain/openai import"


class TestMCPSDK:
    """Verify MCP SDK detection in JS."""

    def test_detects_mcp_sdk(self):
        sigs = _load_signatures()
        text = """\
import { McpServer } from '@modelcontextprotocol/sdk';
"""
        findings = _js_scan(text, sigs)

        mcp_findings = [f for f in findings if f["framework"] == "MCP Server"]
        assert len(mcp_findings) > 0, "Should detect @modelcontextprotocol/sdk import"


class TestEdgeCases:
    """Edge cases for JS scanning."""

    def test_empty_file(self):
        sigs = _load_signatures()
        findings = _js_scan("", sigs)
        assert findings == []

    def test_no_ai_code(self):
        sigs = _load_signatures()
        text = """\
import express from 'express';
const app = express();
app.listen(3000);
"""
        findings = _js_scan(text, sigs)
        assert len(findings) == 0, "Non-AI JS code should produce no findings"
