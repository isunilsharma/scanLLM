"""
Scan differ for ScanLLM.

Compares two scan results to detect drift: new findings, resolved findings,
risk score changes, provider/component changes, and severity changes.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ScanDiff:
    """Result of comparing two scan results."""

    added_findings: list[dict[str, Any]] = field(default_factory=list)
    removed_findings: list[dict[str, Any]] = field(default_factory=list)
    changed_findings: list[dict[str, Any]] = field(default_factory=list)
    risk_score_before: int = 0
    risk_score_after: int = 0
    new_providers: list[str] = field(default_factory=list)
    removed_providers: list[str] = field(default_factory=list)
    new_components: list[dict[str, Any]] = field(default_factory=list)
    removed_components: list[dict[str, Any]] = field(default_factory=list)

    @property
    def risk_score_delta(self) -> int:
        """Change in risk score (positive = worse)."""
        return self.risk_score_after - self.risk_score_before

    @property
    def has_changes(self) -> bool:
        """True if any findings, providers, or components changed."""
        return bool(
            self.added_findings
            or self.removed_findings
            or self.changed_findings
            or self.new_providers
            or self.removed_providers
            or self.new_components
            or self.removed_components
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON output."""
        return {
            "has_changes": self.has_changes,
            "risk_score_before": self.risk_score_before,
            "risk_score_after": self.risk_score_after,
            "risk_score_delta": self.risk_score_delta,
            "added_findings_count": len(self.added_findings),
            "removed_findings_count": len(self.removed_findings),
            "changed_findings_count": len(self.changed_findings),
            "added_findings": self.added_findings[:50],  # Cap for output size
            "removed_findings": self.removed_findings[:50],
            "changed_findings": self.changed_findings[:50],
            "new_providers": self.new_providers,
            "removed_providers": self.removed_providers,
            "new_components": self.new_components[:50],
            "removed_components": self.removed_components[:50],
        }

    def summary_text(self) -> str:
        """Generate human-readable summary for terminal output."""
        lines: list[str] = []

        if not self.has_changes:
            return "No changes detected between scans."

        lines.append("Scan Diff Summary")
        lines.append("=" * 40)

        # Risk score
        if self.risk_score_before != self.risk_score_after:
            direction = "increased" if self.risk_score_delta > 0 else "decreased"
            lines.append(
                f"Risk score {direction}: {self.risk_score_before} -> "
                f"{self.risk_score_after} ({self.risk_score_delta:+d})"
            )

        # Findings
        if self.added_findings:
            lines.append(f"New findings: {len(self.added_findings)}")
            for f in self.added_findings[:5]:
                fp = f.get("file_path", "<unknown>")
                ln = f.get("line_number", "?")
                pn = f.get("pattern_name", f.get("component_type", ""))
                sev = f.get("severity", "")
                lines.append(f"  + [{sev}] {pn} in {fp}:{ln}")
            if len(self.added_findings) > 5:
                lines.append(f"  ... and {len(self.added_findings) - 5} more")

        if self.removed_findings:
            lines.append(f"Resolved findings: {len(self.removed_findings)}")
            for f in self.removed_findings[:5]:
                fp = f.get("file_path", "<unknown>")
                ln = f.get("line_number", "?")
                pn = f.get("pattern_name", f.get("component_type", ""))
                lines.append(f"  - {pn} in {fp}:{ln}")
            if len(self.removed_findings) > 5:
                lines.append(f"  ... and {len(self.removed_findings) - 5} more")

        if self.changed_findings:
            lines.append(f"Changed severity: {len(self.changed_findings)}")
            for c in self.changed_findings[:5]:
                finding = c.get("finding", {})
                fp = finding.get("file_path", "<unknown>")
                pn = finding.get("pattern_name", "")
                old_sev = c.get("old_severity", "?")
                new_sev = c.get("new_severity", "?")
                lines.append(f"  ~ {pn} in {fp}: {old_sev} -> {new_sev}")

        # Providers
        if self.new_providers:
            lines.append(f"New providers: {', '.join(self.new_providers)}")
        if self.removed_providers:
            lines.append(f"Removed providers: {', '.join(self.removed_providers)}")

        # Components
        if self.new_components:
            lines.append(f"New components: {len(self.new_components)}")
            for comp in self.new_components[:5]:
                ctype = comp.get("component_type", comp.get("type", ""))
                name = comp.get("name", comp.get("provider", ""))
                lines.append(f"  + [{ctype}] {name}")

        if self.removed_components:
            lines.append(f"Removed components: {len(self.removed_components)}")
            for comp in self.removed_components[:5]:
                ctype = comp.get("component_type", comp.get("type", ""))
                name = comp.get("name", comp.get("provider", ""))
                lines.append(f"  - [{ctype}] {name}")

        return "\n".join(lines)


