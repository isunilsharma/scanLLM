"""PDF compliance report generator for ScanLLM.

Renders a Jinja2 HTML template and converts it to PDF using xhtml2pdf.
"""

from __future__ import annotations

import io
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).parent / "templates"

# OWASP LLM Top 10 (2025) reference data
OWASP_LLM_TOP_10 = [
    {"id": "LLM01", "name": "Prompt Injection", "default_severity": "high"},
    {"id": "LLM02", "name": "Sensitive Information Disclosure", "default_severity": "high"},
    {"id": "LLM03", "name": "Supply Chain Vulnerabilities", "default_severity": "critical"},
    {"id": "LLM04", "name": "Data and Model Poisoning", "default_severity": "high"},
    {"id": "LLM05", "name": "Improper Output Handling", "default_severity": "critical"},
    {"id": "LLM06", "name": "Excessive Agency", "default_severity": "high"},
    {"id": "LLM07", "name": "System Prompt Leakage", "default_severity": "medium"},
    {"id": "LLM08", "name": "Vector and Embedding Weaknesses", "default_severity": "medium"},
    {"id": "LLM09", "name": "Misinformation", "default_severity": "medium"},
    {"id": "LLM10", "name": "Unbounded Consumption", "default_severity": "low"},
]


def _risk_score_color(score: int | float) -> str:
    """Return CSS color class based on risk score."""
    score = int(score)
    if score < 25:
        return "green"
    if score < 50:
        return "yellow"
    if score < 75:
        return "orange"
    return "red"


def _severity_order(severity: str) -> int:
    """Return sort key for severity levels (lower = more severe)."""
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    return order.get(severity.lower(), 5)


def _bar_color(label: str) -> str:
    """Pick a bar color based on the breakdown category label."""
    label_lower = label.lower()
    if "secret" in label_lower or "credential" in label_lower:
        return "red"
    if "critical" in label_lower or "owasp" in label_lower:
        return "orange"
    if "high" in label_lower:
        return "orange"
    if "agent" in label_lower or "excessive" in label_lower:
        return "purple"
    if "outdated" in label_lower or "package" in label_lower:
        return "yellow"
    if "concentration" in label_lower or "provider" in label_lower:
        return "blue"
    return "blue"


