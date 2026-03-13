"""
Configuration file scanner for detecting AI/LLM references in YAML, JSON,
TOML, .env, Dockerfile, and docker-compose files.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ── Model name patterns ──────────────────────────────────────────────────────

_MODEL_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bgpt-4o(?:-mini)?\b"), "openai"),
    (re.compile(r"\bgpt-4(?:-turbo)?\b"), "openai"),
    (re.compile(r"\bgpt-3\.5-turbo\b"), "openai"),
    (re.compile(r"\bo[134]-(?:mini|pro)\b"), "openai"),
    (re.compile(r"\bclaude-(?:opus|sonnet|haiku)[-\w]*\b"), "anthropic"),
    (re.compile(r"\bclaude-3(?:\.5)?-(?:opus|sonnet|haiku)\b"), "anthropic"),
    (re.compile(r"\bgemini-[\w.-]+\b"), "google_ai"),
    (re.compile(r"\bllama-?[23][-\w]*\b", re.IGNORECASE), "meta"),
    (re.compile(r"\bmistral-(?:large|medium|small|nemo)\b"), "mistral"),
    (re.compile(r"\bcodestral\b"), "mistral"),
    (re.compile(r"\bcommand-r(?:-plus)?\b"), "cohere"),
    (re.compile(r"\bdeepseek-(?:chat|reasoner|coder)\b"), "deepseek"),
    (re.compile(r"\btext-embedding-(?:3-(?:small|large)|ada-002)\b"), "openai"),
    (re.compile(r"\bdall-e-3\b"), "openai"),
    (re.compile(r"\bwhisper-1\b"), "openai"),
]

# ── Endpoint URL patterns ────────────────────────────────────────────────────

_ENDPOINT_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"api\.openai\.com"), "openai"),
    (re.compile(r"api\.anthropic\.com"), "anthropic"),
    (re.compile(r"generativelanguage\.googleapis\.com"), "google_ai"),
    (re.compile(r"\.openai\.azure\.com"), "azure_openai"),
    (re.compile(r"api\.deepseek\.com"), "deepseek"),
    (re.compile(r"api\.mistral\.ai"), "mistral"),
    (re.compile(r"api\.cohere\.ai"), "cohere"),
    (re.compile(r"api\.groq\.com"), "groq"),
    (re.compile(r"api\.together\.xyz"), "together_ai"),
    (re.compile(r"localhost:11434|127\.0\.0\.1:11434"), "ollama"),
    (re.compile(r"localhost:8080"), "tgi"),
]

# ── Docker image patterns ────────────────────────────────────────────────────

_DOCKER_AI_IMAGES: dict[str, tuple[str, str]] = {
    "ollama/ollama": ("ollama", "Ollama"),
    "vllm/vllm-openai": ("vllm", "vLLM"),
    "ghcr.io/huggingface/text-generation-inference": ("tgi", "Text Generation Inference"),
    "chromadb/chroma": ("chromadb", "ChromaDB"),
    "qdrant/qdrant": ("qdrant", "Qdrant"),
    "semitechnologies/weaviate": ("weaviate", "Weaviate"),
    "milvusdb/milvus": ("milvus", "Milvus"),
}

# ── MCP config file names ────────────────────────────────────────────────────

_MCP_CONFIG_NAMES = frozenset({
    "claude_desktop_config.json",
    "mcp.json",
})

# ── AI-related env var prefixes ──────────────────────────────────────────────

_AI_ENV_PREFIXES = (
    "OPENAI_", "ANTHROPIC_", "GOOGLE_API_", "GOOGLE_CLOUD_",
    "AZURE_OPENAI_", "AWS_BEDROCK_", "PINECONE_", "QDRANT_",
    "WEAVIATE_", "MILVUS_", "HF_", "HUGGING_FACE_",
    "COHERE_", "MISTRAL_", "GROQ_", "DEEPSEEK_",
    "TOGETHER_", "LANGCHAIN_", "OLLAMA_",
)


def _make_finding(
    *,
    file_path: str,
    line_number: int,
    line_text: str = "",
    framework: str = "",
    pattern_name: str = "",
    pattern_category: str = "",
    pattern_severity: str = "info",
    pattern_description: str = "",
    snippet: str = "",
    model_name: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    is_streaming: bool = False,
    has_tools: bool = False,
    component_type: str = "",
    provider: str = "",
    owasp_id: str | None = None,
) -> dict[str, Any]:
    return {
        "file_path": file_path,
        "line_number": line_number,
        "line_text": line_text,
        "framework": framework,
        "pattern_name": pattern_name,
        "pattern_category": pattern_category,
        "pattern_severity": pattern_severity,
        "pattern_description": pattern_description,
        "snippet": snippet,
        "model_name": model_name,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "is_streaming": is_streaming,
        "has_tools": has_tools,
        "component_type": component_type,
        "provider": provider,
        "owasp_id": owasp_id,
    }


def _get_snippet(lines: list[str], lineno: int, context: int = 2) -> str:
    start = max(0, lineno - 1 - context)
    end = min(len(lines), lineno + context)
    return "\n".join(lines[start:end])


def _safe_line(lines: list[str], lineno: int) -> str:
    if 1 <= lineno <= len(lines):
        return lines[lineno - 1].rstrip()
    return ""


class ConfigScanner:
    """Scan configuration files (YAML, JSON, TOML, .env, Dockerfile, docker-compose)."""

    def scan_file(
        self,
        file_path: Path,
        relative_path: str,
        signatures: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Scan a single config file and return findings."""
        try:
            source = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            logger.warning("Failed to read %s: %s", file_path, exc)
            return []

        name = file_path.name.lower()
        suffix = file_path.suffix.lower()
        lines = source.splitlines()
        findings: list[dict[str, Any]] = []

        # Route to appropriate parser
        if name.startswith(".env"):
            self._scan_env(lines, relative_path, findings)
        elif suffix in (".yaml", ".yml"):
            self._scan_yaml(source, lines, relative_path, findings)
        elif suffix == ".json":
            self._scan_json(source, lines, relative_path, findings)
        elif suffix == ".toml":
            self._scan_toml(source, lines, relative_path, findings)
        elif name in ("dockerfile", "docker-compose.yml", "docker-compose.yaml",
                       "compose.yml", "compose.yaml"):
            self._scan_docker(lines, relative_path, findings)

        # Always do line-level model/endpoint scanning on all config files
        self._scan_lines_for_models_and_endpoints(lines, relative_path, findings)

        # Check if this is an MCP config file
        if file_path.name in _MCP_CONFIG_NAMES or ".cursor/mcp.json" in relative_path:
            self._scan_mcp_config(source, lines, relative_path, findings)

        # Check for GitHub Actions AI usage
        if ".github/workflows" in relative_path and suffix in (".yaml", ".yml"):
            self._scan_github_actions(lines, relative_path, findings)

        return findings

    # ── YAML parsing ─────────────────────────────────────────────────

    def _scan_yaml(
        self,
        source: str,
        lines: list[str],
        relative_path: str,
        findings: list[dict[str, Any]],
    ) -> None:
        try:
            import yaml
            docs = list(yaml.safe_load_all(source))
        except Exception as exc:
            logger.debug("YAML parse error in %s: %s", relative_path, exc)
            return

        for doc in docs:
            if isinstance(doc, dict):
                self._walk_dict(doc, lines, relative_path, findings, path_prefix="")

    # ── JSON parsing ─────────────────────────────────────────────────

    def _scan_json(
        self,
        source: str,
        lines: list[str],
        relative_path: str,
        findings: list[dict[str, Any]],
    ) -> None:
        try:
            data = json.loads(source)
        except json.JSONDecodeError as exc:
            logger.debug("JSON parse error in %s: %s", relative_path, exc)
            return

        if isinstance(data, dict):
            self._walk_dict(data, lines, relative_path, findings, path_prefix="")
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    self._walk_dict(item, lines, relative_path, findings, path_prefix=f"[{i}]")

    # ── TOML parsing ─────────────────────────────────────────────────

    def _scan_toml(
        self,
        source: str,
        lines: list[str],
        relative_path: str,
        findings: list[dict[str, Any]],
    ) -> None:
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib  # type: ignore[no-redef]
            except ImportError:
                logger.debug("No TOML parser available for %s", relative_path)
                return
        try:
            data = tomllib.loads(source)
        except Exception as exc:
            logger.debug("TOML parse error in %s: %s", relative_path, exc)
            return

        if isinstance(data, dict):
            self._walk_dict(data, lines, relative_path, findings, path_prefix="")

    # ── .env file scanning ───────────────────────────────────────────

    def _scan_env(
        self,
        lines: list[str],
        relative_path: str,
        findings: list[dict[str, Any]],
    ) -> None:
        for i, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            parts = stripped.split("=", 1)
            key = parts[0].strip()
            has_value = len(parts) > 1 and len(parts[1].strip().strip("'\"")) > 0
            if any(key.startswith(prefix) for prefix in _AI_ENV_PREFIXES):
                findings.append(_make_finding(
                    file_path=relative_path,
                    line_number=i,
                    line_text=stripped[:500],
                    framework="config",
                    pattern_name=f"env_var:{key}",
                    pattern_category="secrets" if has_value else "config_reference",
                    pattern_severity="high" if has_value else "info",
                    pattern_description=(
                        f"AI environment variable '{key}' "
                        + ("with hardcoded value" if has_value else "referenced")
                    ),
                    snippet=_get_snippet(lines, i),
                    component_type="secret" if has_value else "config_reference",
                    provider=self._env_var_to_provider(key),
                    owasp_id="LLM07" if has_value else None,
                ))

    # ── Docker / docker-compose scanning ─────────────────────────────

    def _scan_docker(
        self,
        lines: list[str],
        relative_path: str,
        findings: list[dict[str, Any]],
    ) -> None:
        for i, line in enumerate(lines, start=1):
            for image, (prov, display) in _DOCKER_AI_IMAGES.items():
                if image in line:
                    findings.append(_make_finding(
                        file_path=relative_path,
                        line_number=i,
                        line_text=line.rstrip(),
                        framework=display,
                        pattern_name=f"docker:{image}",
                        pattern_category="infrastructure",
                        pattern_severity="info",
                        pattern_description=f"Docker AI service '{display}' ({image}) detected",
                        snippet=_get_snippet(lines, i),
                        component_type="inference_server",
                        provider=prov,
                    ))

    # ── Recursive dict walker ────────────────────────────────────────

    def _walk_dict(
        self,
        data: dict[str, Any],
        lines: list[str],
        relative_path: str,
        findings: list[dict[str, Any]],
        path_prefix: str,
    ) -> None:
        """Walk a parsed dict recursively looking for model names, URLs, etc."""
        for key, value in data.items():
            current_path = f"{path_prefix}.{key}" if path_prefix else key

            if isinstance(value, str):
                self._check_string_value(
                    key, value, lines, relative_path, findings, current_path,
                )
            elif isinstance(value, dict):
                self._walk_dict(value, lines, relative_path, findings, current_path)
            elif isinstance(value, list):
                for idx_val, item in enumerate(value):
                    if isinstance(item, dict):
                        self._walk_dict(item, lines, relative_path, findings,
                                        f"{current_path}[{idx_val}]")
                    elif isinstance(item, str):
                        self._check_string_value(
                            key, item, lines, relative_path, findings, current_path,
                        )

    def _check_string_value(
        self,
        key: str,
        value: str,
        lines: list[str],
        relative_path: str,
        findings: list[dict[str, Any]],
        config_path: str,
    ) -> None:
        """Check a string value for model names or endpoint URLs."""
        lineno = self._find_line_for_value(lines, value)

        # Model names
        for pat, provider in _MODEL_PATTERNS:
            m = pat.search(value)
            if m:
                model_name = m.group(0)
                findings.append(_make_finding(
                    file_path=relative_path,
                    line_number=lineno,
                    line_text=_safe_line(lines, lineno),
                    pattern_name=f"config_model:{model_name}",
                    pattern_category="model_reference",
                    pattern_severity="info",
                    pattern_description=f"Model '{model_name}' referenced in config at '{config_path}'",
                    snippet=_get_snippet(lines, lineno) if lineno else "",
                    model_name=model_name,
                    component_type="config_reference",
                    provider=provider,
                ))
                break

        # Endpoint URLs
        for pat, provider in _ENDPOINT_PATTERNS:
            if pat.search(value):
                findings.append(_make_finding(
                    file_path=relative_path,
                    line_number=lineno,
                    line_text=_safe_line(lines, lineno),
                    pattern_name=f"config_endpoint:{provider}",
                    pattern_category="endpoint_reference",
                    pattern_severity="info",
                    pattern_description=f"AI endpoint URL for {provider} found in config at '{config_path}'",
                    snippet=_get_snippet(lines, lineno) if lineno else "",
                    component_type="config_reference",
                    provider=provider,
                ))
                break

    # ── Line-level model and endpoint scanning ───────────────────────

    def _scan_lines_for_models_and_endpoints(
        self,
        lines: list[str],
        relative_path: str,
        findings: list[dict[str, Any]],
    ) -> None:
        """Fallback line-by-line scan for model names and endpoint URLs."""
        found_lines: set[int] = {f["line_number"] for f in findings}

        for i, line in enumerate(lines, start=1):
            if i in found_lines:
                continue
            for pat, provider in _MODEL_PATTERNS:
                m = pat.search(line)
                if m:
                    findings.append(_make_finding(
                        file_path=relative_path,
                        line_number=i,
                        line_text=line.rstrip(),
                        pattern_name=f"config_model:{m.group(0)}",
                        pattern_category="model_reference",
                        pattern_severity="info",
                        pattern_description=f"Model '{m.group(0)}' found in config",
                        snippet=_get_snippet(lines, i),
                        model_name=m.group(0),
                        component_type="config_reference",
                        provider=provider,
                    ))
                    found_lines.add(i)
                    break
            if i not in found_lines:
                for pat, provider in _ENDPOINT_PATTERNS:
                    if pat.search(line):
                        findings.append(_make_finding(
                            file_path=relative_path,
                            line_number=i,
                            line_text=line.rstrip(),
                            pattern_name=f"config_endpoint:{provider}",
                            pattern_category="endpoint_reference",
                            pattern_severity="info",
                            pattern_description=f"AI endpoint URL for {provider} detected",
                            snippet=_get_snippet(lines, i),
                            component_type="config_reference",
                            provider=provider,
                        ))
                        found_lines.add(i)
                        break

    # ── MCP config scanning ──────────────────────────────────────────

    def _scan_mcp_config(
        self,
        source: str,
        lines: list[str],
        relative_path: str,
        findings: list[dict[str, Any]],
    ) -> None:
        try:
            data = json.loads(source)
        except json.JSONDecodeError:
            return

        servers = data.get("mcpServers", data.get("servers", {}))
        if not isinstance(servers, dict):
            return

        for server_name, config in servers.items():
            lineno = self._find_line_for_value(lines, server_name)
            transport = ""
            if isinstance(config, dict):
                transport = config.get("transport", config.get("command", ""))

            findings.append(_make_finding(
                file_path=relative_path,
                line_number=lineno,
                line_text=_safe_line(lines, lineno),
                framework="MCP Server",
                pattern_name=f"mcp_config:{server_name}",
                pattern_category="mcp_config",
                pattern_severity="medium" if transport == "stdio" else "info",
                pattern_description=(
                    f"MCP server '{server_name}' configured"
                    + (" with stdio transport — verify server source is trusted"
                       if transport == "stdio" else "")
                ),
                snippet=_get_snippet(lines, lineno) if lineno else "",
                component_type="mcp_server",
                provider="mcp_server",
                owasp_id="LLM06" if transport == "stdio" else None,
                has_tools=True,
            ))

    # ── GitHub Actions scanning ──────────────────────────────────────

    def _scan_github_actions(
        self,
        lines: list[str],
        relative_path: str,
        findings: list[dict[str, Any]],
    ) -> None:
        """Check GitHub Actions workflows for AI-related steps."""
        ai_action_patterns = [
            (re.compile(r"openai/"), "OpenAI"),
            (re.compile(r"anthropics?/"), "Anthropic"),
            (re.compile(r"langchain"), "LangChain"),
        ]
        ai_env_pattern = re.compile(
            r"(OPENAI_API_KEY|ANTHROPIC_API_KEY|GOOGLE_API_KEY|HF_TOKEN)",
        )
        for i, line in enumerate(lines, start=1):
            for pat, name in ai_action_patterns:
                if pat.search(line):
                    findings.append(_make_finding(
                        file_path=relative_path,
                        line_number=i,
                        line_text=line.rstrip(),
                        framework=name,
                        pattern_name=f"github_action:{name.lower()}",
                        pattern_category="ci_cd",
                        pattern_severity="info",
                        pattern_description=f"GitHub Actions step referencing {name} detected",
                        snippet=_get_snippet(lines, i),
                        component_type="config_reference",
                        provider=name.lower(),
                    ))
            m = ai_env_pattern.search(line)
            if m:
                findings.append(_make_finding(
                    file_path=relative_path,
                    line_number=i,
                    line_text=line.rstrip(),
                    pattern_name=f"github_action_env:{m.group(1)}",
                    pattern_category="ci_cd",
                    pattern_severity="info",
                    pattern_description=f"AI env var '{m.group(1)}' referenced in GitHub Actions",
                    snippet=_get_snippet(lines, i),
                    component_type="config_reference",
                    provider="",
                ))

    # ── Utilities ────────────────────────────────────────────────────

    @staticmethod
    def _find_line_for_value(lines: list[str], value: str) -> int:
        """Best-effort line number lookup for a string value in the source."""
        for i, line in enumerate(lines, start=1):
            if value in line:
                return i
        return 1

    @staticmethod
    def _env_var_to_provider(env_var: str) -> str:
        """Map an environment variable name to its provider."""
        mapping = {
            "OPENAI": "openai",
            "ANTHROPIC": "anthropic",
            "GOOGLE": "google_ai",
            "PINECONE": "pinecone",
            "HF_": "huggingface",
            "HUGGING": "huggingface",
            "LANGCHAIN": "langchain",
            "COHERE": "cohere",
            "MISTRAL": "mistral",
            "GROQ": "groq",
            "DEEPSEEK": "deepseek",
            "TOGETHER": "together_ai",
            "AWS_BEDROCK": "aws_bedrock",
            "AZURE_OPENAI": "azure_openai",
            "QDRANT": "qdrant",
            "WEAVIATE": "weaviate",
            "OLLAMA": "ollama",
            "MILVUS": "milvus",
        }
        for prefix, provider in mapping.items():
            if env_var.startswith(prefix):
                return provider
        return ""
