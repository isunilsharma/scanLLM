"""Scanner Engine Orchestrator - dispatches files to appropriate scanners"""
import sys
import logging
import yaml
from pathlib import Path
from typing import List, Dict, Any, Set
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

# Add backend to path for existing imports
_backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_backend_dir))

from app.scanner.python_scanner import PythonScanner
from app.scanner.js_scanner import JSScanner
from app.scanner.config_scanner import ConfigScanner
from app.scanner.dependency_scanner import DependencyScanner
from app.scanner.notebook_scanner import NotebookScanner
from app.scanner.secret_scanner import SecretScanner

# File extension to scanner mapping
PYTHON_EXTS = {".py"}
JS_EXTS = {".js", ".ts", ".jsx", ".tsx"}
CONFIG_EXTS = {".yaml", ".yml", ".json", ".toml"}
NOTEBOOK_EXTS = {".ipynb"}
DEP_FILENAMES = {
    "requirements.txt", "pyproject.toml", "pipfile",
    "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
}
ENV_PATTERNS = {".env"}
DOCKER_FILENAMES = {"dockerfile", "docker-compose.yml", "docker-compose.yaml"}

EXCLUDE_DIRS = {
    "node_modules", ".git", "dist", "build", "__pycache__",
    ".venv", "venv", ".pytest_cache", ".mypy_cache", ".tox", ".eggs",
}

SKIP_DIRS = {"test", "tests", "__test__", "spec", "docs", "documentation", "examples", "scripts"}

PRIORITY_DIRS = {"src", "lib", "app", "api", "server", "core"}

MAX_FILE_SIZE = 500_000  # 500KB


class ScanEngine:
    """Orchestrates all scanners to produce unified findings"""

    def __init__(self):
        self.python_scanner = PythonScanner()
        self.js_scanner = JSScanner()
        self.config_scanner = ConfigScanner()
        self.dependency_scanner = DependencyScanner()
        self.notebook_scanner = NotebookScanner()
        self.secret_scanner = SecretScanner()
        self.signatures = self._load_signatures()

    def _load_signatures(self) -> dict:
        """Load AI signatures from YAML"""
        sig_paths = [
            Path(__file__).parent / "signatures" / "ai_signatures.yaml",
            _backend_dir.parent / "ai_signatures.yaml",
        ]
        for sig_path in sig_paths:
            if sig_path.exists():
                try:
                    with open(sig_path) as f:
                        return yaml.safe_load(f) or {}
                except Exception as e:
                    logger.warning(f"Failed to load signatures from {sig_path}: {e}")
        logger.warning("No ai_signatures.yaml found")
        return {}

    def scan(self, repo_path: Path, full_scan: bool = False, workers: int = 10,
             file_limit: int = 1000) -> Dict[str, Any]:
        """Scan a repository directory and return unified results"""
        files = self._collect_files(repo_path, full_scan, file_limit)
        logger.info(f"Scanning {len(files)} files with {workers} workers")

        all_findings: List[Dict[str, Any]] = []

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {}
            for file_path in files:
                relative_path = str(file_path.relative_to(repo_path))
                future = executor.submit(self._scan_file, file_path, relative_path)
                futures[future] = relative_path

            for future in as_completed(futures):
                try:
                    findings = future.result()
                    all_findings.extend(findings)
                except Exception as e:
                    logger.debug(f"Error scanning {futures[future]}: {e}")

        # Deduplicate
        all_findings = self._deduplicate(all_findings)

        # Build summary
        summary = self._build_summary(all_findings, len(files))

        return {
            "findings": all_findings,
            "summary": summary,
        }

    def _scan_file(self, file_path: Path, relative_path: str) -> List[Dict[str, Any]]:
        """Dispatch file to appropriate scanner(s)"""
        findings = []
        suffix = file_path.suffix.lower()
        name = file_path.name.lower()

        try:
            # Python files
            if suffix in PYTHON_EXTS:
                findings.extend(self.python_scanner.scan_file(file_path, relative_path, self.signatures))
                findings.extend(self.secret_scanner.scan_file(file_path, relative_path))

            # JS/TS files
            elif suffix in JS_EXTS:
                findings.extend(self.js_scanner.scan_file(file_path, relative_path, self.signatures))
                findings.extend(self.secret_scanner.scan_file(file_path, relative_path))

            # Notebooks
            elif suffix in NOTEBOOK_EXTS:
                findings.extend(self.notebook_scanner.scan_file(
                    file_path, relative_path, self.signatures, self.python_scanner
                ))

            # Dependency files
            if name in DEP_FILENAMES:
                findings.extend(self.dependency_scanner.scan_file(file_path, relative_path, self.signatures))

            # Config files
            if suffix in CONFIG_EXTS or name.startswith(".env") or name in DOCKER_FILENAMES:
                findings.extend(self.config_scanner.scan_file(file_path, relative_path, self.signatures))

            # Env files (also check with secret scanner)
            if name.startswith(".env"):
                findings.extend(self.secret_scanner.scan_file(file_path, relative_path))

        except Exception as e:
            logger.debug(f"Error scanning {relative_path}: {e}")

        return findings

    def _collect_files(self, repo_path: Path, full_scan: bool, file_limit: int) -> List[Path]:
        """Collect files to scan with smart filtering"""
        priority_files: List[Path] = []
        other_files: List[Path] = []
        all_extensions = PYTHON_EXTS | JS_EXTS | CONFIG_EXTS | NOTEBOOK_EXTS | ENV_PATTERNS

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

            # Check if scannable
            is_scannable = (
                suffix in all_extensions
                or name in DEP_FILENAMES
                or name in DOCKER_FILENAMES
                or name.startswith(".env")
            )
            if not is_scannable:
                continue

            # Skip test/docs in non-full scan
            if not full_scan and any(p.lower() in SKIP_DIRS for p in parts):
                continue

            # Prioritize
            if any(p.lower() in PRIORITY_DIRS for p in parts):
                priority_files.append(file_path)
            else:
                other_files.append(file_path)

        all_files = priority_files + other_files
        if not full_scan and len(all_files) > file_limit:
            all_files = all_files[:file_limit]

        return all_files

    def _deduplicate(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate findings (same file, line, pattern)"""
        seen: Set[str] = set()
        unique = []
        for f in findings:
            key = f"{f['file_path']}:{f['line_number']}:{f['pattern_name']}"
            if key not in seen:
                seen.add(key)
                unique.append(f)
        return unique

    def _build_summary(self, findings: List[Dict[str, Any]], files_scanned: int) -> Dict[str, Any]:
        """Build summary statistics from findings"""
        ai_files = set(f["file_path"] for f in findings)
        frameworks: Dict[str, int] = {}
        component_types: Dict[str, int] = {}
        severities: Dict[str, int] = {}

        for f in findings:
            fw = f.get("framework", "unknown")
            frameworks[fw] = frameworks.get(fw, 0) + 1

            ct = f.get("component_type", "unknown")
            component_types[ct] = component_types.get(ct, 0) + 1

            sev = f.get("pattern_severity", "low")
            severities[sev] = severities.get(sev, 0) + 1

        return {
            "total_findings": len(findings),
            "files_scanned": files_scanned,
            "ai_files_count": len(ai_files),
            "frameworks": frameworks,
            "component_types": component_types,
            "severities": severities,
        }
