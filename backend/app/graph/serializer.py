"""
Graph serializer for ScanLLM.

Converts a ``networkx.DiGraph`` into the JSON structure consumed by
React Flow on the frontend, including automatic layout positioning
via a category-based layered algorithm.

Supports both flat and clustered graphs.  Clustered nodes include
``children``, ``is_cluster``, and ``model_count`` in their data
payload so the frontend can render expandable provider badges.
"""

from __future__ import annotations

import logging
from typing import Any

import networkx as nx

logger = logging.getLogger(__name__)

# Layout constants
_NODE_WIDTH = 240
_NODE_HEIGHT = 90
_HORIZONTAL_GAP = 320
_VERTICAL_GAP = 140

# Category ordering for deterministic left-to-right layout.
# Categories earlier in the list appear further left.
_CATEGORY_LAYER: dict[str, int] = {
    "config_reference": 0,
    "secret": 0,
    "ai_package": 1,
    "orchestration_framework": 1,
    "agent_tool": 2,
    "mcp_server": 2,
    "llm_provider": 3,
    "embedding_service": 3,
    "inference_server": 3,
    "vector_db": 4,
}


class GraphSerializer:
    """Serializes a ``networkx.DiGraph`` to React Flow JSON."""

    def to_react_flow(self, graph: nx.DiGraph) -> dict[str, Any]:
        """Convert *graph* to a React Flow compatible dict.

        The output contains ``nodes`` and ``edges`` lists ready for
        direct consumption by ``<ReactFlow>`` on the frontend.

        Layout is computed using a category-based layered algorithm
        that groups nodes by their component type into vertical columns,
        producing a clean left-to-right flow.

        Parameters
        ----------
        graph:
            A DiGraph produced by :class:`GraphBuilder`.

        Returns
        -------
        dict
            ``{"nodes": [...], "edges": [...]}``
        """
        if graph.number_of_nodes() == 0:
            return {"nodes": [], "edges": []}

        positions = self._compute_layout(graph)
        nodes = self._serialize_nodes(graph, positions)
        edges = self._serialize_edges(graph)

        logger.info(
            "Serialized graph to React Flow: %d nodes, %d edges",
            len(nodes),
            len(edges),
        )
        return {"nodes": nodes, "edges": edges}

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _compute_layout(self, graph: nx.DiGraph) -> dict[str, dict[str, float]]:
        """Assign (x, y) positions using a category-based layered layout.

        1. Assign each node to a layer based on its component type.
        2. Within each layer, space nodes vertically.
        3. Layers are spaced horizontally (left -> right).
        """
        layers = self._assign_layers(graph)

        # Group nodes by layer.
        layer_groups: dict[int, list[str]] = {}
        for nid, layer in layers.items():
            layer_groups.setdefault(layer, []).append(nid)

        # Sort nodes within each layer alphabetically by label for stability.
        for layer in layer_groups:
            layer_groups[layer].sort(
                key=lambda n: graph.nodes[n].get("label", n)
            )

        positions: dict[str, dict[str, float]] = {}
        for layer_idx in sorted(layer_groups):
            members = layer_groups[layer_idx]
            # Centre the layer vertically.
            total_height = len(members) * _VERTICAL_GAP
            start_y = -total_height / 2

            for rank, nid in enumerate(members):
                positions[nid] = {
                    "x": float(layer_idx * _HORIZONTAL_GAP),
                    "y": float(start_y + rank * _VERTICAL_GAP),
                }

        return positions

    @staticmethod
    def _assign_layers(graph: nx.DiGraph) -> dict[str, int]:
        """Assign a layer index to every node.

        Uses the node's component type to determine its layer via the
        ``_CATEGORY_LAYER`` mapping.  This produces a stable, readable
        layout regardless of graph topology.  Nodes with unknown types
        are placed in layer 0.
        """
        layers: dict[str, int] = {}
        for nid, data in graph.nodes(data=True):
            ctype = data.get("type", "unknown")
            layers[nid] = _CATEGORY_LAYER.get(ctype, 0)
        return layers

    # ------------------------------------------------------------------
    # Node serialization
    # ------------------------------------------------------------------

    @staticmethod
    def _serialize_nodes(
        graph: nx.DiGraph,
        positions: dict[str, dict[str, float]],
    ) -> list[dict[str, Any]]:
        """Convert graph nodes to React Flow node objects.

        Clustered nodes include ``children``, ``is_cluster``, and
        ``model_count`` fields in their data payload.
        """
        nodes: list[dict[str, Any]] = []
        for nid, data in graph.nodes(data=True):
            pos = positions.get(nid, {"x": 0.0, "y": 0.0})
            node_type = data.get("type", "default")
            children = data.get("children", [])
            is_cluster = data.get("is_cluster", False)
            files = data.get("files", [])

            react_node: dict[str, Any] = {
                "id": nid,
                "type": node_type,
                "position": {"x": pos["x"], "y": pos["y"]},
                "data": {
                    "label": data.get("label", nid),
                    "provider": data.get("provider", ""),
                    "files": files,
                    "file_count": len(files),
                    "risk_score": data.get("risk_score", 0),
                    "component_type": node_type,
                    "metadata": data.get("metadata", {}),
                    "children": children,
                    "is_cluster": is_cluster,
                    "model_count": len(children) if is_cluster else 0,
                },
            }
            nodes.append(react_node)

        return nodes

    # ------------------------------------------------------------------
    # Edge serialization
    # ------------------------------------------------------------------

    @staticmethod
    def _serialize_edges(graph: nx.DiGraph) -> list[dict[str, Any]]:
        """Convert graph edges to React Flow edge objects."""
        edges: list[dict[str, Any]] = []
        for src, tgt, data in graph.edges(data=True):
            rel = data.get("relationship_type", "related")
            animated = rel in ("feeds-into", "has-access-to")

            edge_type_map: dict[str, str] = {
                "co-located": "default",
                "import-chain": "step",
                "feeds-into": "smoothstep",
                "configures": "default",
                "has-access-to": "smoothstep",
            }

            react_edge: dict[str, Any] = {
                "id": f"e-{src}-{tgt}",
                "source": src,
                "target": tgt,
                "label": rel,
                "type": edge_type_map.get(rel, "default"),
                "animated": animated,
            }
            edges.append(react_edge)

        return edges
