"""Compatibility shim: re-exports the shared implementation from ``core``.

This module used to be a byte-identical copy of ``core.scanner.secret_scanner``. The two
copies drifted the moment either was fixed -- false-positive fixes landed in
``core`` while the deployed backend kept scanning with the old rules, so the
hosted dashboard and the CLI disagreed about the same repository.

There is now exactly one implementation. Import from ``core.scanner.secret_scanner``
directly in new code; this alias exists so existing imports keep working.
"""
from __future__ import annotations

from core.scanner.secret_scanner import SecretScanner

__all__ = ["SecretScanner"]
