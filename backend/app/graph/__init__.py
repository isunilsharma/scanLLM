"""Backward-compatible imports — delegates to core.graph."""
import sys
from pathlib import Path

_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_root))

from core.graph import GraphBuilder, GraphAnalyzer, GraphSerializer

__all__ = ["GraphBuilder", "GraphAnalyzer", "GraphSerializer"]
