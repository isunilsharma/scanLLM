"""Jupyter notebook (.ipynb) scanner"""
import json
import logging
import tempfile
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class NotebookScanner:
    """Parse .ipynb files and scan code cells for AI patterns"""

    def scan_file(self, file_path: Path, relative_path: str, signatures: dict = None,
                  python_scanner=None) -> List[Dict[str, Any]]:
        findings = []

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            notebook = json.loads(content)
        except Exception as e:
            logger.debug(f"Failed to parse notebook {relative_path}: {e}")
            return findings

        cells = notebook.get("cells", [])

        for cell_idx, cell in enumerate(cells):
            if cell.get("cell_type") != "code":
                continue

            source = cell.get("source", [])
            if isinstance(source, list):
                code = "".join(source)
            else:
                code = str(source)

            if not code.strip():
                continue

            # If we have a Python scanner, use it on the cell code
            if python_scanner:
                cell_findings = self._scan_cell_with_python_scanner(
                    code, relative_path, cell_idx, python_scanner, signatures
                )
                findings.extend(cell_findings)
            else:
                # Fallback: basic pattern matching
                cell_findings = self._basic_scan_cell(code, relative_path, cell_idx)
                findings.extend(cell_findings)

        return findings

    def _scan_cell_with_python_scanner(self, code: str, relative_path: str,
                                        cell_idx: int, python_scanner, signatures: dict) -> List[Dict[str, Any]]:
        """Write cell code to temp file and run Python scanner on it"""
        findings = []
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(code)
                f.flush()
                temp_path = Path(f.name)

            cell_findings = python_scanner.scan_file(temp_path, relative_path, signatures)

            # Adjust line numbers to include cell index info
            for finding in cell_findings:
                finding["line_text"] = f"[Cell {cell_idx}] {finding['line_text']}"
                finding["pattern_description"] = f"[Notebook Cell {cell_idx}] {finding.get('pattern_description', '')}"
            findings.extend(cell_findings)

        except Exception as e:
            logger.debug(f"Failed to scan notebook cell {cell_idx}: {e}")
        finally:
            try:
                temp_path.unlink(missing_ok=True)
            except Exception:
                pass

        return findings

    def _basic_scan_cell(self, code: str, relative_path: str, cell_idx: int) -> List[Dict[str, Any]]:
        """Basic pattern matching for notebook cells without Python scanner"""
        import re
        findings = []

        patterns = [
            (r"\bfrom openai import\b|\bimport openai\b", "openai", "llm_provider"),
            (r"\bfrom anthropic import\b|\bimport anthropic\b", "anthropic", "llm_provider"),
            (r"\bfrom langchain\b|\bimport langchain\b", "langchain", "orchestration_framework"),
            (r"\bfrom transformers import\b", "transformers", "llm_provider"),
            (r"\bclient\.chat\.completions\.create\b", "openai", "llm_provider"),
            (r"\bclient\.messages\.create\b", "anthropic", "llm_provider"),
            (r"\bfrom chromadb import\b|\bimport chromadb\b", "chromadb", "vector_db"),
            (r"\bfrom pinecone import\b|\bimport pinecone\b", "pinecone", "vector_db"),
        ]

        lines = code.split("\n")
        for line_num, line in enumerate(lines, start=1):
            for pattern, framework, comp_type in patterns:
                if re.search(pattern, line):
                    findings.append({
                        "file_path": relative_path,
                        "line_number": line_num,
                        "line_text": f"[Cell {cell_idx}] {line.strip()[:500]}",
                        "framework": framework,
                        "pattern_name": f"notebook_{framework}_import",
                        "pattern_category": "client_init",
                        "pattern_severity": "low",
                        "pattern_description": f"[Notebook Cell {cell_idx}] {framework} usage",
                        "snippet": line.strip(),
                        "model_name": None, "temperature": None, "max_tokens": None,
                        "is_streaming": False, "has_tools": False,
                        "component_type": comp_type,
                        "provider": framework,
                        "owasp_id": None,
                    })

        return findings
