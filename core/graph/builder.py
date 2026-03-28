"""
Dependency graph builder for ScanLLM.

Constructs a networkx DiGraph from scanner findings, representing
AI components as nodes and their relationships as edges.
"""

from __future__ import annotations

import hashlib
import logging
from collections import defaultdict
from pathlib import PurePosixPath
from typing import Any

import networkx as nx

logger = logging.getLogger(__name__)


def _node_id(component_type: str, provider: str, label: str) -> str:
    """Generate a deterministic node ID from component attributes."""
    raw = f"{component_type}::{provider}::{label}".lower()
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def _module_key(file_path: str) -> str:
    """Extract the parent directory as a module key for proximity heuristics."""
    return str(PurePosixPath(file_path).parent)


def _derive_label(finding: dict[str, Any]) -> str:
    """Build a human-readable label from a finding dict.

    Prefers 'model_name' when available (e.g. "OpenAI GPT-4o"),
    otherwise falls back to provider + framework.
    """
    provider = (finding.get("provider") or "").strip()
    model = (finding.get("model_name") or "").strip()
    framework = (finding.get("framework") or "").strip()

    if provider and model:
        return f"{provider} {model}"
    if provider:
        return provider
    if framework:
        return framework
    return finding.get("pattern_name", "Unknown Component")


# ---------------------------------------------------------------------------
# Relationship detection helpers
# ---------------------------------------------------------------------------

_EMBEDDING_TYPES = {"embedding_service"}
_VECTOR_DB_TYPES = {"vector_db"}
_AGENT_TYPES = {"agent_tool"}
_TOOL_TYPES = {"agent_tool", "mcp_server"}
_FRAMEWORK_TYPES = {"orchestration_framework"}
_PROVIDER_TYPES = {"llm_provider", "embedding_service", "inference_server"}


