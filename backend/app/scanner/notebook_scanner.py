"""
Jupyter Notebook (.ipynb) scanner. Extracts code cells and delegates to
PythonScanner for AST-based analysis.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .python_scanner import PythonScanner

logger = logging.getLogger(__name__)


class NotebookScanner:
    """Scan Jupyter Notebook files for AI/LLM patterns."""

    def scan_file(
        self,
        file_path: Path,
        relative_path: str,
        signatures: dict[str, Any],
        python_scanner: PythonScanner,
    ) -> list[dict[str, Any]]:
        """Parse an .ipynb file, extract code cells, and scan each with PythonScanner.

        Args:
            file_path: Absolute path to the notebook file.
            relative_path: Path relative to the repo root (used in findings).
            signatures: The loaded AI signatures dict.
            python_scanner: An instance of PythonScanner to reuse.

        Returns:
            A list of Finding dicts, one per detected pattern.
        """
        try:
            source = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            logger.warning("Failed to read %s: %s", file_path, exc)
            return []

        try:
            notebook = json.loads(source)
        except json.JSONDecodeError as exc:
            logger.debug("Invalid notebook JSON in %s: %s", relative_path, exc)
            return []

        cells = notebook.get("cells", [])
        if not isinstance(cells, list):
            logger.debug("No cells array in %s", relative_path)
            return []

        findings: list[dict[str, Any]] = []
        cumulative_line_offset = 0

        for cell_index, cell in enumerate(cells):
            if not isinstance(cell, dict):
                continue
            cell_type = cell.get("cell_type", "")
            cell_source = self._get_cell_source(cell)

            if cell_type != "code":
                # Skip non-code cells but still track line offsets
                cumulative_line_offset += cell_source.count("\n") + 1
                continue

            if not cell_source.strip():
                cumulative_line_offset += cell_source.count("\n") + 1
                continue

            # Scan the cell source with PythonScanner
            cell_findings = python_scanner.scan_source(
                source=cell_source,
                relative_path=relative_path,
                signatures=signatures,
                line_offset=0,  # line numbers relative to cell
            )

            # Annotate each finding with cell metadata
            for finding in cell_findings:
                finding["cell_index"] = cell_index
                finding["cell_line_offset"] = cumulative_line_offset
                # Adjust line_number to be global within the notebook
                finding["line_number"] = finding["line_number"] + cumulative_line_offset
                # Enhance pattern description with cell info
                original_desc = finding.get("pattern_description", "")
                finding["pattern_description"] = (
                    f"[Cell {cell_index}] {original_desc}"
                )
                findings.append(finding)

            cumulative_line_offset += cell_source.count("\n") + 1

        return findings

    # ── Helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _get_cell_source(cell: dict[str, Any]) -> str:
        """Extract the source code string from a notebook cell."""
        source = cell.get("source", "")
        if isinstance(source, list):
            return "".join(source)
        if isinstance(source, str):
            return source
        return ""
