"""
LLM-powered scan analysis service.

Wraps the existing llm_explainer module for the restructured app layout.

Usage:
    from app.services.analysis_service import explain_scan, generate_summary
"""
import sys
from pathlib import Path
from typing import Any, Dict

_backend_dir = str(Path(__file__).parent.parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from services.llm_explainer import explain_scan  # noqa: F401

import logging

logger = logging.getLogger(__name__)


async def generate_summary(scan_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a structured summary of scan results using an LLM.

    Returns a dict with:
        - narrative: str  (human-readable explanation)
        - key_findings: list[str]
        - risk_level: str  ("low" | "medium" | "high" | "critical")
        - recommendations: list[str]

    Falls back to a rule-based summary if the LLM call fails.
    """
    try:
        narrative = await explain_scan(scan_data)
        return {
            "narrative": narrative,
            "key_findings": _extract_key_findings(scan_data),
            "risk_level": _estimate_risk_level(scan_data),
            "recommendations": _extract_recommendations(scan_data),
        }
    except Exception as exc:
        logger.warning("LLM summary generation failed: %s — using fallback", exc)
        return {
            "narrative": _fallback_narrative(scan_data),
            "key_findings": _extract_key_findings(scan_data),
            "risk_level": _estimate_risk_level(scan_data),
            "recommendations": _extract_recommendations(scan_data),
        }


# ---------------------------------------------------------------------------
# Fallback helpers (no LLM needed)
# ---------------------------------------------------------------------------

def _extract_key_findings(scan_data: Dict[str, Any]) -> list:
    findings = []
    total = scan_data.get("total_occurrences", 0)
    files_count = scan_data.get("files_count", 0)
    if total:
        findings.append(f"Found {total} AI/LLM usage(s) across {files_count} file(s).")

    for fw in scan_data.get("frameworks_summary", []):
        name = fw.get("name", "unknown")
        count = fw.get("count", 0)
        if count:
            findings.append(f"{name}: {count} occurrence(s)")

    for flag in scan_data.get("risk_flags", []):
        findings.append(flag.get("message", str(flag)))

    return findings


def _estimate_risk_level(scan_data: Dict[str, Any]) -> str:
    risk_flags = scan_data.get("risk_flags", [])
    severities = [f.get("severity", "low") for f in risk_flags]
    if "critical" in severities:
        return "critical"
    if "high" in severities:
        return "high"
    if "medium" in severities:
        return "medium"
    return "low"


def _extract_recommendations(scan_data: Dict[str, Any]) -> list:
    return [
        a.get("action", str(a))
        for a in scan_data.get("recommended_actions", [])
    ]


def _fallback_narrative(scan_data: Dict[str, Any]) -> str:
    repo = scan_data.get("repo_url", "unknown repository")
    total = scan_data.get("total_occurrences", 0)
    files_count = scan_data.get("files_count", 0)
    return (
        f"Scan of {repo} found {total} AI/LLM-related occurrence(s) "
        f"across {files_count} file(s). Review the detailed findings for "
        f"specifics on frameworks, risk flags, and recommended actions."
    )
