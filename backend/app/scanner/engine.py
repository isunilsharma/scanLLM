"""
Scanner Engine Orchestrator — dispatches files to the appropriate scanners
and collects unified findings across the entire repository.
"""

from __future__ import annotations

import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# Add backend directory to path so we can import GitUtils from services/
_backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_backend_dir))

from app.scanner.python_scanner import PythonScanner
from app.scanner.js_scanner import JSScanner
from app.scanner.config_scanner import ConfigScanner
from app.scanner.dependency_scanner import DependencyScanner
from app.scanner.notebook_scanner import NotebookScanner
from app.scanner.secret_scanner import SecretScanner

# ── File extension / name sets ───────────────────────────────────────────────

PYTHON_EXTS: set[str] = {".py"}
JS_EXTS: set[str] = {".js", ".ts", ".jsx", ".tsx"}
CONFIG_EXTS: set[str] = {".yaml", ".yml", ".json", ".toml"}
NOTEBOOK_EXTS: set[str] = {".ipynb"}

DEP_FILENAMES: set[str] = {
    "requirements.txt", "pyproject.toml", "pipfile",
    "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
}

DOCKER_FILENAMES: set[str] = {
    "dockerfile", "docker-compose.yml", "docker-compose.yaml",
    "compose.yml", "compose.yaml",
}

# Directories that should always be skipped
EXCLUDE_DIRS: set[str] = {
    "node_modules", ".git", "dist", "build", "__pycache__",
    ".venv", "venv", ".pytest_cache", ".mypy_cache", ".tox",
    ".eggs", ".ruff_cache", ".cache", "vendor",
}

# Directories skipped during a quick (non-full) scan
SKIP_DIRS: set[str] = {
    "test", "tests", "__test__", "__tests__", "spec",
    "docs", "documentation", "examples", "scripts",
}

# Directories that get priority in file ordering
PRIORITY_DIRS: set[str] = {
    "src", "lib", "app", "api", "server", "core",
}

# Maximum file size we will attempt to scan (bytes)
MAX_FILE_SIZE: int = 500_000  # 500 KB


