"""AI Bill of Materials (AI-BOM) generator for ScanLLM.

Produces CycloneDX 1.6-compatible ML-BOM output in JSON and XML formats.
Implemented without external CycloneDX library dependencies for robustness.
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any
from xml.dom import minidom

logger = logging.getLogger(__name__)

# Component type mapping to CycloneDX types
_CYCLONEDX_TYPE_MAP: dict[str, str] = {
    "llm_provider": "machine-learning-model",
    "embedding_service": "machine-learning-model",
    "vector_db": "library",
    "orchestration_framework": "framework",
    "agent_tool": "library",
    "mcp_server": "library",
    "inference_server": "platform",
    "ai_package": "library",
    "prompt_file": "data",
    "config_reference": "data",
    "secret": "data",
}

# Known license mapping for common AI packages
_KNOWN_LICENSES: dict[str, str] = {
    "openai": "MIT",
    "anthropic": "MIT",
    "langchain": "MIT",
    "langchain-core": "MIT",
    "langchain-openai": "MIT",
    "langchain-anthropic": "MIT",
    "langchain-community": "MIT",
    "langgraph": "MIT",
    "llamaindex": "MIT",
    "llama-index": "MIT",
    "chromadb": "Apache-2.0",
    "pinecone-client": "Apache-2.0",
    "faiss-cpu": "MIT",
    "faiss-gpu": "MIT",
    "qdrant-client": "Apache-2.0",
    "weaviate-client": "BSD-3-Clause",
    "milvus": "Apache-2.0",
    "crewai": "MIT",
    "autogen": "MIT",
    "dspy-ai": "MIT",
    "haystack-ai": "Apache-2.0",
    "transformers": "Apache-2.0",
    "torch": "BSD-3-Clause",
    "tensorflow": "Apache-2.0",
    "keras": "Apache-2.0",
    "huggingface-hub": "Apache-2.0",
    "sentence-transformers": "Apache-2.0",
    "tiktoken": "MIT",
    "tokenizers": "Apache-2.0",
    "vllm": "Apache-2.0",
    "litellm": "MIT",
    "guidance": "MIT",
    "instructor": "MIT",
    "mcp": "MIT",
    "@modelcontextprotocol/sdk": "MIT",
    "@anthropic-ai/sdk": "MIT",
    "@langchain/core": "MIT",
    "@langchain/openai": "MIT",
    "ai": "Apache-2.0",
    "ollama": "MIT",
}


def _generate_bom_ref(name: str, version: str = "") -> str:
    """Generate a deterministic BOM reference string."""
    raw = f"{name}:{version}" if version else name
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _generate_purl(name: str, version: str = "", pkg_type: str = "pypi") -> str:
    """Generate a Package URL (purl) for a component."""
    purl = f"pkg:{pkg_type}/{name}"
    if version:
        purl += f"@{version}"
    return purl


class AIBOMGenerator:
    """Generate CycloneDX 1.6-compatible AI/ML Bill of Materials."""

    def __init__(
        self,
        tool_name: str = "ScanLLM",
        tool_version: str = "1.0.0",
        tool_vendor: str = "ScanLLM",
    ) -> None:
        self._tool_name = tool_name
        self._tool_version = tool_version
        self._tool_vendor = tool_vendor

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, scan_data: dict[str, Any], findings: list[dict[str, Any]]) -> dict[str, Any]:
        """Generate a CycloneDX 1.6 JSON BOM from scan results.

        Args:
            scan_data: Full scan result dictionary (repo metadata, components, etc.).
            findings: List of individual finding dictionaries.

        Returns:
            CycloneDX 1.6 JSON-compatible dictionary.
        """
        serial = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        components = self._build_components(scan_data, findings)
        dependencies = self._build_dependencies(scan_data, components)

        bom: dict[str, Any] = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.6",
            "serialNumber": f"urn:uuid:{serial}",
            "version": 1,
            "metadata": {
                "timestamp": now,
                "tools": {
                    "components": [
                        {
                            "type": "application",
                            "name": self._tool_name,
                            "version": self._tool_version,
                            "publisher": self._tool_vendor,
                        }
                    ]
                },
                "component": self._build_root_component(scan_data),
                "properties": [
                    {"name": "scanllm:risk_score", "value": str(scan_data.get("risk_score", {}).get("overall_score", 0))},
                    {"name": "scanllm:grade", "value": scan_data.get("risk_score", {}).get("grade", "N/A")},
                    {"name": "scanllm:total_findings", "value": str(scan_data.get("total_occurrences", len(findings)))},
                ],
            },
            "components": components,
            "dependencies": dependencies,
        }

        # Add model card data for ML components
        ml_components = [c for c in components if c.get("type") == "machine-learning-model"]
        if ml_components:
            bom["compositions"] = [
                {
                    "aggregate": "incomplete",
                    "assemblies": [c["bom-ref"] for c in ml_components],
                }
            ]

        return bom

    def generate_xml(self, scan_data: dict[str, Any], findings: list[dict[str, Any]]) -> str:
        """Generate a CycloneDX 1.6 XML BOM from scan results.

        Args:
            scan_data: Full scan result dictionary.
            findings: List of individual finding dictionaries.

        Returns:
            CycloneDX XML string.
        """
        bom_dict = self.generate(scan_data, findings)
        root = self._dict_to_xml(bom_dict)
        rough = ET.tostring(root, encoding="unicode", xml_declaration=True)
        parsed = minidom.parseString(rough)
        return parsed.toprettyxml(indent="  ", encoding="UTF-8").decode("utf-8")

    # ------------------------------------------------------------------
    # Component building
    # ------------------------------------------------------------------

    def _build_root_component(self, scan_data: dict[str, Any]) -> dict[str, Any]:
        """Build the root (subject) component representing the scanned repo."""
        repo_name = scan_data.get("repo_name", scan_data.get("repository", "unknown"))
        repo_url = scan_data.get("repo_url", "")

        root: dict[str, Any] = {
            "type": "application",
            "name": repo_name,
            "bom-ref": _generate_bom_ref(f"root:{repo_name}"),
        }

        if repo_url:
            root["externalReferences"] = [
                {"type": "vcs", "url": repo_url}
            ]

        return root

    def _build_components(
        self,
        scan_data: dict[str, Any],
        findings: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Build the components list from scan data and findings."""
        components: list[dict[str, Any]] = []
        seen_refs: set[str] = set()

        # Process structured components from scan data
        for comp in scan_data.get("components", []):
            cdx_comp = self._component_to_cdx(comp)
            if cdx_comp and cdx_comp["bom-ref"] not in seen_refs:
                seen_refs.add(cdx_comp["bom-ref"])
                components.append(cdx_comp)

        # Process individual findings to capture anything not in components
        for finding in findings:
            cdx_comp = self._finding_to_cdx(finding)
            if cdx_comp and cdx_comp["bom-ref"] not in seen_refs:
                seen_refs.add(cdx_comp["bom-ref"])
                components.append(cdx_comp)

        return components

    def _component_to_cdx(self, comp: dict[str, Any]) -> dict[str, Any] | None:
        """Convert a ScanLLM component to a CycloneDX component."""
        name = comp.get("name", comp.get("display_name", ""))
        if not name:
            return None

        category = comp.get("type", comp.get("category", "library"))
        cdx_type = _CYCLONEDX_TYPE_MAP.get(category, "library")
        version = comp.get("version", "")
        bom_ref = _generate_bom_ref(name, version)

        cdx: dict[str, Any] = {
            "type": cdx_type,
            "name": name,
            "bom-ref": bom_ref,
        }

        if version:
            cdx["version"] = version

        # Package URL
        pkg_type = "npm" if comp.get("ecosystem") == "javascript" else "pypi"
        cdx["purl"] = _generate_purl(name, version, pkg_type)

        # License
        license_id = comp.get("license", _KNOWN_LICENSES.get(name.lower(), ""))
        if license_id:
            cdx["licenses"] = [{"license": {"id": license_id}}]

        # Provider / publisher
        provider = comp.get("provider", comp.get("display_name", ""))
        if provider:
            cdx["publisher"] = provider

        # Properties (ScanLLM-specific metadata)
        properties: list[dict[str, str]] = []
        properties.append({"name": "scanllm:category", "value": category})

        if comp.get("risk_level") or comp.get("severity"):
            properties.append({
                "name": "scanllm:risk_level",
                "value": comp.get("risk_level", comp.get("severity", "medium")),
            })

        files = comp.get("files", [])
        if files:
            properties.append({
                "name": "scanllm:files_count",
                "value": str(len(files)),
            })
            # Include up to 10 file references
            for i, f in enumerate(files[:10]):
                file_path = f if isinstance(f, str) else f.get("path", f.get("file", ""))
                if file_path:
                    properties.append({
                        "name": f"scanllm:file:{i}",
                        "value": file_path,
                    })

        # Model references for ML components
        models = comp.get("models", [])
        if models:
            for i, model in enumerate(models):
                model_name = model if isinstance(model, str) else model.get("name", "")
                if model_name:
                    properties.append({
                        "name": f"scanllm:model:{i}",
                        "value": model_name,
                    })

        # OWASP findings
        owasp_ids = comp.get("owasp_ids", [])
        if owasp_ids:
            properties.append({
                "name": "scanllm:owasp_mappings",
                "value": ", ".join(owasp_ids),
            })

        if properties:
            cdx["properties"] = properties

        # Model card for ML models (CycloneDX 1.6 ML-BOM extension)
        if cdx_type == "machine-learning-model":
            model_card: dict[str, Any] = {"type": "model"}

            if models:
                model_card["modelParameters"] = {
                    "modelArchitecture": ", ".join(
                        m if isinstance(m, str) else m.get("name", "") for m in models
                    )
                }

            env_vars = comp.get("env_vars", [])
            if env_vars:
                model_card["considerations"] = {
                    "environmentalConsiderations": {
                        "properties": [
                            {"name": "env_var", "value": ev} for ev in env_vars
                        ]
                    }
                }

            cdx["modelCard"] = model_card

        return cdx

    def _finding_to_cdx(self, finding: dict[str, Any]) -> dict[str, Any] | None:
        """Convert an individual finding to a CycloneDX component if applicable."""
        name = finding.get("component", finding.get("name", ""))
        if not name:
            return None

        # Skip secrets — they should not be listed as components
        if finding.get("type") == "secret" or finding.get("category") == "secret":
            return None

        category = finding.get("type", finding.get("category", "library"))
        cdx_type = _CYCLONEDX_TYPE_MAP.get(category, "library")
        version = finding.get("version", "")
        bom_ref = _generate_bom_ref(name, version)

        cdx: dict[str, Any] = {
            "type": cdx_type,
            "name": name,
            "bom-ref": bom_ref,
        }

        if version:
            cdx["version"] = version

        properties: list[dict[str, str]] = [
            {"name": "scanllm:category", "value": category},
        ]

        file_path = finding.get("file", finding.get("file_path", ""))
        if file_path:
            properties.append({"name": "scanllm:file:0", "value": file_path})

        line = finding.get("line", finding.get("line_number"))
        if line is not None:
            properties.append({"name": "scanllm:line", "value": str(line)})

        owasp = finding.get("owasp", finding.get("owasp_id", ""))
        if owasp:
            properties.append({"name": "scanllm:owasp_mappings", "value": owasp})

        cdx["properties"] = properties
        return cdx

    # ------------------------------------------------------------------
    # Dependencies
    # ------------------------------------------------------------------

    def _build_dependencies(
        self,
        scan_data: dict[str, Any],
        components: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Build CycloneDX dependency list."""
        deps: list[dict[str, Any]] = []
        bom_ref_set = {c["bom-ref"] for c in components}

        # Root depends on all top-level components
        root_ref = _generate_bom_ref(f"root:{scan_data.get('repo_name', 'unknown')}")
        root_dep: dict[str, Any] = {
            "ref": root_ref,
            "dependsOn": [c["bom-ref"] for c in components],
        }
        deps.append(root_dep)

        # Build inter-component dependencies from scan edges
        edges = scan_data.get("dependencies", scan_data.get("edges", []))
        dep_map: dict[str, list[str]] = {}

        for edge in edges:
            source_name = edge.get("source", edge.get("source_label", ""))
            target_name = edge.get("target", edge.get("target_label", ""))
            if not source_name or not target_name:
                continue

            source_ref = _generate_bom_ref(source_name)
            target_ref = _generate_bom_ref(target_name)

            if source_ref in bom_ref_set and target_ref in bom_ref_set:
                dep_map.setdefault(source_ref, []).append(target_ref)

        for ref, depends_on in dep_map.items():
            deps.append({"ref": ref, "dependsOn": depends_on})

        # Add empty dependency entries for leaf components
        referenced = {d["ref"] for d in deps}
        for comp in components:
            if comp["bom-ref"] not in referenced:
                deps.append({"ref": comp["bom-ref"], "dependsOn": []})

        return deps

    # ------------------------------------------------------------------
    # XML conversion
    # ------------------------------------------------------------------

    def _dict_to_xml(self, bom_dict: dict[str, Any]) -> ET.Element:
        """Convert the BOM dictionary to an XML ElementTree."""
        ns = "http://cyclonedx.org/schema/bom/1.6"
        root = ET.Element("bom", attrib={
            "xmlns": ns,
            "version": str(bom_dict.get("version", 1)),
            "serialNumber": bom_dict.get("serialNumber", ""),
        })

        # Metadata
        metadata = bom_dict.get("metadata", {})
        if metadata:
            meta_el = ET.SubElement(root, "metadata")
            self._add_text_element(meta_el, "timestamp", metadata.get("timestamp", ""))

            # Tools
            tools = metadata.get("tools", {})
            if tools:
                tools_el = ET.SubElement(meta_el, "tools")
                for tool_comp in tools.get("components", []):
                    tc_el = ET.SubElement(tools_el, "tool")
                    self._add_text_element(tc_el, "name", tool_comp.get("name", ""))
                    self._add_text_element(tc_el, "version", tool_comp.get("version", ""))
                    self._add_text_element(tc_el, "vendor", tool_comp.get("publisher", ""))

            # Root component
            root_comp = metadata.get("component", {})
            if root_comp:
                self._add_component_xml(meta_el, root_comp, tag="component")

            # Properties
            self._add_properties_xml(meta_el, metadata.get("properties", []))

        # Components
        components = bom_dict.get("components", [])
        if components:
            comps_el = ET.SubElement(root, "components")
            for comp in components:
                self._add_component_xml(comps_el, comp)

        # Dependencies
        dependencies = bom_dict.get("dependencies", [])
        if dependencies:
            deps_el = ET.SubElement(root, "dependencies")
            for dep in dependencies:
                dep_el = ET.SubElement(deps_el, "dependency", ref=dep.get("ref", ""))
                for child_ref in dep.get("dependsOn", []):
                    ET.SubElement(dep_el, "dependency", ref=child_ref)

        return root

    def _add_component_xml(
        self,
        parent: ET.Element,
        comp: dict[str, Any],
        tag: str = "component",
    ) -> None:
        """Add a component element to the XML tree."""
        attribs: dict[str, str] = {"type": comp.get("type", "library")}
        if "bom-ref" in comp:
            attribs["bom-ref"] = comp["bom-ref"]

        comp_el = ET.SubElement(parent, tag, attrib=attribs)
        self._add_text_element(comp_el, "name", comp.get("name", ""))

        if comp.get("version"):
            self._add_text_element(comp_el, "version", comp["version"])
        if comp.get("publisher"):
            self._add_text_element(comp_el, "publisher", comp["publisher"])
        if comp.get("purl"):
            self._add_text_element(comp_el, "purl", comp["purl"])

        # Licenses
        licenses = comp.get("licenses", [])
        if licenses:
            lics_el = ET.SubElement(comp_el, "licenses")
            for lic in licenses:
                lic_data = lic.get("license", {})
                lic_el = ET.SubElement(lics_el, "license")
                if lic_data.get("id"):
                    self._add_text_element(lic_el, "id", lic_data["id"])
                elif lic_data.get("name"):
                    self._add_text_element(lic_el, "name", lic_data["name"])

        # External references
        ext_refs = comp.get("externalReferences", [])
        if ext_refs:
            refs_el = ET.SubElement(comp_el, "externalReferences")
            for ref in ext_refs:
                ref_el = ET.SubElement(refs_el, "reference", type=ref.get("type", ""))
                self._add_text_element(ref_el, "url", ref.get("url", ""))

        # Properties
        self._add_properties_xml(comp_el, comp.get("properties", []))

    @staticmethod
    def _add_text_element(parent: ET.Element, tag: str, text: str) -> None:
        """Add a simple text child element."""
        if text:
            el = ET.SubElement(parent, tag)
            el.text = str(text)

    @staticmethod
    def _add_properties_xml(parent: ET.Element, properties: list[dict[str, str]]) -> None:
        """Add a properties block to the XML tree."""
        if not properties:
            return
        props_el = ET.SubElement(parent, "properties")
        for prop in properties:
            prop_el = ET.SubElement(props_el, "property", name=prop.get("name", ""))
            prop_el.text = str(prop.get("value", ""))
