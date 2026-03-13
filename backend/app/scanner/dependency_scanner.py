"""Dependency file parser for AI packages"""
import re
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# AI packages to detect in Python
PYTHON_AI_PACKAGES = {
    "openai": ("openai", "llm_provider"),
    "anthropic": ("anthropic", "llm_provider"),
    "langchain": ("langchain", "orchestration_framework"),
    "langchain-openai": ("langchain", "orchestration_framework"),
    "langchain-anthropic": ("langchain", "orchestration_framework"),
    "langchain-community": ("langchain", "orchestration_framework"),
    "langchain-core": ("langchain", "orchestration_framework"),
    "langchain-text-splitters": ("langchain", "orchestration_framework"),
    "langgraph": ("langchain", "orchestration_framework"),
    "langserve": ("langchain", "orchestration_framework"),
    "langsmith": ("langchain", "orchestration_framework"),
    "llama-index": ("llamaindex", "orchestration_framework"),
    "llama-index-core": ("llamaindex", "orchestration_framework"),
    "chromadb": ("chromadb", "vector_db"),
    "pinecone-client": ("pinecone", "vector_db"),
    "pinecone": ("pinecone", "vector_db"),
    "qdrant-client": ("qdrant", "vector_db"),
    "weaviate-client": ("weaviate", "vector_db"),
    "pymilvus": ("milvus", "vector_db"),
    "faiss-cpu": ("faiss", "vector_db"),
    "faiss-gpu": ("faiss", "vector_db"),
    "pgvector": ("pgvector", "vector_db"),
    "transformers": ("huggingface", "llm_provider"),
    "huggingface-hub": ("huggingface", "llm_provider"),
    "sentence-transformers": ("huggingface", "embedding_service"),
    "crewai": ("crewai", "agent_tool"),
    "crewai-tools": ("crewai", "agent_tool"),
    "autogen": ("autogen", "agent_tool"),
    "pyautogen": ("autogen", "agent_tool"),
    "ag2": ("autogen", "agent_tool"),
    "dspy-ai": ("dspy", "orchestration_framework"),
    "dspy": ("dspy", "orchestration_framework"),
    "haystack-ai": ("haystack", "orchestration_framework"),
    "farm-haystack": ("haystack", "orchestration_framework"),
    "vllm": ("vllm", "inference_server"),
    "ollama": ("ollama", "inference_server"),
    "cohere": ("cohere", "llm_provider"),
    "mistralai": ("mistral", "llm_provider"),
    "groq": ("groq", "llm_provider"),
    "together": ("together", "llm_provider"),
    "google-generativeai": ("google", "llm_provider"),
    "google-cloud-aiplatform": ("google", "llm_provider"),
    "vertexai": ("google", "llm_provider"),
    "boto3": ("aws", "llm_provider"),  # May be used for Bedrock
    "mcp": ("mcp", "mcp_server"),
}

# AI packages to detect in JS/Node
JS_AI_PACKAGES = {
    "openai": ("openai", "llm_provider"),
    "@anthropic-ai/sdk": ("anthropic", "llm_provider"),
    "@langchain/openai": ("langchain", "orchestration_framework"),
    "@langchain/anthropic": ("langchain", "orchestration_framework"),
    "@langchain/core": ("langchain", "orchestration_framework"),
    "@langchain/community": ("langchain", "orchestration_framework"),
    "langchain": ("langchain", "orchestration_framework"),
    "ai": ("vercel_ai", "orchestration_framework"),
    "@ai-sdk/openai": ("vercel_ai", "orchestration_framework"),
    "@ai-sdk/anthropic": ("vercel_ai", "orchestration_framework"),
    "@ai-sdk/google": ("vercel_ai", "orchestration_framework"),
    "@google/generative-ai": ("google", "llm_provider"),
    "@modelcontextprotocol/sdk": ("mcp", "mcp_server"),
    "llamaindex": ("llamaindex", "orchestration_framework"),
    "@pinecone-database/pinecone": ("pinecone", "vector_db"),
    "chromadb": ("chromadb", "vector_db"),
}


