"""scanllm export — Export scan results to multiple formats at once."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import typer
from rich.console import Console

from cli.config import ScanLLMConfig

console = Console()


def export(
    path: str = typer.Argument(".", help="Repository path"),
    output_dir: str = typer.Option("./scanllm-reports", "--dir", "-d", help="Output directory for reports"),
    formats: str = typer.Option("all", "--formats", "-f", help="Comma-separated: json,sarif,aibom,summary (or 'all')"),
) -> None:
    """Export scan results to multiple formats in one command."""
    repo_path = Path(path).resolve()
    config = ScanLLMConfig(repo_path)
    latest = config.get_latest_scan()

    if latest is None:
        console.print("[bold red]Error:[/bold red] No saved scans found.\n  Run [bold]scanllm scan --save[/bold] first.")
        raise typer.Exit(code=1)

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    fmt_list = ["json", "sarif", "aibom", "summary"] if formats == "all" else [f.strip() for f in formats.split(",")]

    console.print(f"\n[bold cyan]ScanLLM Export[/bold cyan]")
    console.print(f"  Output directory: {out_dir}\n")

    for fmt in fmt_list:
        try:
            if fmt == "json":
                out_file = out_dir / "scanllm-report.json"
                out_file.write_text(json.dumps(latest, indent=2, default=str), encoding="utf-8")
                console.print(f"  [green]\u2713[/green] {out_file}")

            elif fmt == "sarif":
                out_file = out_dir / "scanllm-report.sarif"
                from cli.output.sarif import to_sarif
                sarif = to_sarif(latest.get("findings", []))
                out_file.write_text(json.dumps(sarif, indent=2, default=str), encoding="utf-8")
                console.print(f"  [green]\u2713[/green] {out_file}")

            elif fmt == "aibom":
                out_file = out_dir / "ai-bom.cdx.json"
                bom = _generate_aibom(latest)
                out_file.write_text(json.dumps(bom, indent=2, default=str), encoding="utf-8")
                console.print(f"  [green]\u2713[/green] {out_file}")

            elif fmt == "summary":
                out_file = out_dir / "scan-summary.md"
                md = _generate_summary_md(latest)
                out_file.write_text(md, encoding="utf-8")
                console.print(f"  [green]\u2713[/green] {out_file}")

            else:
                console.print(f"  [yellow]![/yellow] Unknown format: {fmt}")

        except Exception as e:
            console.print(f"  [red]\u2717[/red] {fmt}: {e}")

    # Record telemetry
    try:
        from cli.telemetry import record_event
        record_event(
            event_type="export",
            command="export",
            finding_count=len(latest.get("findings", [])),
            config_dir=config.base_dir,
        )
    except Exception:
        pass

    console.print()


def _generate_aibom(scan_data: dict[str, Any]) -> dict[str, Any]:
    """Generate CycloneDX AI-BOM from scan data."""
    findings = scan_data.get("findings", [])
    bom: dict[str, Any] = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "version": 1,
        "metadata": {
            "timestamp": scan_data.get("timestamp", datetime.utcnow().isoformat()),
            "tools": [{"vendor": "ScanLLM", "name": "scanllm", "version": "2.1.0"}],
        },
        "components": [],
    }

    seen: set[str] = set()
    for f in findings:
        comp_type = f.get("component_type", "unknown")
        provider = f.get("provider", "")
        name = f.get("pattern_name", "")
        key = f"{comp_type}:{provider}:{name}"
        if key in seen:
            continue
        seen.add(key)
        bom["components"].append({
            "type": "machine-learning-model" if comp_type in ("llm_provider", "embedding_service") else "library",
            "name": name or provider or comp_type,
            "group": provider,
            "properties": [
                {"name": "scanllm:component_type", "value": comp_type},
                {"name": "scanllm:provider", "value": provider},
            ],
        })
    return bom


def _generate_summary_md(scan_data: dict[str, Any]) -> str:
    """Generate a markdown summary of the scan."""
    summary = scan_data.get("summary", {})
    risk = scan_data.get("risk", {})
    findings = scan_data.get("findings", [])

    lines = [
        "# ScanLLM Scan Report",
        "",
        f"**Date:** {scan_data.get('timestamp', 'N/A')}",
        f"**Files Scanned:** {summary.get('files_scanned', 0)}",
        f"**AI Components Found:** {summary.get('total_findings', 0)}",
        f"**Risk Score:** {risk.get('overall_score', 0)}/100 (Grade {risk.get('grade', '?')})",
        "",
        "## Findings by Severity",
        "",
    ]

    severities = summary.get("severities", {})
    for sev in ("critical", "high", "medium", "low", "info"):
        count = severities.get(sev, 0)
        if count:
            lines.append(f"- **{sev.capitalize()}:** {count}")

    lines.extend(["", "## Providers Detected", ""])
    providers = summary.get("providers", {})
    for p, count in sorted(providers.items()):
        lines.append(f"- {p} ({count} references)")

    lines.extend(["", "## Top Findings", ""])
    for f in findings[:10]:
        sev = (f.get("severity") or f.get("pattern_severity") or "info").upper()
        lines.append(f"- [{sev}] {f.get('pattern_name', '')} in {f.get('file_path', '')}:{f.get('line_number', '')}")

    lines.extend(["", "---", "*Generated by [ScanLLM](https://scanllm.ai)*", ""])
    return "\n".join(lines)
