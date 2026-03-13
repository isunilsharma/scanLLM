"""AI-specific secret detection scanner"""
import re
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Hardcoded API key patterns (value patterns - critical severity)
HARDCODED_KEY_PATTERNS = [
    # OpenAI
    (r"sk-[a-zA-Z0-9]{20,}", "openai", "OpenAI API key"),
    (r"sk-proj-[a-zA-Z0-9\-_]{20,}", "openai", "OpenAI project API key"),
    # Anthropic
    (r"sk-ant-[a-zA-Z0-9\-_]{20,}", "anthropic", "Anthropic API key"),
    # Pinecone
    (r"pcsk_[a-zA-Z0-9]{20,}", "pinecone", "Pinecone API key"),
    # Hugging Face
    (r"hf_[a-zA-Z0-9]{20,}", "huggingface", "Hugging Face token"),
    # Cohere
    (r"[a-zA-Z0-9]{40}", None, None),  # Too generic, skip unless in context
    # Generic long keys in assignments
    (r"""(?:api_key|apikey|api_token|access_token)\s*=\s*['"][a-zA-Z0-9\-_]{20,}['"]""",
     None, "Hardcoded API key/token"),
]

# Environment variable reference patterns (governance - low severity)
AI_ENV_VAR_NAMES = [
    "OPENAI_API_KEY", "OPENAI_ORG_ID", "OPENAI_BASE_URL", "OPENAI_API_BASE",
    "ANTHROPIC_API_KEY",
    "GOOGLE_API_KEY", "GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_CLOUD_PROJECT",
    "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_DEFAULT_REGION", "AWS_BEDROCK_REGION",
    "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_VERSION",
    "COHERE_API_KEY", "CO_API_KEY",
    "MISTRAL_API_KEY",
    "TOGETHER_API_KEY",
    "GROQ_API_KEY",
    "DEEPSEEK_API_KEY",
    "PINECONE_API_KEY", "PINECONE_ENVIRONMENT", "PINECONE_INDEX",
    "HF_TOKEN", "HUGGING_FACE_HUB_TOKEN", "HF_HOME",
    "LANGCHAIN_API_KEY", "LANGCHAIN_TRACING_V2", "LANGCHAIN_PROJECT",
    "QDRANT_URL", "QDRANT_API_KEY",
    "WEAVIATE_URL", "WEAVIATE_API_KEY",
    "MILVUS_HOST", "MILVUS_PORT",
    "OLLAMA_HOST", "OLLAMA_BASE_URL",
    "REPLICATE_API_TOKEN",
    "FIREWORKS_API_KEY",
    "PERPLEXITY_API_KEY",
    "VOYAGE_API_KEY",
]


