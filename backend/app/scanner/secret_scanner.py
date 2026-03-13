"""
Secret detection scanner for AI-specific API keys, tokens, and credentials.
Scans .env files, source code, and configuration files.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── AI-specific environment variable patterns ────────────────────────────────
# Each entry: (env_var_name, provider, display_name)

_AI_ENV_VARS: list[tuple[str, str, str]] = [
    # OpenAI
    ("OPENAI_API_KEY", "openai", "OpenAI"),
    ("OPENAI_ORG_ID", "openai", "OpenAI"),
    ("OPENAI_BASE_URL", "openai", "OpenAI"),
    ("OPENAI_API_BASE", "openai", "OpenAI"),
    # Anthropic
    ("ANTHROPIC_API_KEY", "anthropic", "Anthropic"),
    # Google
    ("GOOGLE_API_KEY", "google_ai", "Google AI"),
    ("GOOGLE_APPLICATION_CREDENTIALS", "google_ai", "Google Cloud"),
    ("GOOGLE_CLOUD_PROJECT", "google_ai", "Google Cloud"),
    # AWS Bedrock
    ("AWS_ACCESS_KEY_ID", "aws_bedrock", "AWS"),
    ("AWS_SECRET_ACCESS_KEY", "aws_bedrock", "AWS"),
    ("AWS_DEFAULT_REGION", "aws_bedrock", "AWS"),
    ("AWS_BEDROCK_REGION", "aws_bedrock", "AWS Bedrock"),
    ("AWS_SESSION_TOKEN", "aws_bedrock", "AWS"),
    # Azure OpenAI
    ("AZURE_OPENAI_API_KEY", "azure_openai", "Azure OpenAI"),
    ("AZURE_OPENAI_ENDPOINT", "azure_openai", "Azure OpenAI"),
    ("AZURE_OPENAI_API_VERSION", "azure_openai", "Azure OpenAI"),
    ("AZURE_OPENAI_DEPLOYMENT_NAME", "azure_openai", "Azure OpenAI"),
    # Vector DBs
    ("PINECONE_API_KEY", "pinecone", "Pinecone"),
    ("PINECONE_ENVIRONMENT", "pinecone", "Pinecone"),
    ("PINECONE_INDEX", "pinecone", "Pinecone"),
    ("QDRANT_API_KEY", "qdrant", "Qdrant"),
    ("QDRANT_URL", "qdrant", "Qdrant"),
    ("WEAVIATE_API_KEY", "weaviate", "Weaviate"),
    ("WEAVIATE_URL", "weaviate", "Weaviate"),
    ("MILVUS_HOST", "milvus", "Milvus"),
    ("MILVUS_PORT", "milvus", "Milvus"),
    # Hugging Face
    ("HF_TOKEN", "huggingface", "Hugging Face"),
    ("HUGGING_FACE_HUB_TOKEN", "huggingface", "Hugging Face"),
    ("HF_HOME", "huggingface", "Hugging Face"),
    ("HF_API_KEY", "huggingface", "Hugging Face"),
    # Cohere
    ("COHERE_API_KEY", "cohere", "Cohere"),
    ("CO_API_KEY", "cohere", "Cohere"),
    # Mistral
    ("MISTRAL_API_KEY", "mistral", "Mistral AI"),
    # Groq
    ("GROQ_API_KEY", "groq", "Groq"),
    # DeepSeek
    ("DEEPSEEK_API_KEY", "deepseek", "DeepSeek"),
    # Together AI
    ("TOGETHER_API_KEY", "together_ai", "Together AI"),
    # LangChain
    ("LANGCHAIN_API_KEY", "langchain", "LangChain"),
    ("LANGCHAIN_TRACING_V2", "langchain", "LangChain"),
    ("LANGCHAIN_PROJECT", "langchain", "LangChain"),
    ("LANGSMITH_API_KEY", "langchain", "LangSmith"),
    # Ollama
    ("OLLAMA_HOST", "ollama", "Ollama"),
    ("OLLAMA_BASE_URL", "ollama", "Ollama"),
    # Replicate
    ("REPLICATE_API_TOKEN", "replicate", "Replicate"),
    # Fireworks
    ("FIREWORKS_API_KEY", "fireworks", "Fireworks AI"),
    # Perplexity
    ("PERPLEXITY_API_KEY", "perplexity", "Perplexity"),
    # Voyage AI
    ("VOYAGE_API_KEY", "voyage", "Voyage AI"),
    # Weights & Biases
    ("WANDB_API_KEY", "wandb", "Weights & Biases"),
    # Neptune
    ("NEPTUNE_API_TOKEN", "neptune", "Neptune"),
    # Unstructured
    ("UNSTRUCTURED_API_KEY", "unstructured", "Unstructured"),
]

# Build quick lookup structures
_AI_ENV_VAR_NAMES: set[str] = {v[0] for v in _AI_ENV_VARS}
_AI_ENV_VAR_MAP: dict[str, tuple[str, str]] = {v[0]: (v[1], v[2]) for v in _AI_ENV_VARS}

# Prefixes for broad matching of env vars not in the explicit list
_AI_ENV_PREFIXES = (
    "OPENAI_", "ANTHROPIC_", "AZURE_OPENAI_", "AWS_BEDROCK_",
    "PINECONE_", "QDRANT_", "WEAVIATE_", "MILVUS_",
    "HF_", "HUGGING_FACE_", "COHERE_", "MISTRAL_",
    "GROQ_", "DEEPSEEK_", "TOGETHER_", "LANGCHAIN_",
    "LANGSMITH_", "OLLAMA_", "REPLICATE_", "FIREWORKS_",
    "PERPLEXITY_", "VOYAGE_", "WANDB_",
)

# ── Hardcoded key value patterns ─────────────────────────────────────────────

_HARDCODED_KEY_PATTERNS: list[tuple[re.Pattern[str], str, str]] = [
    # OpenAI keys
    (re.compile(r"""(?:['"])(sk-[a-zA-Z0-9]{20,})(?:['"])"""), "openai", "OpenAI API key"),
    (re.compile(r"""(?:['"])(sk-proj-[a-zA-Z0-9_-]{20,})(?:['"])"""), "openai", "OpenAI project API key"),
    # Anthropic keys
    (re.compile(r"""(?:['"])(sk-ant-[a-zA-Z0-9_-]{20,})(?:['"])"""), "anthropic", "Anthropic API key"),
    # Pinecone keys
    (re.compile(r"""(?:['"])(pcsk_[a-zA-Z0-9]{20,})(?:['"])"""), "pinecone", "Pinecone API key"),
    # HuggingFace
    (re.compile(r"""(?:['"])(hf_[a-zA-Z0-9]{20,})(?:['"])"""), "huggingface", "Hugging Face token"),
    # Bearer tokens in strings
    (re.compile(r"""Bearer\s+(sk-[a-zA-Z0-9]{20,})"""), "openai", "OpenAI Bearer token"),
    (re.compile(r"""Bearer\s+(sk-ant-[a-zA-Z0-9_-]{20,})"""), "anthropic", "Anthropic Bearer token"),
]

