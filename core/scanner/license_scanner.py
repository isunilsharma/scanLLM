"""License compliance scanner for AI packages."""

from __future__ import annotations

from typing import Any

# Known AI package licenses
AI_PACKAGE_LICENSES: dict[str, dict[str, str]] = {
    "openai": {"license": "MIT", "risk": "low"},
    "anthropic": {"license": "MIT", "risk": "low"},
    "langchain": {"license": "MIT", "risk": "low"},
    "langchain-openai": {"license": "MIT", "risk": "low"},
    "langchain-anthropic": {"license": "MIT", "risk": "low"},
    "langchain-community": {"license": "MIT", "risk": "low"},
    "langchain-core": {"license": "MIT", "risk": "low"},
    "langgraph": {"license": "MIT", "risk": "low"},
    "llamaindex": {"license": "MIT", "risk": "low"},
    "llama-index": {"license": "MIT", "risk": "low"},
    "transformers": {"license": "Apache-2.0", "risk": "low"},
    "torch": {"license": "BSD-3-Clause", "risk": "low"},
    "tensorflow": {"license": "Apache-2.0", "risk": "low"},
    "chromadb": {"license": "Apache-2.0", "risk": "low"},
    "pinecone-client": {"license": "Apache-2.0", "risk": "low"},
    "weaviate-client": {"license": "BSD-3-Clause", "risk": "low"},
    "qdrant-client": {"license": "Apache-2.0", "risk": "low"},
    "faiss-cpu": {"license": "MIT", "risk": "low"},
    "sentence-transformers": {"license": "Apache-2.0", "risk": "low"},
    "crewai": {"license": "MIT", "risk": "low"},
    "autogen": {"license": "MIT", "risk": "low"},
    "dspy-ai": {"license": "MIT", "risk": "low"},
    "vllm": {"license": "Apache-2.0", "risk": "low"},
    "ollama": {"license": "MIT", "risk": "low"},
    "huggingface-hub": {"license": "Apache-2.0", "risk": "low"},
    "llama-cpp-python": {"license": "MIT", "risk": "medium", "note": "Wraps LLaMA models which have Meta's custom license"},
    "auto-gptq": {"license": "MIT", "risk": "low"},
    "bitsandbytes": {"license": "MIT", "risk": "low"},
    "gradio": {"license": "Apache-2.0", "risk": "low"},
    "streamlit": {"license": "Apache-2.0", "risk": "low"},
    "promptfoo": {"license": "MIT", "risk": "low"},
    "guardrails-ai": {"license": "Apache-2.0", "risk": "low"},
    "deepeval": {"license": "Apache-2.0", "risk": "low"},
}

# Licenses that are restrictive for proprietary use
RESTRICTIVE_LICENSES = {"GPL-2.0", "GPL-3.0", "LGPL-2.1", "LGPL-3.0", "AGPL-3.0", "SSPL-1.0", "BSL-1.1"}


class LicenseScanner:
    """Scan AI package dependencies for license compliance risks."""

    def scan(self, findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Analyze findings for license compliance issues."""
        license_findings: list[dict[str, Any]] = []
        seen_packages: set[str] = set()

        for finding in findings:
            if finding.get("component_type") != "ai_package":
                continue

            package_name = (finding.get("pattern_name", "") or "").lower().replace("_", "-")
            if package_name in seen_packages:
                continue
            seen_packages.add(package_name)

            license_info = AI_PACKAGE_LICENSES.get(package_name)
            if license_info:
                risk = license_info["risk"]
                severity = "high" if risk == "high" else "medium" if risk == "medium" else "info"

                entry: dict[str, Any] = {
                    "file_path": finding.get("file_path", ""),
                    "line_number": finding.get("line_number", 0),
                    "pattern_name": f"license-{package_name}",
                    "provider": finding.get("provider", ""),
                    "component_type": "license_compliance",
                    "severity": severity,
                    "license": license_info["license"],
                    "license_risk": risk,
                    "message": f"{package_name}: {license_info['license']} license ({risk} risk)",
                }

                if "note" in license_info:
                    entry["message"] += f" — {license_info['note']}"
                    entry["note"] = license_info["note"]

                if license_info["license"] in RESTRICTIVE_LICENSES:
                    entry["severity"] = "high"
                    entry["owasp_id"] = "LLM03"
                    entry["message"] += " — RESTRICTIVE: may not be compatible with proprietary use"

                license_findings.append(entry)

        return license_findings
