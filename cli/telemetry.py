"""Telemetry collection helper — fire-and-forget event recording.

Events are posted to the backend API when reachable, otherwise stored
locally in ``.scanllm/telemetry.json``.  Collection can be disabled via
``scanllm telemetry off`` or the ``SCANLLM_TELEMETRY=off`` env var.
"""

from __future__ import annotations

import json
import logging
import os
import platform
import sys
import uuid
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Lazy session id — unique per CLI invocation
_SESSION_ID: str | None = None


def _get_session_id() -> str:
    global _SESSION_ID
    if _SESSION_ID is None:
        _SESSION_ID = uuid.uuid4().hex[:16]
    return _SESSION_ID


def is_enabled(config_path: Optional[Path] = None) -> bool:
    """Check whether telemetry is enabled.

    Priority:
        1. ``SCANLLM_TELEMETRY`` env var (``off`` / ``false`` / ``0`` to disable)
        2. ``.scanllm/config.yaml`` → ``telemetry.enabled``
        3. Default: **True**
    """
    env = os.environ.get("SCANLLM_TELEMETRY", "").lower()
    if env in ("off", "false", "0", "no"):
        return False

    # Check local config
    if config_path is None:
        config_path = Path.cwd() / ".scanllm" / "config.yaml"
    if config_path.exists():
        try:
            import yaml
            data = yaml.safe_load(config_path.read_text()) or {}
            tel = data.get("telemetry", {})
            if isinstance(tel, dict) and tel.get("enabled") is False:
                return False
        except Exception:
            pass

    return True


def record_event(
    *,
    event_type: str,
    command: str,
    scan_duration_ms: Optional[int] = None,
    finding_count: Optional[int] = None,
    risk_score: Optional[int] = None,
    providers: Optional[list[str]] = None,
    config_dir: Optional[Path] = None,
) -> None:
    """Record a telemetry event. Never raises, never blocks the CLI."""
    try:
        config_yaml = None
        if config_dir:
            config_yaml = config_dir / "config.yaml"
        if not is_enabled(config_yaml):
            return

        from core import __version__

        payload: dict[str, Any] = {
            "event_type": event_type,
            "command": command,
            "scan_duration_ms": scan_duration_ms,
            "finding_count": finding_count,
            "risk_score": risk_score,
            "python_version": platform.python_version(),
            "os_platform": sys.platform,
            "scanllm_version": __version__,
            "session_id": _get_session_id(),
        }
        if providers:
            payload["providers_detected"] = providers

        # Try to post to backend
        backend_url = os.environ.get("SCANLLM_BACKEND_URL", "https://scanllm-backend.onrender.com")
        if backend_url:
            try:
                import urllib.request
                req = urllib.request.Request(
                    f"{backend_url}/api/v1/telemetry/events",
                    data=json.dumps(payload).encode(),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                urllib.request.urlopen(req, timeout=3)
                return
            except Exception:
                pass

        # Fallback: store locally
        store_dir = config_dir or (Path.cwd() / ".scanllm")
        if store_dir.exists():
            tel_file = store_dir / "telemetry.json"
            existing: list[dict[str, Any]] = []
            if tel_file.exists():
                try:
                    existing = json.loads(tel_file.read_text())
                except Exception:
                    existing = []
            # Keep last 500 events locally
            existing.append(payload)
            existing = existing[-500:]
            tel_file.write_text(json.dumps(existing, indent=2))

    except Exception:
        # Never let telemetry break the CLI
        pass
