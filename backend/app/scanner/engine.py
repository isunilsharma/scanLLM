"""Compatibility shim: re-exports the shared implementation from ``core``.

This module used to be a near-copy of ``core.scanner.engine``, differing only
in import paths, a vestigial ``sys.path`` insert, and a shorter signature-file
search list. Keeping two engines meant the hosted dashboard and the CLI could
report different results for the same repository.

``core.scanner.engine`` searches a superset of the signature paths this module
used (``core/signatures/`` first, then the ``/config`` Docker mount, then the
repository ``config/`` directory), so the deployed container resolves the same
file it always did.

Import from ``core.scanner.engine`` directly in new code; this alias exists so
existing imports keep working.
"""
from __future__ import annotations

from core.scanner.engine import EXCLUDE_DIRS, PRIORITY_DIRS, SKIP_DIRS, ScanEngine

__all__ = ["ScanEngine", "EXCLUDE_DIRS", "SKIP_DIRS", "PRIORITY_DIRS"]
