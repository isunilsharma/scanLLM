"""
Graph analysis for ScanLLM dependency graphs.

Provides concentration risk, blast radius, critical path, circular
dependency, and single-point-of-failure analysis on the AI component
dependency graph.
"""

from __future__ import annotations

import logging
from collections import Counter
from typing import Any

import networkx as nx

logger = logging.getLogger(__name__)


class GraphAnalyzer:
    """Analyses a ``networkx.DiGraph`` of AI components for risk signals."""

    def analyze(self, graph: nx.DiGraph) -> dict[str, Any]:
        """Run all analyses on *graph* and return a consolidated report.

        Parameters
        ----------
        graph:
            A DiGraph produced by :class:`GraphBuilder`.  Each node is
            expected to carry ``type``, ``provider``, and ``label`` attributes.

        Returns
        -------
        dict
            Keys: ``concentration_risk``, ``blast_radius``,
            ``critical_paths``, ``circular_deps``,
            ``single_points_of_failure``.
        """
        result: dict[str, Any] = {
            "concentration_risk": self._concentration_risk(graph),
            "blast_radius": self._blast_radius(graph),
            "critical_paths": self._critical_paths(graph),
            "circular_deps": self._circular_deps(graph),
            "single_points_of_failure": self._single_points_of_failure(graph),
        }

        logger.info(
            "Graph analysis complete: %d nodes, %d edges, %d circular deps detected",
            graph.number_of_nodes(),
            graph.number_of_edges(),
            len(result["circular_deps"]),
        )
        return result

    # ------------------------------------------------------------------
    # Concentration risk
    # ------------------------------------------------------------------

    @staticmethod
    def _concentration_risk(graph: nx.DiGraph) -> dict[str, Any]:
        """Calculate percentage of nodes dependent on each provider.

        Returns a dict with per-provider share and a boolean flag
        indicating whether the repo is dangerously concentrated
        (any single provider > 80 %).
        """
        if graph.number_of_nodes() == 0:
            return {
                "providers": {},
                "highest_provider": None,
                "highest_share": 0.0,
                "is_concentrated": False,
            }

        provider_counts: Counter[str] = Counter()
        for _nid, data in graph.nodes(data=True):
            provider = (data.get("provider") or "unknown").lower()
            provider_counts[provider] += 1

        total = graph.number_of_nodes()
        providers = {
            prov: {
                "count": cnt,
                "share": round(cnt / total * 100, 1),
            }
            for prov, cnt in provider_counts.most_common()
        }

        highest_prov, highest_cnt = provider_counts.most_common(1)[0]
        highest_share = round(highest_cnt / total * 100, 1)

        return {
            "providers": providers,
            "highest_provider": highest_prov,
            "highest_share": highest_share,
            "is_concentrated": highest_share > 80.0,
        }

    # ------------------------------------------------------------------
    # Blast radius
    # ------------------------------------------------------------------

    @staticmethod
    def _blast_radius(graph: nx.DiGraph) -> dict[str, dict[str, Any]]:
        """For each node, compute how many other nodes would be affected
        if it were removed.

        Uses ``nx.descendants`` on the directed graph to find all
        transitively dependent nodes.
        """
        radii: dict[str, dict[str, Any]] = {}
        total = graph.number_of_nodes()

        for nid in graph.nodes():
            desc = nx.descendants(graph, nid)
            affected = len(desc)
            radii[nid] = {
                "label": graph.nodes[nid].get("label", nid),
                "affected_count": affected,
                "affected_ids": sorted(desc),
                "affected_pct": round(affected / total * 100, 1) if total else 0.0,
            }

        return radii

    # ------------------------------------------------------------------
    # Critical paths (longest dependency chains)
    # ------------------------------------------------------------------

    @staticmethod
    def _critical_paths(graph: nx.DiGraph) -> list[dict[str, Any]]:
        """Identify the longest dependency chains in the graph.

        For DAGs, uses ``nx.dag_longest_path``.  For graphs with cycles
        the function falls back to all-pairs-shortest-path analysis on the
        condensation DAG (treating each SCC as a single super-node).

        Returns a list of paths sorted by length (longest first), capped
        at the top 10.
        """
        if graph.number_of_nodes() == 0:
            return []

        # If the graph is a DAG we can use the efficient built-in.
        if nx.is_directed_acyclic_graph(graph):
            path = nx.dag_longest_path(graph)
            if path:
                return [_path_to_dict(graph, path)]
            return []

        # Graph has cycles — condense SCCs, then find longest path in DAG.
        condensation = nx.condensation(graph)
        if condensation.number_of_nodes() == 0:
            return []

        dag_path = nx.dag_longest_path(condensation)
        # Map super-node indices back to original node ids.
        scc_members = nx.get_node_attributes(condensation, "members")

        expanded_path: list[str] = []
        for scc_idx in dag_path:
            members = sorted(scc_members.get(scc_idx, set()))
            expanded_path.extend(members)

        if expanded_path:
            return [_path_to_dict(graph, expanded_path)]
        return []

    # ------------------------------------------------------------------
    # Circular dependencies
    # ------------------------------------------------------------------

    @staticmethod
    def _circular_deps(graph: nx.DiGraph) -> list[dict[str, Any]]:
        """Detect circular dependencies (simple cycles) in the graph.

        Returns a list of cycles, each described as an ordered list of
        node labels.  Capped at 50 cycles to avoid combinatorial blowup
        in dense graphs.
        """
        cycles: list[dict[str, Any]] = []
        try:
            for cycle in nx.simple_cycles(graph):
                if len(cycles) >= 50:
                    logger.warning("Cycle detection capped at 50 cycles")
                    break
                labels = [graph.nodes[n].get("label", n) for n in cycle]
                cycles.append({
                    "node_ids": cycle,
                    "labels": labels,
                    "length": len(cycle),
                })
        except nx.NetworkXError:
            logger.exception("Cycle detection failed")

        return sorted(cycles, key=lambda c: c["length"], reverse=True)

    # ------------------------------------------------------------------
    # Single points of failure (betweenness centrality)
    # ------------------------------------------------------------------

    @staticmethod
    def _single_points_of_failure(graph: nx.DiGraph) -> list[dict[str, Any]]:
        """Find nodes with the highest betweenness centrality.

        These are the nodes whose removal would most disrupt the flow of
        information through the dependency graph.

        Returns the top-5 nodes sorted by descending centrality.
        """
        if graph.number_of_nodes() < 2:
            return []

        centrality = nx.betweenness_centrality(graph, weight="weight")

        ranked = sorted(centrality.items(), key=lambda x: x[1], reverse=True)

        results: list[dict[str, Any]] = []
        for nid, score in ranked[:5]:
            if score <= 0:
                continue
            node_data = graph.nodes[nid]
            results.append({
                "node_id": nid,
                "label": node_data.get("label", nid),
                "type": node_data.get("type", "unknown"),
                "centrality_score": round(score, 4),
            })

        return results


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _path_to_dict(graph: nx.DiGraph, path: list[str]) -> dict[str, Any]:
    """Convert a list of node ids into a serialisable path descriptor."""
    return {
        "length": len(path),
        "node_ids": path,
        "labels": [graph.nodes[n].get("label", n) for n in path if n in graph],
    }
