"""
Graph serializer for ScanLLM.

Converts a ``networkx.DiGraph`` into the JSON structure consumed by
React Flow on the frontend, including automatic layout positioning
via a simple layered (dagre-style) algorithm.
"""

from __future__ import annotations

import logging
from typing import Any

import networkx as nx

logger = logging.getLogger(__name__)

# Layout constants
_NODE_WIDTH = 220
_NODE_HEIGHT = 80
_HORIZONTAL_GAP = 280
_VERTICAL_GAP = 120


class GraphSerializer:
    """Serializes a ``networkx.DiGraph`` to React Flow JSON."""

    def to_react_flow(self, graph: nx.DiGraph) -> dict[str, Any]:
        """Convert *graph* to a React Flow compatible dict.

        The output contains ``nodes`` and ``edges`` lists ready for
        direct consumption by ``<ReactFlow>`` on the frontend.

        Layout is computed via a simplified layered layout algorithm
        that assigns layers using topological ordering (falling back
        to BFS layering when the graph contains cycles).

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
        """Assign (x, y) positions using a layered layout.

        1. Assign each node to a layer (depth from sources).
        2. Within each layer, space nodes vertically.
        3. Layers are spaced horizontally (left → right).
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

        Uses topological sort for DAGs.  For graphs with cycles, uses
        BFS from roots (nodes with in-degree 0), then assigns remaining
        nodes to the max-predecessor-layer + 1.
        """
        if nx.is_directed_acyclic_graph(graph):
            layers: dict[str, int] = {}
            for nid in nx.topological_sort(graph):
                pred_layers = [layers[p] for p in graph.predecessors(nid) if p in layers]
                layers[nid] = (max(pred_layers) + 1) if pred_layers else 0
            return layers

        # Fallback: BFS from roots.
        layers = {}
        roots = [n for n in graph.nodes() if graph.in_degree(n) == 0]
        if not roots:
            # No roots — pick the node with the highest out-degree as root.
            roots = [max(graph.nodes(), key=lambda n: graph.out_degree(n))]

        visited: set[str] = set()
        queue: list[tuple[str, int]] = [(r, 0) for r in roots]
        for r in roots:
            visited.add(r)

        while queue:
            nid, depth = queue.pop(0)
            layers[nid] = max(layers.get(nid, 0), depth)
            for succ in graph.successors(nid):
                if succ not in visited:
                    visited.add(succ)
                    queue.append((succ, depth + 1))

        # Any disconnected nodes get layer 0.
        for nid in graph.nodes():
            if nid not in layers:
                layers[nid] = 0

        return layers

    # ------------------------------------------------------------------
    # Node serialization
    # ------------------------------------------------------------------

    @staticmethod
    def _serialize_nodes(
        graph: nx.DiGraph,
        positions: dict[str, dict[str, float]],
    ) -> list[dict[str, Any]]:
        """Convert graph nodes to React Flow node objects."""
        nodes: list[dict[str, Any]] = []
        for nid, data in graph.nodes(data=True):
            pos = positions.get(nid, {"x": 0.0, "y": 0.0})
            node_type = data.get("type", "default")

            react_node: dict[str, Any] = {
                "id": nid,
                "type": node_type,
                "position": {"x": pos["x"], "y": pos["y"]},
                "data": {
                    "label": data.get("label", nid),
                    "provider": data.get("provider", ""),
                    "files": data.get("files", []),
                    "risk_score": data.get("risk_score", 0),
                    "component_type": node_type,
                    "metadata": data.get("metadata", {}),
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
