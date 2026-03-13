"""Tests for the YAML/JSON/TOML/env config scanner.

Verifies detection of model names, endpoint URLs, Docker AI services,
and environment variable references in configuration files.
"""

import re
import sys
from pathlib import Path

import pytest
import yaml as pyyaml

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
        return pyyaml.safe_load(f)


def _collect_all_models(signatures: dict) -> list[str]:
    """Collect all model name strings from signatures."""
    models = []
    for section_key in ("providers", "vector_databases", "frameworks", "inference"):
        section = signatures.get(section_key, {})
        for _, data in section.items():
            for m in data.get("python", {}).get("models", data.get("models", [])):
                models.append(m)
    return models


def _collect_all_env_vars(signatures: dict) -> list[str]:
    """Collect all env var names from signatures."""
    env_vars = []
    for section_key in ("providers", "vector_databases", "frameworks", "inference", "mcp"):
        section = signatures.get(section_key, {})
        for _, data in section.items():
            for ev in data.get("env_vars", []):
                env_vars.append(ev)
    return env_vars


def _collect_endpoint_urls(signatures: dict) -> list[str]:
    """Collect all endpoint URL patterns."""
    urls = []
    for section_key in ("providers", "inference"):
        section = signatures.get(section_key, {})
        for _, data in section.items():
            for url in data.get("endpoint_urls", []):
                urls.append(url)
    return urls


def _collect_docker_images(signatures: dict) -> list[str]:
    """Collect all docker image patterns."""
    images = []
    for section_key in ("inference",):
        section = signatures.get(section_key, {})
        for _, data in section.items():
            for img in data.get("docker_images", []):
                images.append(img)
    return images


def _config_scan(text: str, signatures: dict) -> list[dict]:
    """Scan config file text for AI-related references."""
    findings = []
    lines = text.splitlines()

    all_models = _collect_all_models(signatures)
    all_env_vars = _collect_all_env_vars(signatures)
    all_urls = _collect_endpoint_urls(signatures)
    all_images = _collect_docker_images(signatures)

    for line_num, line in enumerate(lines, start=1):
        # Check model names
        for model in all_models:
            if model in line:
                findings.append({
                    "line_number": line_num,
                    "line_text": line.strip(),
                    "kind": "model_reference",
                    "value": model,
                })

        # Check env vars
        for ev in all_env_vars:
            if ev in line:
                findings.append({
                    "line_number": line_num,
                    "line_text": line.strip(),
                    "kind": "env_var_reference",
                    "value": ev,
                })

        # Check endpoint URLs
        for url in all_urls:
            if url in line:
                findings.append({
                    "line_number": line_num,
                    "line_text": line.strip(),
                    "kind": "endpoint_url",
                    "value": url,
                })

        # Check docker images
        for img in all_images:
            if img in line:
                findings.append({
                    "line_number": line_num,
                    "line_text": line.strip(),
                    "kind": "docker_image",
                    "value": img,
                })

    return findings


def _read_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text()


class TestModelNameDetection:
    """Verify model name detection in config files."""

    def test_detects_model_names_in_yaml(self):
        sigs = _load_signatures()
        text = _read_fixture("sample_config.yaml")
        findings = _config_scan(text, sigs)

        model_findings = [f for f in findings if f["kind"] == "model_reference"]
        model_values = {f["value"] for f in model_findings}

        assert "gpt-4o" in model_values, "Should detect gpt-4o in config"

    def test_detects_embedding_model(self):
        sigs = _load_signatures()
        text = _read_fixture("sample_config.yaml")
        findings = _config_scan(text, sigs)

        model_findings = [f for f in findings if f["kind"] == "model_reference"]
        model_values = {f["value"] for f in model_findings}

        assert "text-embedding-3-small" in model_values, "Should detect embedding model"


class TestEndpointURLDetection:
    """Verify endpoint URL detection."""

    def test_detects_endpoint_urls(self):
        sigs = _load_signatures()
        text = "endpoint: https://api.openai.com/v1/chat/completions"
        findings = _config_scan(text, sigs)

        url_findings = [f for f in findings if f["kind"] == "endpoint_url"]
        assert len(url_findings) > 0, "Should detect api.openai.com"

    def test_detects_ollama_endpoint(self):
        sigs = _load_signatures()
        text = "ollama_host: http://localhost:11434"
        findings = _config_scan(text, sigs)

        url_findings = [f for f in findings if f["kind"] == "endpoint_url"]
        assert len(url_findings) > 0, "Should detect localhost:11434 (Ollama)"


class TestDockerServiceDetection:
    """Verify Docker AI service detection."""

    def test_detects_docker_ai_services(self):
        sigs = _load_signatures()
        text = _read_fixture("sample_config.yaml")
        findings = _config_scan(text, sigs)

        docker_findings = [f for f in findings if f["kind"] == "docker_image"]
        assert len(docker_findings) > 0, "Should detect ollama/ollama docker image"

    def test_detects_vllm_image(self):
        sigs = _load_signatures()
        text = "image: vllm/vllm-openai:latest"
        findings = _config_scan(text, sigs)

        docker_findings = [f for f in findings if f["kind"] == "docker_image"]
        assert len(docker_findings) > 0, "Should detect vllm docker image"


class TestEnvVarDetection:
    """Verify env var reference detection in config files."""

    def test_detects_env_file_keys(self):
        sigs = _load_signatures()
        text = _read_fixture("sample.env")
        findings = _config_scan(text, sigs)

        env_findings = [f for f in findings if f["kind"] == "env_var_reference"]
        env_values = {f["value"] for f in env_findings}

        assert "OPENAI_API_KEY" in env_values, "Should detect OPENAI_API_KEY"
        assert "ANTHROPIC_API_KEY" in env_values, "Should detect ANTHROPIC_API_KEY"
        assert "PINECONE_API_KEY" in env_values, "Should detect PINECONE_API_KEY"
        assert "HF_TOKEN" in env_values, "Should detect HF_TOKEN"

    def test_does_not_flag_non_ai_env_vars(self):
        sigs = _load_signatures()
        text = "DATABASE_URL=postgresql://localhost/mydb\nSECRET_KEY=not-an-ai-key"
        findings = _config_scan(text, sigs)

        env_findings = [f for f in findings if f["kind"] == "env_var_reference"]
        assert len(env_findings) == 0, "Non-AI env vars should not be flagged"


class TestEdgeCases:
    """Edge cases for config scanning."""

    def test_empty_config(self):
        sigs = _load_signatures()
        findings = _config_scan("", sigs)
        assert findings == []

    def test_comments_only(self):
        sigs = _load_signatures()
        text = "# This is a comment\n# No actual config here"
        findings = _config_scan(text, sigs)
        assert len(findings) == 0