class GraphBuilder:
    """Builds a ``networkx.DiGraph`` from a list of scanner findings.

    Each unique AI component becomes a node.  Edges encode relationships
    such as co-location, data flow, configuration references, and
    agent-tool bindings.
    """

    def build(self, findings: list[dict[str, Any]]) -> nx.DiGraph:
        """Construct the dependency graph.

        Parameters
        ----------
        findings:
            A list of finding dicts produced by the scanning engine.
            Expected keys per finding: ``file_path``, ``line_number``,
            ``framework``, ``pattern_category``, ``pattern_name``,
            ``component_type``, ``provider``, ``model_name``.
            Additional optional keys are preserved in node metadata.

        Returns
        -------
        nx.DiGraph
            The constructed dependency graph.
        """
        graph = nx.DiGraph()

        # ---- Phase 1: Create nodes ------------------------------------------
        # Accumulate file references per logical node.
        node_map: dict[str, dict[str, Any]] = {}
        # Track which nodes appear in which files and modules.
        file_to_nodes: dict[str, list[str]] = defaultdict(list)
        module_to_nodes: dict[str, list[str]] = defaultdict(list)

        for finding in findings:
            component_type: str = finding.get("component_type", "unknown")
            provider: str = finding.get("provider", "")
            label: str = _derive_label(finding)
            nid: str = _node_id(component_type, provider, label)

            file_ref = {
                "file_path": finding.get("file_path", ""),
                "line_number": finding.get("line_number"),
            }

            if nid not in node_map:
                node_map[nid] = {
                    "id": nid,
                    "type": component_type,
                    "label": label,
                    "provider": provider,
                    "files": [],
                    "metadata": {},
                    "risk_score": 0,
                }

            # Deduplicate file references.
            if file_ref not in node_map[nid]["files"]:
                node_map[nid]["files"].append(file_ref)

            # Accumulate extra metadata.
            for key in ("framework", "pattern_category", "pattern_name", "model_name"):
                val = finding.get(key)
                if val:
                    node_map[nid]["metadata"].setdefault(key, set())
                    node_map[nid]["metadata"][key].add(val)

            # Index for edge detection.
            fpath = finding.get("file_path", "")
            if fpath:
                file_to_nodes[fpath].append(nid)
                module_to_nodes[_module_key(fpath)].append(nid)

        # Serialize metadata sets to sorted lists for JSON compatibility.
        for ndata in node_map.values():
            ndata["metadata"] = {
                k: sorted(v) if isinstance(v, set) else v
                for k, v in ndata["metadata"].items()
            }

        # Add nodes to graph.
        for nid, ndata in node_map.items():
            graph.add_node(nid, **ndata)

        logger.info("Graph built with %d nodes from %d findings", len(node_map), len(findings))

        # ---- Phase 2: Build edges -------------------------------------------
        edge_set: set[tuple[str, str, str]] = set()

        self._add_colocation_edges(file_to_nodes, node_map, edge_set)
        self._add_module_edges(module_to_nodes, node_map, edge_set)
        self._add_data_flow_edges(file_to_nodes, node_map, edge_set)
        self._add_config_edges(file_to_nodes, node_map, edge_set)
        self._add_agent_tool_edges(file_to_nodes, node_map, edge_set)

        for src, tgt, rel in edge_set:
            weight = self._edge_weight(rel)
            graph.add_edge(src, tgt, relationship_type=rel, weight=weight)

        logger.info("Graph has %d edges", graph.number_of_edges())
        return graph

    # ------------------------------------------------------------------
    # Edge-building helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _add_colocation_edges(
        file_to_nodes: dict[str, list[str]],
        node_map: dict[str, dict[str, Any]],
        edge_set: set[tuple[str, str, str]],
    ) -> None:
        """Two different AI components in the same file are co-located."""
        for _fpath, nids in file_to_nodes.items():
            unique = list(dict.fromkeys(nids))
            for i, a in enumerate(unique):
                for b in unique[i + 1 :]:
                    if a != b:
                        edge_set.add((a, b, "co-located"))

    @staticmethod
    def _add_module_edges(
        module_to_nodes: dict[str, list[str]],
        node_map: dict[str, dict[str, Any]],
        edge_set: set[tuple[str, str, str]],
    ) -> None:
        """Framework in one file + provider in another file in the same module
        implies an import-chain relationship."""
        for _module, nids in module_to_nodes.items():
            unique = list(dict.fromkeys(nids))
            frameworks = [n for n in unique if node_map[n]["type"] in _FRAMEWORK_TYPES]
            providers = [n for n in unique if node_map[n]["type"] in _PROVIDER_TYPES]
            for fw in frameworks:
                for prov in providers:
                    if fw != prov:
                        edge_set.add((fw, prov, "import-chain"))

    @staticmethod
    def _add_data_flow_edges(
        file_to_nodes: dict[str, list[str]],
        node_map: dict[str, dict[str, Any]],
        edge_set: set[tuple[str, str, str]],
    ) -> None:
        """Embedding service + vector DB in the same file/module → feeds-into."""
        for _fpath, nids in file_to_nodes.items():
            unique = list(dict.fromkeys(nids))
            embeddings = [n for n in unique if node_map[n]["type"] in _EMBEDDING_TYPES]
            vdbs = [n for n in unique if node_map[n]["type"] in _VECTOR_DB_TYPES]
            for emb in embeddings:
                for vdb in vdbs:
                    edge_set.add((emb, vdb, "feeds-into"))

            # Also: llm_provider producing output consumed by vector_db in same file
            llms = [n for n in unique if node_map[n]["type"] == "llm_provider"]
            for llm in llms:
                for vdb in vdbs:
                    edge_set.add((llm, vdb, "feeds-into"))

    @staticmethod
    def _add_config_edges(
        file_to_nodes: dict[str, list[str]],
        node_map: dict[str, dict[str, Any]],
        edge_set: set[tuple[str, str, str]],
    ) -> None:
        """Config-file references pointing to the same provider as code → configures."""
        config_exts = {".yaml", ".yml", ".json", ".toml", ".env"}
        code_exts = {".py", ".js", ".ts", ".jsx", ".tsx"}

        config_nodes: dict[str, set[str]] = defaultdict(set)
        code_nodes: dict[str, set[str]] = defaultdict(set)

        for fpath, nids in file_to_nodes.items():
            suffix = PurePosixPath(fpath).suffix.lower()
            bucket = config_nodes if suffix in config_exts else code_nodes if suffix in code_exts else None
            if bucket is not None:
                for nid in dict.fromkeys(nids):
                    provider = node_map[nid].get("provider", "").lower()
                    if provider:
                        bucket[provider].add(nid)

        for provider, cfg_nids in config_nodes.items():
            code_nids = code_nodes.get(provider, set())
            for cfg in cfg_nids:
                for code in code_nids:
                    if cfg != code:
                        edge_set.add((cfg, code, "configures"))

    @staticmethod
    def _add_agent_tool_edges(
        file_to_nodes: dict[str, list[str]],
        node_map: dict[str, dict[str, Any]],
        edge_set: set[tuple[str, str, str]],
    ) -> None:
        """Agent nodes with tool-type nodes in the same file → has-access-to."""
        for _fpath, nids in file_to_nodes.items():
            unique = list(dict.fromkeys(nids))
            agents = [n for n in unique if node_map[n]["type"] in _AGENT_TYPES]
            others = [n for n in unique if node_map[n]["type"] not in _AGENT_TYPES]
            for agent in agents:
                for other in others:
                    edge_set.add((agent, other, "has-access-to"))

    @staticmethod
    def _edge_weight(relationship_type: str) -> float:
        """Assign edge weight based on relationship type.

        Higher weight indicates a stronger / more risky coupling.
        """
        weights: dict[str, float] = {
            "co-located": 0.3,
            "import-chain": 0.5,
            "feeds-into": 0.8,
            "configures": 0.4,
            "has-access-to": 0.9,
        }
        return weights.get(relationship_type, 0.5)