# ── Patterns for detecting env var references vs hardcoded values ────────────

_RE_ENV_ASSIGNMENT = re.compile(
    r"""^([A-Z][A-Z0-9_]+)\s*=\s*(.*)$""",
    re.MULTILINE,
)

_RE_CODE_ASSIGNMENT = re.compile(
    r"""(?:api_key|apikey|api_token|token|secret|password|credential)\s*=\s*['"]((?!os\.environ|os\.getenv|process\.env).{8,})['"]""",
    re.IGNORECASE,
)

_RE_OS_ENVIRON = re.compile(
    r"""os\.(?:environ(?:\.get)?\s*\[?\s*|getenv\s*\(\s*)['"]([A-Z][A-Z0-9_]+)['"]""",
)

_RE_PROCESS_ENV = re.compile(
    r"""process\.env\.([A-Z][A-Z0-9_]+)""",
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


class SecretScanner:
    """Detect AI-specific secrets and credentials in source and config files."""

    def scan_file(
        self,
        file_path: Path,
        relative_path: str,
    ) -> list[dict[str, Any]]:
        """Scan a single file for hardcoded secrets and AI credential references.

        Args:
            file_path: Absolute path to the file.
            relative_path: Path relative to the repo root.

        Returns:
            A list of Finding dicts.
        """
        try:
            source = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            logger.warning("Failed to read %s: %s", file_path, exc)
            return []

        lines = source.splitlines()
        findings: list[dict[str, Any]] = []
        name = file_path.name.lower()

        if name.startswith(".env"):
            self._scan_env_file(lines, relative_path, findings)
        else:
            self._scan_source_file(lines, relative_path, findings)

        return findings

    # ── .env file scanning ───────────────────────────────────────────

    def _scan_env_file(
        self,
        lines: list[str],
        relative_path: str,
        findings: list[dict[str, Any]],
    ) -> None:
        """Scan .env files for AI credential definitions."""
        for i, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            m = _RE_ENV_ASSIGNMENT.match(stripped)
            if not m:
                continue

            var_name = m.group(1)
            var_value = m.group(2).strip().strip("'\"")

            # Check if this is a known AI env var or matches prefix
            is_ai_var = var_name in _AI_ENV_VAR_NAMES or any(
                var_name.startswith(prefix) for prefix in _AI_ENV_PREFIXES
            )
            if not is_ai_var:
                continue

            provider_info = _AI_ENV_VAR_MAP.get(var_name, ("", ""))
            provider, display = provider_info
            if not provider:
                provider = self._env_var_to_provider(var_name)
                display = provider.replace("_", " ").title() if provider else ""

            has_value = bool(var_value) and var_value not in (
                "${" + var_name + "}",
                "$" + var_name,
                "",
            )

            if has_value:
                # Mask the value for the finding output
                masked_value = var_value[:4] + "..." + var_value[-4:] if len(var_value) > 8 else "****"
                findings.append(_make_finding(
                    file_path=relative_path,
                    line_number=i,
                    line_text=f"{var_name}={masked_value}",
                    framework=display,
                    pattern_name=f"hardcoded_secret:{var_name}",
                    pattern_category="secret",
                    pattern_severity="critical",
                    pattern_description=(
                        f"Hardcoded {display} credential '{var_name}' detected -- "
                        f"use a secrets manager instead"
                    ),
                    snippet=f"{var_name}={masked_value}",
                    component_type="secret",
                    provider=provider,
                    owasp_id="LLM07",
                ))
            else:
                findings.append(_make_finding(
                    file_path=relative_path,
                    line_number=i,
                    line_text=stripped,
                    framework=display,
                    pattern_name=f"env_reference:{var_name}",
                    pattern_category="governance",
                    pattern_severity="info",
                    pattern_description=(
                        f"{display} credential '{var_name}' referenced "
                        f"(value not hardcoded)"
                    ),
                    snippet=_get_snippet(lines, i),
                    component_type="config_reference",
                    provider=provider,
                ))

    # ── Source code scanning ─────────────────────────────────────────

    def _scan_source_file(
        self,
        lines: list[str],
        relative_path: str,
        findings: list[dict[str, Any]],
    ) -> None:
        """Scan source code for hardcoded keys and env var references."""
        for i, line in enumerate(lines, start=1):
            # Skip comment-only lines
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("*"):
                continue

            # Check for hardcoded key patterns
            for pattern, provider, description in _HARDCODED_KEY_PATTERNS:
                m = pattern.search(line)
                if m:
                    key_value = m.group(1)
                    # Make sure it is not inside an env var fetch
                    if re.search(r"(os\.getenv|os\.environ|process\.env|ENV\[)", line):
                        continue
                    masked = key_value[:6] + "..." + key_value[-4:] if len(key_value) > 10 else "****"
                    findings.append(_make_finding(
                        file_path=relative_path,
                        line_number=i,
                        line_text=line.rstrip()[:200],
                        framework=provider.title() if provider != "unknown" else "",
                        pattern_name=f"hardcoded_key:{provider}",
                        pattern_category="secret",
                        pattern_severity="critical",
                        pattern_description=(
                            f"Hardcoded {description} detected in source code -- "
                            f"value: {masked}"
                        ),
                        snippet=_get_snippet(lines, i),
                        component_type="secret",
                        provider=provider,
                        owasp_id="LLM07",
                    ))
                    break  # One hardcoded key finding per line

            # Check for api_key = "..." assignments (generic)
            m = _RE_CODE_ASSIGNMENT.search(line)
            if m:
                secret_val = m.group(1)
                # Make sure it is not a placeholder or env var reference
                if not re.search(r"(os\.getenv|os\.environ|process\.env|config\.|settings\.)", line):
                    if not re.search(r"(?:xxx|placeholder|your.key|changeme|TODO|REPLACE)", secret_val, re.IGNORECASE):
                        masked = secret_val[:4] + "..." if len(secret_val) > 8 else "****"
                        findings.append(_make_finding(
                            file_path=relative_path,
                            line_number=i,
                            line_text=line.rstrip()[:200],
                            pattern_name="hardcoded_credential",
                            pattern_category="secret",
                            pattern_severity="high",
                            pattern_description=(
                                f"Possible hardcoded credential in source: {masked}"
                            ),
                            snippet=_get_snippet(lines, i),
                            component_type="secret",
                            provider="",
                            owasp_id="LLM07",
                        ))

            # Check for os.environ / os.getenv references to AI keys
            for env_match in _RE_OS_ENVIRON.finditer(line):
                env_name = env_match.group(1)
                if env_name in _AI_ENV_VAR_NAMES:
                    prov, display = _AI_ENV_VAR_MAP[env_name]
                    findings.append(_make_finding(
                        file_path=relative_path,
                        line_number=i,
                        line_text=line.rstrip()[:200],
                        framework=display,
                        pattern_name=f"env_reference:{env_name}",
                        pattern_category="governance",
                        pattern_severity="info",
                        pattern_description=(
                            f"{display} credential '{env_name}' accessed via os.environ/getenv"
                        ),
                        snippet=_get_snippet(lines, i),
                        component_type="config_reference",
                        provider=prov,
                    ))

            # Check for process.env references (JS/TS)
            for env_match in _RE_PROCESS_ENV.finditer(line):
                env_name = env_match.group(1)
                if env_name in _AI_ENV_VAR_NAMES:
                    prov, display = _AI_ENV_VAR_MAP[env_name]
                    findings.append(_make_finding(
                        file_path=relative_path,
                        line_number=i,
                        line_text=line.rstrip()[:200],
                        framework=display,
                        pattern_name=f"env_reference:{env_name}",
                        pattern_category="governance",
                        pattern_severity="info",
                        pattern_description=(
                            f"{display} credential '{env_name}' accessed via process.env"
                        ),
                        snippet=_get_snippet(lines, i),
                        component_type="config_reference",
                        provider=prov,
                    ))

    # ── Utilities ────────────────────────────────────────────────────

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
            "LANGSMITH": "langchain",
            "COHERE": "cohere",
            "MISTRAL": "mistral",
            "GROQ": "groq",
            "DEEPSEEK": "deepseek",
            "TOGETHER": "together_ai",
            "AWS_BEDROCK": "aws_bedrock",
            "AWS": "aws_bedrock",
            "AZURE_OPENAI": "azure_openai",
            "AZURE": "azure_openai",
            "QDRANT": "qdrant",
            "WEAVIATE": "weaviate",
            "MILVUS": "milvus",
            "OLLAMA": "ollama",
            "REPLICATE": "replicate",
            "FIREWORKS": "fireworks",
            "PERPLEXITY": "perplexity",
            "VOYAGE": "voyage",
            "WANDB": "wandb",
        }
        for prefix, provider in mapping.items():
            if env_var.startswith(prefix):
                return provider
        return ""
