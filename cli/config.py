"""
.scanllm/ directory management.

Handles initialization, scan storage, history retrieval, and
configuration loading for the local ScanLLM workspace.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG = {
    "version": "2.0.0",
    "scan": {
        "full_scan": False,
        "workers": 10,
        "file_limit": 1000,
        "exclude_dirs": [],
        "severity_filter": None,
    },
    "output": {
        "format": "table",
        "save_scans": True,
    },
}

_DEFAULT_IGNORE = """\
# ScanLLM ignore patterns (gitignore syntax)
# Files matching these patterns will be skipped during scanning.

node_modules/
.git/
dist/
build/
__pycache__/
*.min.js
*.bundle.js
*.lock
"""


class ScanLLMConfig:
    """Manages the ``.scanllm/`` directory in a repository."""

    SCANLLM_DIR = ".scanllm"

    def __init__(self, repo_path: Path | None = None) -> None:
        self.repo_path = repo_path or Path.cwd()
        self.scanllm_dir = self.repo_path / self.SCANLLM_DIR

    # ── Queries ──────────────────────────────────────────────────────

    def is_initialized(self) -> bool:
        """Return True if the ``.scanllm/`` directory exists."""
        return self.scanllm_dir.is_dir()

    # ── Initialization ───────────────────────────────────────────────

    def initialize(self) -> None:
        """Create ``.scanllm/`` with default configuration files."""
        self.scanllm_dir.mkdir(parents=True, exist_ok=True)
        (self.scanllm_dir / "scans").mkdir(exist_ok=True)
        (self.scanllm_dir / "baselines").mkdir(exist_ok=True)

        # config.yaml
        config_path = self.scanllm_dir / "config.yaml"
        if not config_path.exists():
            config_path.write_text(
                yaml.dump(_DEFAULT_CONFIG, default_flow_style=False, sort_keys=False),
                encoding="utf-8",
            )

        # policies.yaml
        policies_path = self.scanllm_dir / "policies.yaml"
        if not policies_path.exists():
            try:
                from core.policy.defaults import generate_default_yaml
                policies_path.write_text(generate_default_yaml(), encoding="utf-8")
            except ImportError:
                policies_path.write_text(
                    yaml.dump({"policies": []}, default_flow_style=False),
                    encoding="utf-8",
                )

        # .scanllmignore
        ignore_path = self.repo_path / ".scanllmignore"
        if not ignore_path.exists():
            ignore_path.write_text(_DEFAULT_IGNORE, encoding="utf-8")

    # ── Scan persistence ─────────────────────────────────────────────

    def save_scan(self, scan_result: dict[str, Any]) -> Path:
        """Save *scan_result* to ``.scanllm/scans/`` and return the path."""
        scans_dir = self.scanllm_dir / "scans"
        scans_dir.mkdir(parents=True, exist_ok=True)

        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"scan_{ts}.json"
        out_path = scans_dir / filename

        out_path.write_text(
            json.dumps(scan_result, indent=2, default=str),
            encoding="utf-8",
        )
        logger.info("Saved scan to %s", out_path)
        return out_path

    def get_latest_scan(self) -> dict[str, Any] | None:
        """Load and return the most recent scan result, or None."""
        scans = self._scan_files()
        if not scans:
            return None
        return self._load_json(scans[-1])

    def get_previous_scan(self) -> dict[str, Any] | None:
        """Load and return the second-most-recent scan result, or None."""
        scans = self._scan_files()
        if len(scans) < 2:
            return None
        return self._load_json(scans[-2])

    def get_scan_history(self) -> list[dict[str, Any]]:
        """Return metadata for all stored scans (newest first)."""
        history: list[dict[str, Any]] = []
        for scan_file in reversed(self._scan_files()):
            data = self._load_json(scan_file)
            if data:
                history.append({
                    "file": str(scan_file),
                    "timestamp": data.get("timestamp", scan_file.stem),
                    "total_findings": data.get("summary", {}).get("total_findings", 0),
                    "risk_score": data.get("risk_score"),
                })
        return history

    # ── Policy helpers ───────────────────────────────────────────────

    def get_policies_path(self) -> Path | None:
        """Return the path to policies.yaml if it exists."""
        p = self.scanllm_dir / "policies.yaml"
        return p if p.exists() else None

    # ── Configuration ────────────────────────────────────────────────

    def get_config(self) -> dict[str, Any]:
        """Load and return the merged configuration dict."""
        config_path = self.scanllm_dir / "config.yaml"
        if not config_path.exists():
            return dict(_DEFAULT_CONFIG)

        try:
            with open(config_path, encoding="utf-8") as fh:
                user_config = yaml.safe_load(fh) or {}
        except Exception:
            logger.warning("Failed to load config.yaml, using defaults")
            return dict(_DEFAULT_CONFIG)

        # Merge user config on top of defaults (shallow per top-level key)
        merged = dict(_DEFAULT_CONFIG)
        for key, value in user_config.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = {**merged[key], **value}
            else:
                merged[key] = value
        return merged

    # ── Internal helpers ─────────────────────────────────────────────

    def _scan_files(self) -> list[Path]:
        """Return sorted list of scan JSON files (oldest first)."""
        scans_dir = self.scanllm_dir / "scans"
        if not scans_dir.is_dir():
            return []
        files = sorted(scans_dir.glob("scan_*.json"))
        return files

    @staticmethod
    def _load_json(path: Path) -> dict[str, Any] | None:
        try:
            with open(path, encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            logger.warning("Failed to load %s", path)
            return None
