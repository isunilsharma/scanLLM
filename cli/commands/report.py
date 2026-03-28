"""scanllm report [pdf|aibom|json] — Report generation commands."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import typer
from rich.console import Console

from cli.config import ScanLLMConfig

console = Console()

report_app = typer.Typer(help="Report generation commands.")


def _get_latest_scan(path: str) -> tuple[dict[str, Any], ScanLLMConfig]:
    """Load the latest saved scan or exit with an error."""
    repo_path = Path(path).resolve()
    config = ScanLLMConfig(repo_path)

    latest = config.get_latest_scan()
    if latest is None:
        console.print(
            "[bold red]Error:[/bold red] No saved scans found.\n"
            "  Run [bold]scanllm scan --save[/bold] first."
        )
        raise typer.Exit(code=1)

    return latest, config


@report_app.command(name="json")
def report_json(
    path: str = typer.Argument(".", help="Repository path"),
    pretty: bool = typer.Option(True, "--pretty/--compact", help="Pretty-print JSON"),
    output_file: str = typer.Option(None, "--file", "-f", help="Write to file instead of stdout"),
) -> None:
    """Export latest scan findings as JSON."""
    latest, config = _get_latest_scan(path)

    indent = 2 if pretty else None
    json_str = json.dumps(latest, indent=indent, default=str)

    if output_file:
        out_path = Path(output_file).resolve()
        out_path.write_text(json_str + "\n", encoding="utf-8")
        console.print(f"[green]Report written to:[/green] {out_path}")
    else:
        sys.stdout.write(json_str + "\n")


@report_app.command(name="aibom")
def report_aibom(
    path: str = typer.Argument(".", help="Repository path"),
    format: str = typer.Option("json", "--format", help="Output format: json, xml"),
    output_file: str = typer.Option(None, "--file", "-f", help="Write to file instead of stdout"),
) -> None:
    """Generate an AI Bill of Materials (CycloneDX 1.6)."""
    latest, config = _get_latest_scan(path)
    findings = latest.get("findings", [])

    bom = _build_cyclonedx_bom(findings, latest)

    if format == "xml":
        xml_str = _bom_to_xml(bom)
        if output_file:
            out_path = Path(output_file).resolve()
            out_path.write_text(xml_str, encoding="utf-8")
            console.print(f"[green]AI-BOM written to:[/green] {out_path}")
        else:
            sys.stdout.write(xml_str + "\n")
    else:
        json_str = json.dumps(bom, indent=2, default=str)
        if output_file:
            out_path = Path(output_file).resolve()
            out_path.write_text(json_str + "\n", encoding="utf-8")
            console.print(f"[green]AI-BOM written to:[/green] {out_path}")
        else:
            sys.stdout.write(json_str + "\n")


@report_app.command(name="pdf")
def report_pdf(
    path: str = typer.Argument(".", help="Repository path"),
    output_file: str = typer.Option(None, "--file", "-f", help="Output PDF file path"),
) -> None:
    """Generate a PDF security report from latest scan."""
    latest, config = _get_latest_scan(path)

    if output_file is None:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output_file = f"scanllm_report_{timestamp}.pdf"

    out_path = Path(output_file).resolve()
    findings = latest.get("findings", [])
    summary = latest.get("summary", {})
    risk = latest.get("risk", {})
    owasp = latest.get("owasp", {})

    # Try to use the backend PDF generator if available
    try:
        from core.reports.pdf_generator import generate_pdf  # type: ignore[import]
        generate_pdf(
            findings=findings,
            summary=summary,
            risk=risk,
            owasp=owasp,
            output_path=str(out_path),
        )
        console.print(f"[green]PDF report written to:[/green] {out_path}")
        return
    except ImportError:
        pass

    # Fallback: generate a simple HTML-based report
    html = _generate_html_report(findings, summary, risk, owasp, latest)

    try:
        from xhtml2pdf import pisa  # type: ignore[import]
        with open(out_path, "wb") as fh:
            pisa.CreatePDF(html, dest=fh)
        console.print(f"[green]PDF report written to:[/green] {out_path}")
    except ImportError:
        # If xhtml2pdf not available, save as HTML
        html_path = out_path.with_suffix(".html")
        html_path.write_text(html, encoding="utf-8")
        console.print(
            f"[yellow]xhtml2pdf not installed. HTML report saved to:[/yellow] {html_path}\n"
            f"  Install with: [dim]pip install xhtml2pdf[/dim]"
        )


def _build_cyclonedx_bom(
    findings: list[dict[str, Any]],
    scan_data: dict[str, Any],
) -> dict[str, Any]:
    """Build a CycloneDX 1.6 AI-BOM from findings."""
    bom: dict[str, Any] = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "version": 1,
        "metadata": {
            "timestamp": scan_data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "tools": [{
                "vendor": "ScanLLM",
                "name": "scanllm",
                "version": "2.0.0",
            }],
        },
        "components": [],
        "dependencies": [],
    }

    seen: set[str] = set()
    for finding in findings:
        comp_type = finding.get("component_type", "unknown")
        provider = finding.get("provider", "")
        name = finding.get("pattern_name", "")
        key = f"{comp_type}:{provider}:{name}"

        if key in seen:
            continue
        seen.add(key)

        cdx_type = "machine-learning-model" if comp_type in (
            "llm_provider", "embedding_service"
        ) else "library"

        component: dict[str, Any] = {
            "type": cdx_type,
            "name": name or provider or comp_type,
            "group": provider,
            "properties": [
                {"name": "scanllm:component_type", "value": comp_type},
                {"name": "scanllm:provider", "value": provider},
            ],
        }

        model_name = finding.get("model_name", "")
        if model_name:
            component["properties"].append(
                {"name": "scanllm:model_name", "value": model_name}
            )

        bom["components"].append(component)

    return bom


def _bom_to_xml(bom: dict[str, Any]) -> str:
    """Convert a CycloneDX BOM dict to minimal XML."""
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<bom xmlns="http://cyclonedx.org/schema/bom/1.6" version="1">',
        "  <metadata>",
        f'    <timestamp>{bom["metadata"]["timestamp"]}</timestamp>',
        "    <tools>",
        "      <tool>",
        "        <vendor>ScanLLM</vendor>",
        "        <name>scanllm</name>",
        "        <version>2.0.0</version>",
        "      </tool>",
        "    </tools>",
        "  </metadata>",
        "  <components>",
    ]

    for comp in bom.get("components", []):
        name = _xml_escape(comp.get("name", ""))
        ctype = _xml_escape(comp.get("type", "library"))
        group = _xml_escape(comp.get("group", ""))
        lines.append(f'    <component type="{ctype}">')
        if group:
            lines.append(f"      <group>{group}</group>")
        lines.append(f"      <name>{name}</name>")

        props = comp.get("properties", [])
        if props:
            lines.append("      <properties>")
            for prop in props:
                pname = _xml_escape(prop.get("name", ""))
                pval = _xml_escape(prop.get("value", ""))
                lines.append(f'        <property name="{pname}">{pval}</property>')
            lines.append("      </properties>")

        lines.append("    </component>")

    lines.append("  </components>")
    lines.append("</bom>")
    return "\n".join(lines)


def _xml_escape(s: str) -> str:
    """Escape special XML characters."""
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def _generate_html_report(
    findings: list[dict[str, Any]],
    summary: dict[str, Any],
    risk: dict[str, Any],
    owasp: dict[str, Any],
    scan_data: dict[str, Any],
) -> str:
    """Generate an HTML report for PDF conversion."""
    score = risk.get("overall_score", 0) if risk else 0
    grade = risk.get("grade", "?") if risk else "?"
    total = summary.get("total_findings", 0)
    files_scanned = summary.get("files_scanned", 0)
    timestamp = scan_data.get("timestamp", "")
    scan_path = scan_data.get("path", "")

    severity_colors = {
        "critical": "#dc2626",
        "high": "#ef4444",
        "medium": "#f59e0b",
        "low": "#06b6d4",
        "info": "#9ca3af",
    }

    # Build findings rows
    rows = []
    for f in findings[:100]:  # Cap at 100 for PDF
        sev = (f.get("severity") or f.get("pattern_severity") or "info").lower()
        color = severity_colors.get(sev, "#9ca3af")
        rows.append(
            f"<tr>"
            f'<td>{_xml_escape(f.get("file_path", ""))}</td>'
            f'<td>{_xml_escape(f.get("pattern_name", ""))}</td>'
            f'<td>{_xml_escape(f.get("provider", "") or "-")}</td>'
            f'<td style="color:{color};font-weight:bold">{sev}</td>'
            f'<td>{_xml_escape(f.get("owasp_id", "") or "")}</td>'
            f"</tr>"
        )

    findings_html = "\n".join(rows)

    # Build OWASP section
    owasp_rows = []
    for cat in owasp.get("categories", []) if owasp else []:
        status = cat.get("status", "not_detected")
        status_color = "#22c55e" if status == "not_detected" else "#ef4444"
        owasp_rows.append(
            f"<tr>"
            f'<td>{_xml_escape(cat.get("id", ""))}</td>'
            f'<td>{_xml_escape(cat.get("name", ""))}</td>'
            f'<td style="color:{status_color}">{status}</td>'
            f'<td>{cat.get("finding_count", 0)}</td>'
            f"</tr>"
        )
    owasp_html = "\n".join(owasp_rows)

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>ScanLLM Security Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 40px; color: #1a1a1a; }}
        h1 {{ color: #0891b2; border-bottom: 2px solid #0891b2; padding-bottom: 10px; }}
        h2 {{ color: #334155; margin-top: 30px; }}
        .summary {{ background: #f1f5f9; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .score {{ font-size: 48px; font-weight: bold; color: #0891b2; }}
        .grade {{ font-size: 36px; font-weight: bold; margin-left: 10px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 15px 0; font-size: 12px; }}
        th, td {{ border: 1px solid #e2e8f0; padding: 8px 12px; text-align: left; }}
        th {{ background: #f8fafc; font-weight: 600; }}
        tr:nth-child(even) {{ background: #f8fafc; }}
        .footer {{ margin-top: 40px; color: #94a3b8; font-size: 11px; border-top: 1px solid #e2e8f0; padding-top: 10px; }}
    </style>
</head>
<body>
    <h1>ScanLLM Security Report</h1>

    <div class="summary">
        <span class="score">{score}/100</span>
        <span class="grade">Grade {grade}</span>
        <br><br>
        <strong>Path:</strong> {_xml_escape(scan_path)}<br>
        <strong>Scan Date:</strong> {_xml_escape(timestamp)}<br>
        <strong>Files Scanned:</strong> {files_scanned}<br>
        <strong>Total Findings:</strong> {total}
    </div>

    <h2>OWASP LLM Top 10 Coverage</h2>
    <table>
        <tr><th>ID</th><th>Name</th><th>Status</th><th>Findings</th></tr>
        {owasp_html}
    </table>

    <h2>Findings</h2>
    <table>
        <tr><th>File</th><th>Finding</th><th>Provider</th><th>Severity</th><th>OWASP</th></tr>
        {findings_html}
    </table>

    <div class="footer">
        Generated by ScanLLM v2.0.0 | {_xml_escape(timestamp)}
    </div>
</body>
</html>"""