class SecretScanner:
    """Detect AI-specific secrets and API key patterns"""

    def scan_file(self, file_path: Path, relative_path: str) -> List[Dict[str, Any]]:
        findings = []

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            logger.debug(f"Failed to read {relative_path}: {e}")
            return findings

        lines = content.split("\n")

        for line_num, line in enumerate(lines, start=1):
            # Skip comments
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("*"):
                continue

            # Check for hardcoded key patterns
            findings.extend(self._check_hardcoded_keys(line, line_num, lines, relative_path))

            # Check for env var references
            findings.extend(self._check_env_var_references(line, line_num, relative_path))

        return findings

    def _check_hardcoded_keys(self, line: str, line_num: int, lines: List[str],
                               relative_path: str) -> List[Dict[str, Any]]:
        findings = []

        # OpenAI keys
        if re.search(r"sk-[a-zA-Z0-9]{20,}", line):
            # Make sure it's not just a variable name reference
            if not re.search(r"(os\.getenv|os\.environ|process\.env|ENV\[)", line):
                findings.append(self._make_secret_finding(
                    relative_path, line_num, line, "openai",
                    "Hardcoded OpenAI API key detected",
                    "critical", self._extract_snippet(lines, line_num)
                ))

        # OpenAI project keys
        if re.search(r"sk-proj-[a-zA-Z0-9\-_]{20,}", line):
            if not re.search(r"(os\.getenv|os\.environ|process\.env)", line):
                findings.append(self._make_secret_finding(
                    relative_path, line_num, line, "openai",
                    "Hardcoded OpenAI project API key detected",
                    "critical", self._extract_snippet(lines, line_num)
                ))

        # Anthropic keys
        if re.search(r"sk-ant-[a-zA-Z0-9\-_]{20,}", line):
            if not re.search(r"(os\.getenv|os\.environ|process\.env)", line):
                findings.append(self._make_secret_finding(
                    relative_path, line_num, line, "anthropic",
                    "Hardcoded Anthropic API key detected",
                    "critical", self._extract_snippet(lines, line_num)
                ))

        # Pinecone keys
        if re.search(r"pcsk_[a-zA-Z0-9]{20,}", line):
            findings.append(self._make_secret_finding(
                relative_path, line_num, line, "pinecone",
                "Hardcoded Pinecone API key detected",
                "critical", self._extract_snippet(lines, line_num)
            ))

        # HuggingFace tokens
        if re.search(r"hf_[a-zA-Z0-9]{20,}", line):
            findings.append(self._make_secret_finding(
                relative_path, line_num, line, "huggingface",
                "Hardcoded Hugging Face token detected",
                "critical", self._extract_snippet(lines, line_num)
            ))

        # Generic hardcoded key in assignment
        key_assign = re.search(
            r"""(?:api_key|apikey|api_token|secret_key)\s*=\s*['"]([a-zA-Z0-9\-_]{20,})['"]""",
            line, re.IGNORECASE
        )
        if key_assign and not re.search(r"(os\.getenv|os\.environ|process\.env|config\.|settings\.)", line):
            findings.append(self._make_secret_finding(
                relative_path, line_num, line, None,
                "Hardcoded API key or token in assignment",
                "high", self._extract_snippet(lines, line_num)
            ))

        return findings

    def _check_env_var_references(self, line: str, line_num: int,
                                   relative_path: str) -> List[Dict[str, Any]]:
        findings = []
        for env_var in AI_ENV_VAR_NAMES:
            if env_var in line:
                # Determine if it's a reference (low) or a value assignment (high)
                is_env_file = relative_path.endswith(".env") or "/.env" in relative_path
                has_value = False
                if is_env_file and "=" in line:
                    val = line.split("=", 1)[1].strip()
                    has_value = len(val) > 0 and val not in ('""', "''", "${" + env_var + "}")

                findings.append({
                    "file_path": relative_path,
                    "line_number": line_num,
                    "line_text": line.strip()[:500],
                    "framework": "secrets",
                    "pattern_name": f"env_var_{env_var.lower()}",
                    "pattern_category": "secrets" if has_value else "config_reference",
                    "pattern_severity": "high" if has_value else "info",
                    "pattern_description": f"AI env var {'with value' if has_value else 'reference'}: {env_var}",
                    "snippet": line.strip(),
                    "model_name": None, "temperature": None, "max_tokens": None,
                    "is_streaming": False, "has_tools": False,
                    "component_type": "secret" if has_value else "config_reference",
                    "provider": self._env_var_to_provider(env_var),
                    "owasp_id": "LLM07" if has_value else None,
                })
                break  # One finding per line for env vars

        return findings

    def _make_secret_finding(self, relative_path: str, line_num: int, line: str,
                              provider: str, description: str, severity: str,
                              snippet: str) -> Dict[str, Any]:
        return {
            "file_path": relative_path,
            "line_number": line_num,
            "line_text": line.strip()[:500],
            "framework": "secrets",
            "pattern_name": f"hardcoded_secret_{provider or 'generic'}",
            "pattern_category": "secrets",
            "pattern_severity": severity,
            "pattern_description": description,
            "snippet": snippet,
            "model_name": None, "temperature": None, "max_tokens": None,
            "is_streaming": False, "has_tools": False,
            "component_type": "secret",
            "provider": provider,
            "owasp_id": "LLM07",
        }

    def _extract_snippet(self, lines: List[str], match_line: int, context: int = 3) -> str:
        start = max(0, match_line - context - 1)
        end = min(len(lines), match_line + context)
        return "\n".join(lines[start:end])

    def _env_var_to_provider(self, env_var: str) -> str:
        mapping = {
            "OPENAI": "openai", "ANTHROPIC": "anthropic", "GOOGLE": "google",
            "PINECONE": "pinecone", "HF_": "huggingface", "HUGGING": "huggingface",
            "LANGCHAIN": "langchain", "COHERE": "cohere", "MISTRAL": "mistral",
            "GROQ": "groq", "DEEPSEEK": "deepseek", "TOGETHER": "together",
            "AWS": "aws", "AZURE": "azure", "QDRANT": "qdrant",
            "WEAVIATE": "weaviate", "MILVUS": "milvus", "OLLAMA": "ollama",
            "REPLICATE": "replicate", "FIREWORKS": "fireworks",
            "PERPLEXITY": "perplexity", "VOYAGE": "voyage",
        }
        for prefix, prov in mapping.items():
            if env_var.startswith(prefix):
                return prov
        return "unknown"
