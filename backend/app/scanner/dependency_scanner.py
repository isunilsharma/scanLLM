"""
Dependency file scanner for detecting AI/LLM packages in requirements.txt,
pyproject.toml, Pipfile, package.json, package-lock.json, and yarn.lock.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Known AI Python packages mapped to (provider_key, category, display_name) ─

_PYTHON_AI_PACKAGES: dict[str, tuple[str, str, str]] = {
    "openai": ("openai", "llm_provider", "OpenAI"),
    "anthropic": ("anthropic", "llm_provider", "Anthropic"),
    "google-generativeai": ("google_ai", "llm_provider", "Google AI"),
    "google-cloud-aiplatform": ("google_ai", "llm_provider", "Google Vertex AI"),
    "vertexai": ("google_ai", "llm_provider", "Google Vertex AI"),
    "boto3": ("aws_bedrock", "llm_provider", "AWS (potential Bedrock)"),
    "cohere": ("cohere", "llm_provider", "Cohere"),
    "mistralai": ("mistral", "llm_provider", "Mistral AI"),
    "together": ("together_ai", "llm_provider", "Together AI"),
    "groq": ("groq", "llm_provider", "Groq"),
    # Orchestration frameworks
    "langchain": ("langchain", "orchestration_framework", "LangChain"),
    "langchain-core": ("langchain", "orchestration_framework", "LangChain Core"),
    "langchain-openai": ("langchain", "orchestration_framework", "LangChain OpenAI"),
    "langchain-anthropic": ("langchain", "orchestration_framework", "LangChain Anthropic"),
    "langchain-google-genai": ("langchain", "orchestration_framework", "LangChain Google"),
    "langchain-community": ("langchain", "orchestration_framework", "LangChain Community"),
    "langchain-text-splitters": ("langchain", "orchestration_framework", "LangChain Text Splitters"),
    "langgraph": ("langchain", "orchestration_framework", "LangGraph"),
    "langserve": ("langchain", "orchestration_framework", "LangServe"),
    "langsmith": ("langchain", "orchestration_framework", "LangSmith"),
    "llama-index": ("llamaindex", "orchestration_framework", "LlamaIndex"),
    "llama-index-core": ("llamaindex", "orchestration_framework", "LlamaIndex Core"),
    "llama-index-llms-openai": ("llamaindex", "orchestration_framework", "LlamaIndex OpenAI"),
    "llama-index-llms-anthropic": ("llamaindex", "orchestration_framework", "LlamaIndex Anthropic"),
    "llama-index-embeddings-openai": ("llamaindex", "orchestration_framework", "LlamaIndex Embeddings"),
    "dspy-ai": ("dspy", "orchestration_framework", "DSPy"),
    "dspy": ("dspy", "orchestration_framework", "DSPy"),
    "haystack-ai": ("haystack", "orchestration_framework", "Haystack"),
    "farm-haystack": ("haystack", "orchestration_framework", "Haystack"),
    # Agent frameworks
    "crewai": ("crewai", "agent_tool", "CrewAI"),
    "crewai-tools": ("crewai", "agent_tool", "CrewAI Tools"),
    "autogen": ("autogen", "agent_tool", "AutoGen"),
    "pyautogen": ("autogen", "agent_tool", "AutoGen"),
    "ag2": ("autogen", "agent_tool", "AG2"),
    # Vector databases
    "chromadb": ("chromadb", "vector_db", "ChromaDB"),
    "pinecone-client": ("pinecone", "vector_db", "Pinecone"),
    "pinecone": ("pinecone", "vector_db", "Pinecone"),
    "qdrant-client": ("qdrant", "vector_db", "Qdrant"),
    "weaviate-client": ("weaviate", "vector_db", "Weaviate"),
    "pymilvus": ("milvus", "vector_db", "Milvus"),
    "faiss-cpu": ("faiss", "vector_db", "FAISS"),
    "faiss-gpu": ("faiss", "vector_db", "FAISS"),
    "pgvector": ("pgvector", "vector_db", "pgvector"),
    # ML / Hugging Face
    "transformers": ("huggingface", "llm_provider", "Hugging Face Transformers"),
    "huggingface-hub": ("huggingface", "llm_provider", "Hugging Face Hub"),
    "sentence-transformers": ("huggingface", "embedding_service", "Sentence Transformers"),
    "tokenizers": ("huggingface", "llm_provider", "Hugging Face Tokenizers"),
    "accelerate": ("huggingface", "llm_provider", "Hugging Face Accelerate"),
    "datasets": ("huggingface", "llm_provider", "Hugging Face Datasets"),
    "peft": ("huggingface", "llm_provider", "Hugging Face PEFT"),
    "trl": ("huggingface", "llm_provider", "Hugging Face TRL"),
    # Inference
    "vllm": ("vllm", "inference_server", "vLLM"),
    "ollama": ("ollama", "inference_server", "Ollama"),
    # MCP
    "mcp": ("mcp_server", "mcp_server", "MCP"),
    # Guardrails / safety
    "guardrails-ai": ("guardrails", "orchestration_framework", "Guardrails AI"),
    "nemo-guardrails": ("nemo_guardrails", "orchestration_framework", "NeMo Guardrails"),
    # Evaluation
    "ragas": ("ragas", "orchestration_framework", "RAGAS"),
    "deepeval": ("deepeval", "orchestration_framework", "DeepEval"),
}

# ── Known AI JS/TS packages ─────────────────────────────────────────────────

_JS_AI_PACKAGES: dict[str, tuple[str, str, str]] = {
    "openai": ("openai", "llm_provider", "OpenAI"),
    "@anthropic-ai/sdk": ("anthropic", "llm_provider", "Anthropic"),
    "@google/generative-ai": ("google_ai", "llm_provider", "Google AI"),
    "ai": ("vercel_ai", "orchestration_framework", "Vercel AI SDK"),
    "@ai-sdk/openai": ("vercel_ai", "orchestration_framework", "Vercel AI SDK OpenAI"),
    "@ai-sdk/anthropic": ("vercel_ai", "orchestration_framework", "Vercel AI SDK Anthropic"),
    "@ai-sdk/google": ("vercel_ai", "orchestration_framework", "Vercel AI SDK Google"),
    "langchain": ("langchain", "orchestration_framework", "LangChain"),
    "@langchain/openai": ("langchain", "orchestration_framework", "LangChain OpenAI"),
    "@langchain/anthropic": ("langchain", "orchestration_framework", "LangChain Anthropic"),
    "@langchain/core": ("langchain", "orchestration_framework", "LangChain Core"),
    "@langchain/community": ("langchain", "orchestration_framework", "LangChain Community"),
    "llamaindex": ("llamaindex", "orchestration_framework", "LlamaIndex"),
    "@modelcontextprotocol/sdk": ("mcp_server", "mcp_server", "MCP SDK"),
    "chromadb": ("chromadb", "vector_db", "ChromaDB"),
    "@pinecone-database/pinecone": ("pinecone", "vector_db", "Pinecone"),
    "@qdrant/js-client-rest": ("qdrant", "vector_db", "Qdrant"),
    "weaviate-ts-client": ("weaviate", "vector_db", "Weaviate"),
    "cohere-ai": ("cohere", "llm_provider", "Cohere"),
    "@mistralai/mistralai": ("mistral", "llm_provider", "Mistral AI"),
    "groq-sdk": ("groq", "llm_provider", "Groq"),
    "@huggingface/inference": ("huggingface", "llm_provider", "Hugging Face"),
}

# ── Version patterns for extracting versions from dependency files ───────────

_RE_REQUIREMENTS_LINE = re.compile(
    r"^([a-zA-Z0-9_-][a-zA-Z0-9._-]*)\s*(?:\[.*?\])?\s*([<>=!~]+\s*[\d.]+(?:\s*,\s*[<>=!~]+\s*[\d.]+)*)?\s*$"
)

_RE_YARN_LOCK_ENTRY = re.compile(
    r'^"?(@?[a-zA-Z0-9._/-]+)@'
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


class DependencyScanner:
    """Scan dependency files for AI/LLM packages."""

    def __init__(self) -> None:
        # Extended lookups enriched from signatures at scan time
        self._extra_py_packages: dict[str, tuple[str, str, str]] = {}
        self._extra_js_packages: dict[str, tuple[str, str, str]] = {}

    def scan_file(
        self,
        file_path: Path,
        relative_path: str,
        signatures: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Scan a dependency file and return findings for AI packages."""
        if signatures:
            self._enrich_from_signatures(signatures)

        name = file_path.name.lower()

        try:
            source = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            logger.warning("Failed to read %s: %s", file_path, exc)
            return []

        if name == "requirements.txt" or name.startswith("requirements"):
            return self._scan_requirements_txt(source, relative_path)
        elif name == "pyproject.toml":
            return self._scan_pyproject_toml(source, relative_path)
        elif name == "pipfile":
            return self._scan_pipfile(source, relative_path)
        elif name == "package.json":
            return self._scan_package_json(source, relative_path)
        elif name == "package-lock.json":
            return self._scan_package_lock_json(source, relative_path)
        elif name == "yarn.lock":
            return self._scan_yarn_lock(source, relative_path)

        return []

    # ── Signature enrichment ─────────────────────────────────────────

    def _enrich_from_signatures(self, signatures: dict[str, Any]) -> None:
        """Pull additional package names from signatures YAML."""
        for section_key in ("providers", "vector_databases", "frameworks",
                            "agents", "inference", "mcp"):
            section = signatures.get(section_key, {})
            if not isinstance(section, dict):
                continue
            for prov_key, info in section.items():
                if not isinstance(info, dict):
                    continue
                cat = info.get("category", section_key)
                display = info.get("display_name", prov_key)
                py = info.get("python", {})
                if isinstance(py, dict):
                    for imp in py.get("imports", []):
                        pkg = imp.replace("from ", "").replace(" import", "").strip()
                        pkg_normalised = pkg.replace("_", "-").lower()
                        if pkg_normalised and pkg_normalised not in _PYTHON_AI_PACKAGES:
                            self._extra_py_packages[pkg_normalised] = (prov_key, cat, display)
                js = info.get("javascript", {})
                if isinstance(js, dict):
                    for imp in js.get("imports", []):
                        m = re.search(r"""['"]([^'"]+)['"]""", imp)
                        if m:
                            pkg = m.group(1)
                            if pkg not in _JS_AI_PACKAGES:
                                self._extra_js_packages[pkg] = (prov_key, cat, display)

    def _lookup_py_package(self, pkg_name: str) -> tuple[str, str, str] | None:
        """Look up a Python package name in the combined package map."""
        normalised = pkg_name.lower().replace("_", "-")
        result = _PYTHON_AI_PACKAGES.get(normalised)
        if result:
            return result
        # Try prefix matching for langchain-*, llama-index-*, etc.
        for prefix in ("langchain-", "llama-index-", "autogen-"):
            if normalised.startswith(prefix):
                base = _PYTHON_AI_PACKAGES.get(prefix.rstrip("-"))
                if base:
                    return base
        return self._extra_py_packages.get(normalised)

    def _lookup_js_package(self, pkg_name: str) -> tuple[str, str, str] | None:
        """Look up a JS/TS package name in the combined package map."""
        result = _JS_AI_PACKAGES.get(pkg_name)
        if result:
            return result
        # Prefix matching for scoped packages
        for prefix in ("@langchain/", "@ai-sdk/", "@huggingface/"):
            if pkg_name.startswith(prefix):
                for key, val in _JS_AI_PACKAGES.items():
                    if key.startswith(prefix):
                        return val
        return self._extra_js_packages.get(pkg_name)

    # ── requirements.txt ─────────────────────────────────────────────

    def _scan_requirements_txt(
        self, source: str, relative_path: str,
    ) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        lines = source.splitlines()
        for i, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("-"):
                continue
            m = _RE_REQUIREMENTS_LINE.match(stripped)
            if not m:
                continue
            pkg_name = m.group(1)
            version_spec = m.group(2) or ""
            info = self._lookup_py_package(pkg_name)
            if info:
                prov, cat, display = info
                findings.append(_make_finding(
                    file_path=relative_path,
                    line_number=i,
                    line_text=stripped,
                    framework=display,
                    pattern_name=f"dependency:{pkg_name}",
                    pattern_category="ai_package",
                    pattern_severity="info",
                    pattern_description=(
                        f"AI package '{pkg_name}' ({display}) "
                        + (f"pinned to {version_spec}" if version_spec else "with no version pin")
                    ),
                    snippet=_get_snippet(lines, i),
                    component_type=cat,
                    provider=prov,
                    owasp_id="LLM03" if not version_spec else None,
                ))
        return findings

    # ── pyproject.toml ───────────────────────────────────────────────

    def _scan_pyproject_toml(
        self, source: str, relative_path: str,
    ) -> list[dict[str, Any]]:
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib  # type: ignore[no-redef]
            except ImportError:
                logger.debug("No TOML parser available for %s", relative_path)
                return []
        try:
            data = tomllib.loads(source)
        except Exception as exc:
            logger.debug("TOML parse error in %s: %s", relative_path, exc)
            return []

        findings: list[dict[str, Any]] = []
        lines = source.splitlines()

        # Collect dependencies from various pyproject.toml layouts
        deps: list[str] = []
        # PEP 621
        project = data.get("project", {})
        if isinstance(project, dict):
            deps.extend(project.get("dependencies", []))
            optional = project.get("optional-dependencies", {})
            if isinstance(optional, dict):
                for group_deps in optional.values():
                    if isinstance(group_deps, list):
                        deps.extend(group_deps)
        # Poetry
        poetry = data.get("tool", {}).get("poetry", {})
        if isinstance(poetry, dict):
            for section in ("dependencies", "dev-dependencies"):
                section_data = poetry.get(section, {})
                if isinstance(section_data, dict):
                    deps.extend(section_data.keys())
            # Poetry groups
            groups = poetry.get("group", {})
            if isinstance(groups, dict):
                for group in groups.values():
                    if isinstance(group, dict):
                        group_deps = group.get("dependencies", {})
                        if isinstance(group_deps, dict):
                            deps.extend(group_deps.keys())

        for dep_str in deps:
            m = re.match(r"([a-zA-Z0-9_-][a-zA-Z0-9._-]*)", dep_str)
            if not m:
                continue
            pkg_name = m.group(1)
            info = self._lookup_py_package(pkg_name)
            if info:
                prov, cat, display = info
                lineno = self._find_line(lines, pkg_name)
                version_str = dep_str[len(pkg_name):].strip()
                findings.append(_make_finding(
                    file_path=relative_path,
                    line_number=lineno,
                    line_text=_safe_line(lines, lineno),
                    framework=display,
                    pattern_name=f"dependency:{pkg_name}",
                    pattern_category="ai_package",
                    pattern_severity="info",
                    pattern_description=(
                        f"AI package '{pkg_name}' ({display}) in pyproject.toml"
                        + (f" -- {version_str}" if version_str else "")
                    ),
                    snippet=_get_snippet(lines, lineno),
                    component_type=cat,
                    provider=prov,
                ))
        return findings

    # ── Pipfile ──────────────────────────────────────────────────────

    def _scan_pipfile(
        self, source: str, relative_path: str,
    ) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        lines = source.splitlines()

        for i, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("["):
                continue
            m = re.match(r'^([a-zA-Z0-9_-]+)\s*=', stripped)
            if not m:
                continue
            pkg_name = m.group(1)
            info = self._lookup_py_package(pkg_name)
            if info:
                prov, cat, display = info
                findings.append(_make_finding(
                    file_path=relative_path,
                    line_number=i,
                    line_text=stripped,
                    framework=display,
                    pattern_name=f"dependency:{pkg_name}",
                    pattern_category="ai_package",
                    pattern_severity="info",
                    pattern_description=f"AI package '{pkg_name}' ({display}) in Pipfile",
                    snippet=_get_snippet(lines, i),
                    component_type=cat,
                    provider=prov,
                ))
        return findings

    # ── package.json ─────────────────────────────────────────────────

    def _scan_package_json(
        self, source: str, relative_path: str,
    ) -> list[dict[str, Any]]:
        try:
            data = json.loads(source)
        except json.JSONDecodeError as exc:
            logger.debug("JSON parse error in %s: %s", relative_path, exc)
            return []

        findings: list[dict[str, Any]] = []
        lines = source.splitlines()

        for section in ("dependencies", "devDependencies", "peerDependencies"):
            deps = data.get(section, {})
            if not isinstance(deps, dict):
                continue
            for pkg_name, version in deps.items():
                info = self._lookup_js_package(pkg_name)
                if info:
                    prov, cat, display = info
                    lineno = self._find_line(lines, pkg_name)
                    version_str = version if isinstance(version, str) else ""
                    findings.append(_make_finding(
                        file_path=relative_path,
                        line_number=lineno,
                        line_text=_safe_line(lines, lineno),
                        framework=display,
                        pattern_name=f"dependency:{pkg_name}",
                        pattern_category="ai_package",
                        pattern_severity="info",
                        pattern_description=(
                            f"AI package '{pkg_name}' ({display}) "
                            + (f"version {version_str}" if version_str else "")
                            + f" in {section}"
                        ),
                        snippet=_get_snippet(lines, lineno),
                        component_type=cat,
                        provider=prov,
                    ))
        return findings

    # ── package-lock.json ────────────────────────────────────────────

    def _scan_package_lock_json(
        self, source: str, relative_path: str,
    ) -> list[dict[str, Any]]:
        try:
            data = json.loads(source)
        except json.JSONDecodeError as exc:
            logger.debug("JSON parse error in %s: %s", relative_path, exc)
            return []

        findings: list[dict[str, Any]] = []

        # package-lock v2/v3 uses "packages" key
        packages = data.get("packages", {})
        if isinstance(packages, dict):
            for pkg_path, pkg_info in packages.items():
                pkg_name = pkg_path.replace("node_modules/", "").strip()
                if not pkg_name:
                    continue
                info = self._lookup_js_package(pkg_name)
                if info:
                    prov, cat, display = info
                    version = pkg_info.get("version", "") if isinstance(pkg_info, dict) else ""
                    findings.append(_make_finding(
                        file_path=relative_path,
                        line_number=1,
                        line_text=f"{pkg_name}@{version}",
                        framework=display,
                        pattern_name=f"dependency:{pkg_name}",
                        pattern_category="ai_package",
                        pattern_severity="info",
                        pattern_description=(
                            f"AI package '{pkg_name}' ({display}) "
                            f"version {version} in lock file"
                        ),
                        snippet="",
                        component_type=cat,
                        provider=prov,
                    ))

        # Fallback: package-lock v1 uses "dependencies"
        deps = data.get("dependencies", {})
        if isinstance(deps, dict) and not packages:
            for pkg_name, pkg_info in deps.items():
                info = self._lookup_js_package(pkg_name)
                if info:
                    prov, cat, display = info
                    version = pkg_info.get("version", "") if isinstance(pkg_info, dict) else ""
                    findings.append(_make_finding(
                        file_path=relative_path,
                        line_number=1,
                        line_text=f"{pkg_name}@{version}",
                        framework=display,
                        pattern_name=f"dependency:{pkg_name}",
                        pattern_category="ai_package",
                        pattern_severity="info",
                        pattern_description=(
                            f"AI package '{pkg_name}' ({display}) "
                            f"version {version} in lock file"
                        ),
                        snippet="",
                        component_type=cat,
                        provider=prov,
                    ))

        return findings

    # ── yarn.lock ────────────────────────────────────────────────────

    def _scan_yarn_lock(
        self, source: str, relative_path: str,
    ) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        lines = source.splitlines()
        seen: set[str] = set()

        for i, line in enumerate(lines, start=1):
            m = _RE_YARN_LOCK_ENTRY.match(line)
            if not m:
                continue
            pkg_name = m.group(1)
            if pkg_name in seen:
                continue
            seen.add(pkg_name)
            info = self._lookup_js_package(pkg_name)
            if info:
                prov, cat, display = info
                # Try to grab version from next few lines
                version = ""
                for j in range(i, min(i + 5, len(lines))):
                    version_match = re.search(r'version\s+"?([^"]+)"?', lines[j])
                    if version_match:
                        version = version_match.group(1)
                        break
                findings.append(_make_finding(
                    file_path=relative_path,
                    line_number=i,
                    line_text=line.rstrip(),
                    framework=display,
                    pattern_name=f"dependency:{pkg_name}",
                    pattern_category="ai_package",
                    pattern_severity="info",
                    pattern_description=(
                        f"AI package '{pkg_name}' ({display}) "
                        + (f"version {version}" if version else "")
                        + " in yarn.lock"
                    ),
                    snippet=_get_snippet(lines, i),
                    component_type=cat,
                    provider=prov,
                ))
        return findings

    # ── Utilities ────────────────────────────────────────────────────

    @staticmethod
    def _find_line(lines: list[str], value: str) -> int:
        """Best-effort line number lookup."""
        for i, line in enumerate(lines, start=1):
            if value in line:
                return i
        return 1