class ScanDiffer:
    """Compare two scan results to detect drift."""

    def diff(
        self,
        baseline: dict[str, Any],
        current: dict[str, Any],
    ) -> ScanDiff:
        """Compare two scan results.

        Both baseline and current should have the structure:
        {
            "findings": [...],
            "summary": {...},
            "risk_score": int,  # optional
        }

        Parameters
        ----------
        baseline:
            Previous scan result dict.
        current:
            Current scan result dict.

        Returns
        -------
        ScanDiff with added/removed/changed findings, provider and component diffs.
        """
        old_findings = baseline.get("findings", [])
        new_findings = current.get("findings", [])

        # Index findings by composite key
        old_keys = {self._finding_key(f): f for f in old_findings}
        new_keys = {self._finding_key(f): f for f in new_findings}

        old_key_set = set(old_keys.keys())
        new_key_set = set(new_keys.keys())

        added = [new_keys[k] for k in sorted(new_key_set - old_key_set)]
        removed = [old_keys[k] for k in sorted(old_key_set - new_key_set)]

        # Detect changed severity for same finding
        changed: list[dict[str, Any]] = []
        for k in sorted(old_key_set & new_key_set):
            old_f = old_keys[k]
            new_f = new_keys[k]
            old_sev = (old_f.get("severity") or "").lower()
            new_sev = (new_f.get("severity") or "").lower()
            if old_sev != new_sev:
                changed.append({
                    "finding": new_f,
                    "old_severity": old_sev,
                    "new_severity": new_sev,
                })

        # Provider diff
        old_summary = baseline.get("summary", {})
        new_summary = current.get("summary", {})
        old_providers = set(old_summary.get("providers", {}).keys())
        new_providers = set(new_summary.get("providers", {}).keys())
        added_providers = sorted(new_providers - old_providers)
        removed_providers = sorted(old_providers - new_providers)

        # Component diff
        new_components, removed_components = self._diff_components(
            old_findings, new_findings
        )

        # Risk scores
        old_risk = baseline.get("risk_score", 0)
        new_risk = current.get("risk_score", 0)
        # Handle dict-style risk_score (e.g. {"score": 45, "grade": "C"})
        if isinstance(old_risk, dict):
            old_risk = old_risk.get("score", 0)
        if isinstance(new_risk, dict):
            new_risk = new_risk.get("score", 0)

        return ScanDiff(
            added_findings=added,
            removed_findings=removed,
            changed_findings=changed,
            risk_score_before=int(old_risk or 0),
            risk_score_after=int(new_risk or 0),
            new_providers=added_providers,
            removed_providers=removed_providers,
            new_components=new_components,
            removed_components=removed_components,
        )

    @staticmethod
    def _finding_key(finding: dict[str, Any]) -> str:
        """Generate a unique key for a finding for comparison.

        Two findings are "the same" if they share file_path, line_number,
        and pattern_name.
        """
        return (
            f"{finding.get('file_path', '')}:"
            f"{finding.get('line_number', '')}:"
            f"{finding.get('pattern_name', '')}"
        )

    @staticmethod
    def _diff_components(
        old_findings: list[dict[str, Any]],
        new_findings: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Identify new and removed AI components between scan results.

        A component is identified by (component_type, provider/name).
        """

        def _extract_components(findings: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
            components: dict[str, dict[str, Any]] = {}
            for f in findings:
                ctype = f.get("component_type", "")
                provider = f.get("provider", f.get("name", ""))
                if ctype:
                    key = f"{ctype}:{provider}"
                    if key not in components:
                        components[key] = {
                            "component_type": ctype,
                            "provider": provider,
                            "name": f.get("name", provider),
                            "file_path": f.get("file_path", ""),
                        }
            return components

        old_comps = _extract_components(old_findings)
        new_comps = _extract_components(new_findings)

        old_keys = set(old_comps.keys())
        new_keys = set(new_comps.keys())

        added = [new_comps[k] for k in sorted(new_keys - old_keys)]
        removed = [old_comps[k] for k in sorted(old_keys - new_keys)]

        return added, removed
