"""
Dependency graph builder for ScanLLM.

Constructs a networkx DiGraph from scanner findings, representing
AI components as nodes and their relationships as edges.

Supports two modes:
- **flat** (original): every unique component is its own node.
- **clustered** (default): model-level nodes are grouped under their
  provider, producing a much more readable graph for repos with many
  model references.
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


def _cluster_node_id(component_type: str, provider: str) -> str:
    """Generate a deterministic node ID for a provider-level cluster node."""
    raw = f"cluster::{component_type}::{provider}".lower()
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

# Component types whose nodes should be clustered by provider when they
# have multiple model-level variants (e.g. "openai gpt-4o", "openai o1-mini").
_CLUSTERABLE_TYPES = {"llm_provider", "embedding_service", "inference_server"}


class GraphBuilder:
    """Builds a ``networkx.DiGraph`` from a list of scanner findings.

    Each unique AI component becomes a node.  Edges encode relationships
    such as co-location, data flow, configuration references, and
    agent-tool bindings.
    """

    def build(
        self,
        findings: list[dict[str, Any]],
        *,
        clustered: bool = True,
    ) -> nx.DiGraph:
        """Construct the dependency graph.

        Parameters
        ----------
        findings:
            A list of finding dicts produced by the scanning engine.
            Expected keys per finding: ``file_path``, ``line_number``,
            ``framework``, ``pattern_category``, ``pattern_name``,
            ``component_type``, ``provider``, ``model_name``.
            Additional optional keys are preserved in node metadata.
        clustered:
            When *True* (default) model-level nodes for the same provider
            are merged into a single provider-level cluster node.  The
            individual model names are stored in the node's ``children``
            list.  Set to *False* for the original flat behaviour.

        Returns
        -------
        nx.DiGraph
            The constructed dependency graph.
        """
        # Always build the flat graph first.
        flat_graph = self._build_flat(findings)

        if not clustered:
            return flat_graph

        return self._collapse_to_clusters(flat_graph)

    # ------------------------------------------------------------------
    # Flat graph construction (original logic)
    # ------------------------------------------------------------------

    def _build_flat(self, findings: list[dict[str, Any]]) -> nx.DiGraph:
        """Build the original per-component flat graph."""
        graph = nx.DiGraph()

        # ---- Phase 1: Create nodes ------------------------------------------
        node_map: dict[str, dict[str, Any]] = {}
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

        logger.info("Flat graph built with %d nodes from %d findings", len(node_map), len(findings))

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

        logger.info("Flat graph has %d edges", graph.number_of_edges())
        return graph

    # ------------------------------------------------------------------
    # Clustered graph construction
    # ------------------------------------------------------------------

    @staticmethod
    def _collapse_to_clusters(flat_graph: nx.DiGraph) -> nx.DiGraph:
        """Collapse model-level nodes into provider-level cluster nodes.

        For each provider that has multiple model-level nodes (e.g.
        ``openai gpt-4o``, ``openai o1-mini``), create a single cluster
        node with all model names stored in ``children``.  Non-clusterable
        node types (frameworks, vector DBs, agents, secrets, etc.) remain
        as individual nodes.

        Edges are re-mapped so they connect cluster nodes.  Co-located
        edges between nodes that map to the *same* cluster are dropped.
        """
        clustered = nx.DiGraph()

        # Step 1: Decide which flat nodes map to which cluster node.
        # flat_nid -> cluster_nid (or same nid if not clustered)
        nid_to_cluster: dict[str, str] = {}
        cluster_data: dict[str, dict[str, Any]] = {}

        for nid, data in flat_graph.nodes(data=True):
            ctype = data.get("type", "unknown")
            provider = (data.get("provider") or "").strip().lower()

            # Only cluster types that tend to have many model variants
            # AND have a non-empty provider.
            if ctype in _CLUSTERABLE_TYPES and provider:
                cid = _cluster_node_id(ctype, provider)
                nid_to_cluster[nid] = cid

                if cid not in cluster_data:
                    # Use the provider name (title-cased) as the label.
                    display_label = provider.replace("_", " ").title()
                    cluster_data[cid] = {
                        "id": cid,
                        "type": ctype,
                        "label": display_label,
                        "provider": provider,
                        "files": [],
                        "children": [],
                        "metadata": {},
                        "risk_score": 0,
                        "is_cluster": True,
                    }

                cd = cluster_data[cid]
                # Merge model names into children list.
                model_names = data.get("metadata", {}).get("model_name", [])
                if isinstance(model_names, list):
                    for m in model_names:
                        if m and m not in cd["children"]:
                            cd["children"].append(m)
                # If the flat node label contains a model name not yet tracked
                label = data.get("label", "")
                if label and label != cd["label"] and label not in cd["children"]:
                    cd["children"].append(label)

                # Merge files.
                for fref in data.get("files", []):
                    if fref not in cd["files"]:
                        cd["files"].append(fref)

                # Merge metadata.
                for key, vals in data.get("metadata", {}).items():
                    cd["metadata"].setdefault(key, [])
                    if isinstance(vals, list):
                        for v in vals:
                            if v not in cd["metadata"][key]:
                                cd["metadata"][key].append(v)
                    else:
                        if vals not in cd["metadata"][key]:
                            cd["metadata"][key].append(vals)

                # Take the max risk score.
                cd["risk_score"] = max(cd["risk_score"], data.get("risk_score", 0))
            else:
                # Non-clusterable: keep as-is.
                nid_to_cluster[nid] = nid
                cluster_data[nid] = dict(data)
                cluster_data[nid]["is_cluster"] = False

        # Sort children alphabetically for stability.
        for cd in cluster_data.values():
            if "children" in cd:
                cd["children"] = sorted(cd["children"])

        # Step 2: Add nodes to the clustered graph.
        for cid, cdata in cluster_data.items():
            clustered.add_node(cid, **cdata)

        # Step 3: Re-map edges, dropping self-loops and co-located-only
        # edges between nodes of the same category.
        edge_set: set[tuple[str, str, str]] = set()

        for src, tgt, data in flat_graph.edges(data=True):
            csrc = nid_to_cluster.get(src, src)
            ctgt = nid_to_cluster.get(tgt, tgt)
            rel = data.get("relationship_type", "related")

            # Drop self-loops created by clustering.
            if csrc == ctgt:
                continue

            # Drop co-located edges between nodes of the same component
            # category -- these create the hairball.
            if rel == "co-located":
                src_type = cluster_data.get(csrc, {}).get("type", "")
                tgt_type = cluster_data.get(ctgt, {}).get("type", "")
                if src_type == tgt_type:
                    continue

            edge_set.add((csrc, ctgt, rel))

        for src, tgt, rel in edge_set:
            weight = GraphBuilder._edge_weight(rel)
            clustered.add_edge(src, tgt, relationship_type=rel, weight=weight)

        logger.info(
            "Clustered graph: %d nodes, %d edges (collapsed from %d flat nodes, %d flat edges)",
            clustered.number_of_nodes(),
            clustered.number_of_edges(),
            flat_graph.number_of_nodes(),
            flat_graph.number_of_edges(),
        )
        return clustered

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
        """Embedding service + vector DB in the same file/module -> feeds-into."""
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
        """Config-file references pointing to the same provider as code -> configures."""
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
        """Agent nodes with tool-type nodes in the same file -> has-access-to."""
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
