"""Backward-compatible imports — delegates to core.scanner."""
import sys
from pathlib import Path

# Ensure core/ is importable
_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_root))

from core.scanner import (
    ScanEngine,
    PythonScanner,
    JSScanner,
    ConfigScanner,
    DependencyScanner,
    NotebookScanner,
    SecretScanner,
)

__all__ = [
    "ScanEngine",
    "PythonScanner",
    "JSScanner",
    "ConfigScanner",
    "DependencyScanner",
    "NotebookScanner",
    "SecretScanner",
]