class ScanEngine:
    """Orchestrate all scanners to produce unified findings for a repository."""

    def __init__(self) -> None:
        self.python_scanner = PythonScanner()
        self.js_scanner = JSScanner()
        self.config_scanner = ConfigScanner()
        self.dependency_scanner = DependencyScanner()
        self.notebook_scanner = NotebookScanner()
        self.secret_scanner = SecretScanner()
        self.signatures = self._load_signatures()

    # ── Public API ───────────────────────────────────────────────────

    def scan(
        self,
        repo_path: Path,
        full_scan: bool = False,
        workers: int = 10,
        file_limit: int = 1000,
    ) -> dict[str, Any]:
        """Scan a repository directory and return unified results.

        Args:
            repo_path: Absolute path to the repository root.
            full_scan: If True, include test/docs directories.
            workers: Number of ThreadPoolExecutor workers.
            file_limit: Max files to scan in a quick (non-full) scan.

        Returns:
            A dict with ``findings`` (list) and ``summary`` (dict).
        """
        files = self._collect_files(repo_path, full_scan, file_limit)
        logger.info("Scanning %d files in %s with %d workers", len(files), repo_path, workers)

        all_findings: list[dict[str, Any]] = []

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures: dict[Any, str] = {}
            for file_path in files:
                relative_path = str(file_path.relative_to(repo_path))
                future = executor.submit(self._scan_file, file_path, relative_path)
                futures[future] = relative_path

            for future in as_completed(futures):
                try:
                    findings = future.result()
                    all_findings.extend(findings)
                except Exception:
                    logger.debug(
                        "Error scanning %s", futures[future], exc_info=True,
                    )

        # Deduplicate
        all_findings = self._deduplicate(all_findings)

        # Build summary
        summary = self._build_summary(all_findings, len(files))

        return {
            "findings": all_findings,
            "summary": summary,
        }

    # ── Per-file dispatch ────────────────────────────────────────────

    def _scan_file(
        self, file_path: Path, relative_path: str,
    ) -> list[dict[str, Any]]:
        """Route a file to the correct scanner(s) and return findings."""
        findings: list[dict[str, Any]] = []
        suffix = file_path.suffix.lower()
        name = file_path.name.lower()

        try:
            # Python files
            if suffix in PYTHON_EXTS:
                findings.extend(
                    self.python_scanner.scan_file(file_path, relative_path, self.signatures),
                )
                findings.extend(
                    self.secret_scanner.scan_file(file_path, relative_path),
                )

            # JS/TS files
            elif suffix in JS_EXTS:
                findings.extend(
                    self.js_scanner.scan_file(file_path, relative_path, self.signatures),
                )
                findings.extend(
                    self.secret_scanner.scan_file(file_path, relative_path),
                )

            # Notebooks
            elif suffix in NOTEBOOK_EXTS:
                findings.extend(
                    self.notebook_scanner.scan_file(
                        file_path, relative_path, self.signatures, self.python_scanner,
                    ),
                )

            # Dependency files (may also be .json / .toml — handled below)
            if name in DEP_FILENAMES:
                findings.extend(
                    self.dependency_scanner.scan_file(file_path, relative_path, self.signatures),
                )

            # Config files (YAML, JSON, TOML, Dockerfile, docker-compose)
            if (
                suffix in CONFIG_EXTS
                or name.startswith(".env")
                or name in DOCKER_FILENAMES
            ):
                findings.extend(
                    self.config_scanner.scan_file(file_path, relative_path, self.signatures),
                )

            # .env files — also run secret scanner
            if name.startswith(".env"):
                findings.extend(
                    self.secret_scanner.scan_file(file_path, relative_path),
                )

            # GitHub Actions workflows
            if ".github/workflows" in relative_path and suffix in (".yaml", ".yml"):
                # Config scanner already handles this via scan_file, but
                # we also run the secret scanner on workflow files.
                findings.extend(
                    self.secret_scanner.scan_file(file_path, relative_path),
                )

        except Exception:
            logger.debug("Error scanning %s", relative_path, exc_info=True)

        return findings

    # ── File collection ──────────────────────────────────────────────

    def _collect_files(
        self,
        repo_path: Path,
        full_scan: bool,
        file_limit: int,
    ) -> list[Path]:
        """Walk the repo and collect scannable files with smart filtering."""
        priority_files: list[Path] = []
        other_files: list[Path] = []
        all_extensions = PYTHON_EXTS | JS_EXTS | CONFIG_EXTS | NOTEBOOK_EXTS

        for file_path in repo_path.rglob("*"):
            if not file_path.is_file():
                continue

            # Check exclusions
            parts = file_path.relative_to(repo_path).parts
            if any(p in EXCLUDE_DIRS for p in parts):
                continue

            # Check file size
            try:
                if file_path.stat().st_size > MAX_FILE_SIZE:
                    continue
            except OSError:
                continue

            name = file_path.name.lower()
            suffix = file_path.suffix.lower()

            # Determine if the file is scannable
            is_scannable = (
                suffix in all_extensions
                or name in DEP_FILENAMES
                or name in DOCKER_FILENAMES
                or name.startswith(".env")
            )
            if not is_scannable:
                continue

            # Skip test/docs directories in quick scan mode
            if not full_scan and any(p.lower() in SKIP_DIRS for p in parts):
                continue

            # Prioritise files in core directories
            if any(p.lower() in PRIORITY_DIRS for p in parts):
                priority_files.append(file_path)
            else:
                other_files.append(file_path)

        all_files = priority_files + other_files
        if not full_scan and len(all_files) > file_limit:
            logger.info(
                "Quick scan: truncating from %d to %d files", len(all_files), file_limit,
            )
            all_files = all_files[:file_limit]

        return all_files

    # ── Deduplication ────────────────────────────────────────────────

    @staticmethod
    def _deduplicate(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Remove duplicate findings (same file + line + pattern_name)."""
        seen: set[str] = set()
        unique: list[dict[str, Any]] = []
        for f in findings:
            key = f"{f['file_path']}:{f['line_number']}:{f['pattern_name']}"
            if key not in seen:
                seen.add(key)
                unique.append(f)
        return unique

    # ── Summary builder ──────────────────────────────────────────────

    @staticmethod
    def _build_summary(
        findings: list[dict[str, Any]], files_scanned: int,
    ) -> dict[str, Any]:
        """Build summary statistics from findings."""
        ai_files: set[str] = set()
        frameworks: dict[str, int] = {}
        component_types: dict[str, int] = {}
        severities: dict[str, int] = {}
        owasp_counts: dict[str, int] = {}
        providers: dict[str, int] = {}

        for f in findings:
            ai_files.add(f["file_path"])

            fw = f.get("framework") or "unknown"
            frameworks[fw] = frameworks.get(fw, 0) + 1

            ct = f.get("component_type") or "unknown"
            component_types[ct] = component_types.get(ct, 0) + 1

            sev = f.get("pattern_severity") or "info"
            severities[sev] = severities.get(sev, 0) + 1

            owasp = f.get("owasp_id")
            if owasp:
                owasp_counts[owasp] = owasp_counts.get(owasp, 0) + 1

            prov = f.get("provider")
            if prov:
                providers[prov] = providers.get(prov, 0) + 1

        return {
            "total_findings": len(findings),
            "files_scanned": files_scanned,
            "ai_files_count": len(ai_files),
            "frameworks": frameworks,
            "component_types": component_types,
            "severities": severities,
            "owasp_counts": owasp_counts,
            "providers": providers,
        }

    # ── Signature loading ────────────────────────────────────────────

    @staticmethod
    def _load_signatures() -> dict[str, Any]:
        """Load AI signatures from the bundled YAML file."""
        sig_paths = [
            Path(__file__).parent / "signatures" / "ai_signatures.yaml",
            _backend_dir.parent / "ai_signatures.yaml",
        ]
        for sig_path in sig_paths:
            if sig_path.exists():
                try:
                    with open(sig_path, encoding="utf-8") as fh:
                        data = yaml.safe_load(fh)
                        logger.info("Loaded signatures from %s", sig_path)
                        return data or {}
                except Exception:
                    logger.warning(
                        "Failed to load signatures from %s", sig_path, exc_info=True,
                    )
        logger.warning("No ai_signatures.yaml found — scanning with empty signatures")
        return {}