class DependencyScanner:
    """Parse dependency files to detect AI packages"""

    def scan_file(self, file_path: Path, relative_path: str, signatures: dict = None) -> List[Dict[str, Any]]:
        findings = []
        name = file_path.name.lower()

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            logger.debug(f"Failed to read {relative_path}: {e}")
            return findings

        if name == "requirements.txt":
            findings.extend(self._parse_requirements_txt(content, relative_path))
        elif name == "pyproject.toml":
            findings.extend(self._parse_pyproject_toml(content, relative_path))
        elif name == "pipfile":
            findings.extend(self._parse_pipfile(content, relative_path))
        elif name == "package.json":
            findings.extend(self._parse_package_json(content, relative_path))
        elif name in ("package-lock.json", "yarn.lock", "pnpm-lock.yaml"):
            findings.extend(self._parse_lockfile(content, relative_path, name))

        return findings

    def _parse_requirements_txt(self, content: str, relative_path: str) -> List[Dict[str, Any]]:
        findings = []
        for line_num, line in enumerate(content.split("\n"), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("-"):
                continue

            # Parse package==version or package>=version
            match = re.match(r"^([a-zA-Z0-9_.-]+)\s*([><=!~]+\s*[\d.]+)?", stripped)
            if not match:
                continue

            pkg_name = match.group(1).lower()
            version = match.group(2).strip() if match.group(2) else None

            if pkg_name in PYTHON_AI_PACKAGES:
                framework, comp_type = PYTHON_AI_PACKAGES[pkg_name]
                findings.append(self._make_finding(
                    relative_path, line_num, stripped, pkg_name, version,
                    framework, comp_type
                ))
        return findings

    def _parse_pyproject_toml(self, content: str, relative_path: str) -> List[Dict[str, Any]]:
        findings = []
        try:
            import tomllib
            data = tomllib.loads(content)
        except Exception:
            # Fallback to line-by-line for pyproject.toml
            return self._scan_lines_for_packages(content, relative_path, PYTHON_AI_PACKAGES)

        # Check [project.dependencies] and [tool.poetry.dependencies]
        deps = []
        project_deps = data.get("project", {}).get("dependencies", [])
        if isinstance(project_deps, list):
            deps.extend(project_deps)

        poetry_deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
        if isinstance(poetry_deps, dict):
            deps.extend(poetry_deps.keys())

        for dep_str in deps:
            pkg_name = re.match(r"^([a-zA-Z0-9_.-]+)", str(dep_str))
            if pkg_name:
                name = pkg_name.group(1).lower()
                if name in PYTHON_AI_PACKAGES:
                    framework, comp_type = PYTHON_AI_PACKAGES[name]
                    findings.append(self._make_finding(
                        relative_path, 1, dep_str, name, None, framework, comp_type
                    ))
        return findings

    def _parse_pipfile(self, content: str, relative_path: str) -> List[Dict[str, Any]]:
        return self._scan_lines_for_packages(content, relative_path, PYTHON_AI_PACKAGES)

    def _parse_package_json(self, content: str, relative_path: str) -> List[Dict[str, Any]]:
        findings = []
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return findings

        for section in ("dependencies", "devDependencies", "peerDependencies"):
            deps = data.get(section, {})
            if not isinstance(deps, dict):
                continue
            for pkg_name, version in deps.items():
                if pkg_name in JS_AI_PACKAGES:
                    framework, comp_type = JS_AI_PACKAGES[pkg_name]
                    findings.append(self._make_finding(
                        relative_path, 1, f'"{pkg_name}": "{version}"',
                        pkg_name, version, framework, comp_type
                    ))
        return findings

    def _parse_lockfile(self, content: str, relative_path: str, name: str) -> List[Dict[str, Any]]:
        """Scan lockfiles for AI packages"""
        packages = JS_AI_PACKAGES if "package" in name or "yarn" in name or "pnpm" in name else PYTHON_AI_PACKAGES
        return self._scan_lines_for_packages(content, relative_path, packages)

    def _scan_lines_for_packages(self, content: str, relative_path: str, packages: dict) -> List[Dict[str, Any]]:
        findings = []
        for line_num, line in enumerate(content.split("\n"), start=1):
            for pkg_name, (framework, comp_type) in packages.items():
                if pkg_name in line.lower():
                    findings.append(self._make_finding(
                        relative_path, line_num, line.strip()[:500],
                        pkg_name, None, framework, comp_type
                    ))
                    break
        return findings

    def _make_finding(self, relative_path: str, line_num: int, line_text: str,
                      pkg_name: str, version: Optional[str], framework: str,
                      component_type: str) -> Dict[str, Any]:
        return {
            "file_path": relative_path,
            "line_number": line_num,
            "line_text": line_text,
            "framework": framework,
            "pattern_name": f"dependency_{pkg_name}",
            "pattern_category": "ai_package",
            "pattern_severity": "low",
            "pattern_description": f"AI package dependency: {pkg_name}" + (f" ({version})" if version else ""),
            "snippet": line_text,
            "model_name": None,
            "temperature": None,
            "max_tokens": None,
            "is_streaming": False,
            "has_tools": False,
            "component_type": component_type,
            "provider": framework,
            "owasp_id": "LLM03",  # Supply chain
        }
