"""Canonical finding schema for ScanLLM.

Every scanner builds its findings through :func:`make_finding` (or the
agent-security flavoured :func:`make_agent_finding`) so that a finding looks
identical no matter which scanner produced it.  Two fields matter to
downstream consumers and used to be missing entirely:

``severity``
    The canonical severity.  ``pattern_severity`` is kept alongside it, with
    the same value, so existing consumers keep working.

``finding_type``
    The coarse kind of the finding, derived from the namespaced
    ``pattern_name`` (``"prompt_injection:template_literal"`` →
    ``"prompt_injection"``).

Severity tallies are also centralised here.  ``summary.severities`` and
``risk.severity_counts`` are both produced by :func:`count_severities`, which
is what stops the two counters from drifting apart — previously they read
different keys and reported contradictory numbers for the same scan.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

# Ordered most severe first; this is the complete severity vocabulary.
SEVERITY_LEVELS: tuple[str, ...] = ("critical", "high", "medium", "low", "info")

DEFAULT_SEVERITY: str = "info"
DEFAULT_FINDING_TYPE: str = "unknown"

_SEVERITY_SET: frozenset[str] = frozenset(SEVERITY_LEVELS)


def normalize_severity(value: object) -> str:
    """Coerce *value* to a member of :data:`SEVERITY_LEVELS`.

    Anything unrecognised (including ``None``) becomes ``"info"`` so that
    every finding lands in exactly one bucket.
    """
    if not isinstance(value, str):
        return DEFAULT_SEVERITY
    severity = value.strip().lower()
    return severity if severity in _SEVERITY_SET else DEFAULT_SEVERITY


def derive_finding_type(pattern_name: str | None) -> str:
    """Derive the coarse finding type from a namespaced *pattern_name*.

    Pattern names are written as ``"<type>:<detail>"`` (``"import:langchain"``,
    ``"model_ref:gpt-4o"``); the part before the first colon is the type.
    Names without a colon (``"hardcoded_credential"``, MCP/skill risk ids) are
    already a type and are used verbatim.
    """
    if not pattern_name:
        return DEFAULT_FINDING_TYPE
    head = pattern_name.split(":", 1)[0].strip()
    return head or DEFAULT_FINDING_TYPE


def finding_severity(finding: Mapping[str, Any]) -> str:
    """Return the canonical severity of a finding dict.

    Prefers ``severity``; falls back to ``pattern_severity`` so that findings
    built outside :func:`make_finding` (license, config-health, findings
    loaded from an older saved scan) are still bucketed correctly.
    """
    raw = finding.get("severity") or finding.get("pattern_severity")
    return normalize_severity(raw)


def count_severities(findings: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    """Tally findings by severity.

    Always returns all of :data:`SEVERITY_LEVELS`, in order, so callers can
    index any level without a default.  This is the single source of truth
    for every severity tally ScanLLM emits.
    """
    counts: dict[str, int] = dict.fromkeys(SEVERITY_LEVELS, 0)
    for finding in findings:
        counts[finding_severity(finding)] += 1
    return counts


def make_finding(
    *,
    file_path: str,
    line_number: int,
    line_text: str = "",
    framework: str = "",
    pattern_name: str = "",
    pattern_category: str = "",
    pattern_severity: str = "info",
    pattern_description: str = "",
    snippet: str = "",
    model_name: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    is_streaming: bool = False,
    has_tools: bool = False,
    component_type: str = "",
    provider: str = "",
    owasp_id: str | None = None,
    remediation: str | None = None,
    risk_id: str | None = None,
) -> dict[str, Any]:
    """Construct a normalised finding dict.

    ``severity`` and ``pattern_severity`` are always populated with the same
    normalised value.  ``remediation`` and ``risk_id`` are only emitted when
    supplied, keeping the dict shape unchanged for the scanners that do not
    produce them.
    """
    severity = normalize_severity(pattern_severity)
    finding: dict[str, Any] = {
        "file_path": file_path,
        "line_number": line_number,
        "line_text": line_text,
        "framework": framework,
        "pattern_name": pattern_name,
        "pattern_category": pattern_category,
        "pattern_severity": severity,
        "pattern_description": pattern_description,
        "snippet": snippet,
        "model_name": model_name,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "is_streaming": is_streaming,
        "has_tools": has_tools,
        "component_type": component_type,
        "provider": provider,
        "owasp_id": owasp_id,
        # Canonical fields — see module docstring.
        "severity": severity,
        "finding_type": derive_finding_type(pattern_name),
    }
    if remediation is not None:
        finding["remediation"] = remediation
    if risk_id is not None:
        finding["risk_id"] = risk_id
    return finding


def make_agent_finding(
    *,
    file_path: str,
    risk_id: str,
    severity: str,
    description: str,
    framework: str,
    component_type: str,
    line_number: int = 0,
    remediation: str = "",
    provider: str = "",
    snippet: str = "",
    owasp_id: str | None = None,
) -> dict[str, Any]:
    """Construct a finding for the agent-security scanners (MCP, skills).

    These scanners speak in risk ids and remediations rather than detection
    patterns, so this maps their vocabulary onto :func:`make_finding`.
    """
    return make_finding(
        file_path=file_path,
        line_number=line_number,
        line_text=snippet,
        framework=framework,
        pattern_name=risk_id,
        pattern_category="agent_security",
        pattern_severity=severity,
        pattern_description=description,
        snippet=snippet,
        component_type=component_type,
        provider=provider,
        owasp_id=owasp_id,
        remediation=remediation,
        risk_id=risk_id,
    )