class PDFGenerator:
    """Generate branded PDF compliance reports from scan results."""

    def __init__(self, template_dir: Path | str | None = None) -> None:
        tpl_dir = Path(template_dir) if template_dir else TEMPLATE_DIR
        self._env = Environment(
            loader=FileSystemLoader(str(tpl_dir)),
            autoescape=True,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_pdf(
        self,
        scan_data: dict[str, Any],
        risk_score: dict[str, Any],
        owasp_data: dict[str, Any],
        org_name: str = "ScanLLM",
    ) -> bytes:
        """Render the HTML report and convert it to a PDF byte string.

        Args:
            scan_data: Scan results including components, findings, dependencies.
            risk_score: Risk scoring output with overall_score, grade, breakdown.
            owasp_data: OWASP LLM Top 10 mapping with per-category findings.
            org_name: Organization name for branding.

        Returns:
            Raw PDF bytes.
        """
        html = self._render_html(scan_data, risk_score, owasp_data, org_name)
        return self._html_to_pdf(html)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _render_html(
        self,
        scan_data: dict[str, Any],
        risk_score: dict[str, Any],
        owasp_data: dict[str, Any],
        org_name: str,
    ) -> str:
        """Build the full HTML string from the Jinja2 template."""

        template = self._env.get_template("report.html")

        # --- Components table ---
        components = self._build_components(scan_data)

        # --- Risk breakdown bars ---
        breakdown_items = self._build_breakdown(risk_score)

        # --- OWASP table ---
        owasp_items = self._build_owasp_items(owasp_data)

        # --- Findings grouped by severity ---
        findings_by_severity = self._build_findings_by_severity(scan_data)

        # --- Dependencies list ---
        dependencies = self._build_dependencies(scan_data)

        # --- Recommendations ---
        recommendations = self._build_recommendations(scan_data, risk_score, owasp_data)

        overall_score = risk_score.get("overall_score", 0)

        return template.render(
            org_name=org_name,
            scan_data=scan_data,
            risk_score=risk_score,
            generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            score_color=_risk_score_color(overall_score),
            components=components,
            breakdown_items=breakdown_items,
            owasp_items=owasp_items,
            findings_by_severity=findings_by_severity,
            dependencies=dependencies,
            recommendations=recommendations,
        )

    @staticmethod
    def _html_to_pdf(html: str) -> bytes:
        """Convert an HTML string to PDF bytes using xhtml2pdf."""
        try:
            from xhtml2pdf import pisa
        except ImportError as exc:
            raise RuntimeError(
                "xhtml2pdf is required for PDF generation. "
                "Install it with: pip install xhtml2pdf"
            ) from exc

        buf = io.BytesIO()
        pisa_status = pisa.CreatePDF(io.StringIO(html), dest=buf)

        if pisa_status.err:
            logger.error("xhtml2pdf reported %d errors during PDF creation", pisa_status.err)
            raise RuntimeError(f"PDF generation failed with {pisa_status.err} error(s)")

        return buf.getvalue()

    # ------------------------------------------------------------------
    # Data preparation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_components(scan_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Normalise component data for the inventory table."""
        raw = scan_data.get("components", [])
        out: list[dict[str, Any]] = []
        for comp in raw:
            out.append(
                {
                    "name": comp.get("name", comp.get("display_name", "Unknown")),
                    "type": comp.get("type", comp.get("category", "unknown")).replace("_", " ").title(),
                    "provider": comp.get("provider", comp.get("display_name", "—")),
                    "files_count": comp.get("files_count", len(comp.get("files", []))),
                    "severity": comp.get("severity", comp.get("risk_level", "medium")),
                }
            )
        out.sort(key=lambda c: _severity_order(c["severity"]))
        return out

    @staticmethod
    def _build_breakdown(risk_score: dict[str, Any]) -> list[dict[str, Any]]:
        """Build bar-chart data from the risk score breakdown."""
        breakdown = risk_score.get("breakdown", {})
        if not breakdown:
            return []

        max_score = risk_score.get("max_possible_score", 100)
        items: list[dict[str, Any]] = []

        for key, detail in breakdown.items():
            if isinstance(detail, dict):
                label = detail.get("label", key.replace("_", " ").title())
                score = detail.get("score", 0)
            else:
                label = key.replace("_", " ").title()
                score = detail

            percentage = min(100, int((score / max(max_score, 1)) * 100 * 5))  # scale up for visibility
            items.append(
                {
                    "label": label,
                    "score": score,
                    "percentage": min(percentage, 100),
                    "color": _bar_color(label),
                }
            )

        items.sort(key=lambda i: i["score"], reverse=True)
        return items

    @staticmethod
    def _build_owasp_items(owasp_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Build the OWASP table rows."""
        categories = owasp_data.get("categories", {})
        items: list[dict[str, Any]] = []

        for entry in OWASP_LLM_TOP_10:
            cat_id = entry["id"]
            cat_data = categories.get(cat_id, {})
            findings_count = cat_data.get("count", cat_data.get("findings_count", 0))
            max_severity = cat_data.get("max_severity", cat_data.get("severity", ""))

            if findings_count == 0:
                status_color = "green"
                status_label = "Clear"
            elif max_severity in ("critical", "high"):
                status_color = "red"
                status_label = "At Risk"
            else:
                status_color = "yellow"
                status_label = "Attention"

            items.append(
                {
                    "id": cat_id,
                    "name": entry["name"],
                    "status_color": status_color,
                    "status_label": status_label,
                    "findings_count": findings_count,
                    "max_severity": max_severity or "info",
                }
            )

        return items

    @staticmethod
    def _build_findings_by_severity(scan_data: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
        """Group findings by severity for the findings table."""
        findings = scan_data.get("findings", [])
        if not findings:
            return {}

        grouped: dict[str, list[dict[str, Any]]] = {}
        for f in findings:
            sev = f.get("severity", "medium").lower()
            entry = {
                "message": f.get("message", f.get("description", "—")),
                "file": f.get("file", f.get("file_path", "—")),
                "line": f.get("line", f.get("line_number", "—")),
                "owasp": f.get("owasp", f.get("owasp_id", "")),
            }
            grouped.setdefault(sev, []).append(entry)

        # Return in severity order
        ordered: dict[str, list[dict[str, Any]]] = {}
        for sev in ("critical", "high", "medium", "low", "info"):
            if sev in grouped:
                ordered[sev] = grouped[sev]
        return ordered

    @staticmethod
    def _build_dependencies(scan_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Build the dependency list-view table."""
        deps = scan_data.get("dependencies", scan_data.get("edges", []))
        out: list[dict[str, Any]] = []
        for d in deps:
            out.append(
                {
                    "source": d.get("source", d.get("source_label", "—")),
                    "relationship": d.get("relationship", d.get("label", "depends on")),
                    "target": d.get("target", d.get("target_label", "—")),
                }
            )
        return out

    @staticmethod
    def _build_recommendations(
        scan_data: dict[str, Any],
        risk_score: dict[str, Any],
        owasp_data: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Generate prioritized remediation recommendations."""
        recs: list[dict[str, Any]] = []

        # Pull explicit recommendations if provided
        explicit = scan_data.get("recommendations", [])
        for r in explicit:
            recs.append(
                {
                    "severity": r.get("severity", "medium"),
                    "title": r.get("title", "Recommendation"),
                    "description": r.get("description", ""),
                    "owasp": r.get("owasp", ""),
                }
            )

        # Auto-generate from risk breakdown
        breakdown = risk_score.get("breakdown", {})

        secrets_detail = breakdown.get("secrets_found", {})
        secrets_count = secrets_detail.get("count", 0) if isinstance(secrets_detail, dict) else secrets_detail
        if secrets_count and secrets_count > 0:
            recs.append(
                {
                    "severity": "critical",
                    "title": "Remove hardcoded secrets and API keys",
                    "description": (
                        f"Found {secrets_count} hardcoded secret(s). Rotate affected credentials "
                        "immediately and migrate to a secrets manager (e.g., AWS Secrets Manager, "
                        "HashiCorp Vault, or environment variables via CI/CD)."
                    ),
                    "owasp": "LLM02, LLM07",
                }
            )

        owasp_cats = owasp_data.get("categories", {})

        if owasp_cats.get("LLM01", {}).get("count", 0) > 0:
            recs.append(
                {
                    "severity": "high",
                    "title": "Mitigate prompt injection risks",
                    "description": (
                        "User input is concatenated directly into prompts. Use parameterised prompt "
                        "templates, input validation, and output filtering to reduce injection risk."
                    ),
                    "owasp": "LLM01",
                }
            )

        if owasp_cats.get("LLM05", {}).get("count", 0) > 0:
            recs.append(
                {
                    "severity": "critical",
                    "title": "Sanitise LLM output before execution",
                    "description": (
                        "LLM output is passed to eval(), exec(), or shell commands without "
                        "sanitisation. Never execute LLM-generated code directly."
                    ),
                    "owasp": "LLM05",
                }
            )

        if owasp_cats.get("LLM06", {}).get("count", 0) > 0:
            recs.append(
                {
                    "severity": "high",
                    "title": "Restrict agent tool permissions",
                    "description": (
                        "Agent configurations grant broad tool access. Apply least-privilege "
                        "principles and add human-in-the-loop approval for destructive actions."
                    ),
                    "owasp": "LLM06",
                }
            )

        if owasp_cats.get("LLM10", {}).get("count", 0) > 0:
            recs.append(
                {
                    "severity": "low",
                    "title": "Set max_tokens and rate limits on LLM calls",
                    "description": (
                        "Some LLM API calls lack max_tokens limits or timeout settings. "
                        "Add explicit limits to prevent unbounded resource consumption."
                    ),
                    "owasp": "LLM10",
                }
            )

        concentration = breakdown.get("provider_concentration", {})
        conc_score = concentration.get("score", 0) if isinstance(concentration, dict) else concentration
        if conc_score and conc_score > 5:
            recs.append(
                {
                    "severity": "medium",
                    "title": "Reduce single-provider concentration risk",
                    "description": (
                        "This codebase relies heavily on a single LLM provider. Consider "
                        "abstracting the provider layer (e.g., via LiteLLM or LangChain) to "
                        "enable failover and reduce vendor lock-in."
                    ),
                    "owasp": "",
                }
            )

        # Deduplicate by title
        seen_titles: set[str] = set()
        unique_recs: list[dict[str, Any]] = []
        for r in recs:
            if r["title"] not in seen_titles:
                seen_titles.add(r["title"])
                unique_recs.append(r)

        unique_recs.sort(key=lambda r: _severity_order(r["severity"]))
        return unique_recs
