"""Backward-compatible imports — delegates to core.scoring."""
import sys
from pathlib import Path

_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_root))

from core.scoring import RiskEngine, OwaspMapper

__all__ = ["RiskEngine", "OwaspMapper"]
