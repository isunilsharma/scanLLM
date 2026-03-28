"""Rich table formatting for ScanLLM CLI output."""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()

# ── Severity styling ────────────────────────────────────────────────────────

_SEVERITY_STYLES: dict[str, str] = {
    "critical": "bold red",
    "high": "red",
    "medium": "yellow",
    "low": "cyan",
    "info": "dim",
}

_SEVERITY_ORDER: dict[str, int] = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
    "info": 4,
}

_GRADE_STYLES: dict[str, str] = {
    "A": "bold green",
    "B": "green",
    "C": "yellow",
    "D": "red",
    "F": "bold red",
}


def _severity_text(severity: str) -> Text:
    """Return a Rich Text object styled for the given severity."""
    sev = severity.lower()
    style = _SEVERITY_STYLES.get(sev, "dim")
    return Text(sev, style=style)


# ── Summary panel ───────────────────────────────────────────────────────────

def print_summary_panel(
    summary: dict[str, Any],
    risk_result: dict[str, Any] | None = None,
    owasp_result: dict[str, Any] | None = None,
) -> None:
    """Print the top-level summary panel with risk score and key metrics."""
    lines: list[str] = []

    # Risk score line
    if risk_result:
        score = risk_result.get("overall_score", 0)
        grade = risk_result.get("grade", "?")
        grade_style = _GRADE_STYLES.get(grade, "white")
        lines.append(
            f"  [bold]Risk Score:[/bold] {score}/100 "
            f"([{grade_style}]Grade {grade}[/{grade_style}])"
        )

    # Component count
    total = summary.get("total_findings", 0)
    ai_files = summary.get("ai_files_count", 0)
    files_scanned = summary.get("files_scanned", 0)
    lines.append(
        f"  [bold]AI Components:[/bold] {total} found across {ai_files} files "
        f"({files_scanned} files scanned)"
    )

    # Providers
    providers = summary.get("providers", {})
    if providers:
        provider_names = ", ".join(sorted(providers.keys()))
        lines.append(f"  [bold]Providers:[/bold] {provider_names}")

    # OWASP issues
    if owasp_result:
        categories = owasp_result.get("categories", [])
        detected = [c for c in categories if c.get("status") == "detected"]
        if detected:
            owasp_items = []
            for cat in detected:
                sev = cat.get("severity", "medium").capitalize()
                owasp_items.append(f"{cat['id']} ({sev})")
            lines.append(
                f"  [bold]OWASP Issues:[/bold] {', '.join(owasp_items)}"
            )
        else:
            lines.append("  [bold]OWASP Issues:[/bold] None detected")

    # Severity breakdown
    severities = summary.get("severities", {})
    if severities:
        parts = []
        for sev in ("critical", "high", "medium", "low", "info"):
            count = severities.get(sev, 0)
            if count > 0:
                style = _SEVERITY_STYLES.get(sev, "dim")
                parts.append(f"[{style}]{count} {sev}[/{style}]")
        if parts:
            lines.append(f"  [bold]Severity:[/bold] {' | '.join(parts)}")

    panel_text = "\n".join(lines)
    console.print(Panel(
        panel_text,
        title="[bold cyan]ScanLLM Results[/bold cyan]",
        border_style="cyan",
        padding=(1, 2),
    ))


# ── Findings table ──────────────────────────────────────────────────────────

def print_findings_table(
    findings: list[dict[str, Any]],
    severity_filter: str | None = None,
) -> None:
    """Print the findings as a Rich table, optionally filtered by severity."""
    # Apply severity filter
    if severity_filter:
        min_order = _SEVERITY_ORDER.get(severity_filter.lower(), 4)
        findings = [
            f for f in findings
            if _SEVERITY_ORDER.get((f.get("severity") or f.get("pattern_severity") or "info").lower(), 4) <= min_order
        ]

    # Sort by severity (critical first)
    findings = sorted(
        findings,
        key=lambda f: _SEVERITY_ORDER.get(
            (f.get("severity") or f.get("pattern_severity") or "info").lower(), 4
        ),
    )

    if not findings:
        console.print("\n  [dim]No findings to display.[/dim]\n")
        return

    table = Table(
        title=f"Findings ({len(findings)} total)",
        show_header=True,
        header_style="bold",
        border_style="dim",
        padding=(0, 1),
    )
    table.add_column("File", style="cyan", max_width=35, no_wrap=True)
    table.add_column("Finding", max_width=30)
    table.add_column("Provider", style="magenta", max_width=14)
    table.add_column("Severity", max_width=10)
    table.add_column("OWASP", style="yellow", max_width=8)

    for f in findings:
        file_path = f.get("file_path", "")
        # Truncate long paths from the left
        if len(file_path) > 35:
            file_path = "..." + file_path[-32:]

        finding_name = f.get("pattern_name", f.get("message", ""))
        if len(finding_name) > 30:
            finding_name = finding_name[:27] + "..."

        provider = f.get("provider", "") or f.get("framework", "") or "-"
        severity = (f.get("severity") or f.get("pattern_severity") or "info").lower()
        owasp = f.get("owasp_id", "") or ""

        table.add_row(
            file_path,
            finding_name,
            provider,
            _severity_text(severity),
            owasp,
        )

    console.print()
    console.print(table)
    console.print()


# ── Policy result ───────────────────────────────────────────────────────────

def print_policy_result(policy_eval: dict[str, Any]) -> None:
    """Print the policy evaluation result."""
    passed = policy_eval.get("passed", True)
    errors = policy_eval.get("errors", 0)
    warnings = policy_eval.get("warnings", 0)
    passes = policy_eval.get("passes", 0)

    if passed:
        status = "[bold green]PASS[/bold green]"
    else:
        status = "[bold red]FAIL[/bold red]"

    parts = []
    if errors:
        parts.append(f"[red]{errors} error{'s' if errors != 1 else ''}[/red]")
    if warnings:
        parts.append(f"[yellow]{warnings} warning{'s' if warnings != 1 else ''}[/yellow]")
    if passes:
        parts.append(f"[green]{passes} passed[/green]")

    summary_line = ", ".join(parts) if parts else "no rules evaluated"

    console.print(Panel(
        f"  Policy Check: {status}  --  {summary_line}",
        border_style="green" if passed else "red",
        padding=(0, 1),
    ))

    # Show individual rule results
    results = policy_eval.get("results", [])
    if results:
        table = Table(show_header=True, header_style="bold", border_style="dim")
        table.add_column("Rule", max_width=30)
        table.add_column("Status", max_width=8)
        table.add_column("Severity", max_width=10)
        table.add_column("Violations", max_width=6, justify="right")
        table.add_column("Detail", max_width=50)

        for r in results:
            rule_passed = r.get("passed", True)
            status_text = Text("PASS", style="green") if rule_passed else Text("FAIL", style="red")
            sev = r.get("severity", "warning")
            violation_count = r.get("violation_count", 0)
            detail = ""
            violations = r.get("violations", [])
            if violations:
                detail = violations[0].get("message", "")
                if len(detail) > 50:
                    detail = detail[:47] + "..."

            table.add_row(
                r.get("name", ""),
                status_text,
                _severity_text(sev),
                str(violation_count),
                detail,
            )

        console.print(table)
        console.print()


# ── Diff result ─────────────────────────────────────────────────────────────

def print_diff_result(scan_diff: dict[str, Any]) -> None:
    """Print scan diff with color coding.

    Supports both legacy keys (added_count, added) and newer keys
    (added_findings_count, added_findings) from the rewritten differ.
    """
    has_changes = scan_diff.get("has_changes", False)

    if not has_changes:
        console.print(Panel(
            "  [green]No changes detected between scans.[/green]",
            title="[bold cyan]Scan Diff[/bold cyan]",
            border_style="green",
        ))
        return

    added_count = scan_diff.get("added_count", scan_diff.get("added_findings_count", 0))
    removed_count = scan_diff.get("removed_count", scan_diff.get("removed_findings_count", 0))
    changed_count = scan_diff.get("changed_count", scan_diff.get("changed_findings_count", 0))

    # Summary
    parts = []
    if added_count:
        parts.append(f"[red]+{added_count} new[/red]")
    if removed_count:
        parts.append(f"[green]-{removed_count} resolved[/green]")
    if changed_count:
        parts.append(f"[yellow]~{changed_count} changed[/yellow]")

    risk_delta = scan_diff.get("risk_delta", scan_diff.get("risk_score_delta"))
    risk_line = ""
    if risk_delta is not None:
        old_score = scan_diff.get("old_risk_score", scan_diff.get("risk_score_before", "?"))
        new_score = scan_diff.get("new_risk_score", scan_diff.get("risk_score_after", "?"))
        if risk_delta > 0:
            risk_line = f"\n  Risk Score: {old_score} -> {new_score} ([red]+{risk_delta}[/red])"
        elif risk_delta < 0:
            risk_line = f"\n  Risk Score: {old_score} -> {new_score} ([green]{risk_delta}[/green])"
        else:
            risk_line = f"\n  Risk Score: {new_score} (unchanged)"

    # Provider changes
    new_providers = scan_diff.get("new_providers", [])
    removed_providers = scan_diff.get("removed_providers", [])
    provider_line = ""
    if new_providers:
        provider_line += f"\n  New providers: [cyan]{', '.join(new_providers)}[/cyan]"
    if removed_providers:
        provider_line += f"\n  Removed providers: [yellow]{', '.join(removed_providers)}[/yellow]"

    console.print(Panel(
        f"  {' | '.join(parts)}{risk_line}{provider_line}",
        title="[bold cyan]Scan Diff[/bold cyan]",
        border_style="cyan",
        padding=(1, 2),
    ))

    # Added findings
    added = scan_diff.get("added", scan_diff.get("added_findings", []))
    if added:
        table = Table(title="[red]New Findings[/red]", border_style="red", show_header=True)
        table.add_column("File", style="cyan", max_width=35)
        table.add_column("Finding", max_width=30)
        table.add_column("Severity", max_width=10)

        for f in added[:20]:
            sev = (f.get("severity") or f.get("pattern_severity") or "info").lower()
            table.add_row(
                _truncate_path(f.get("file_path", "")),
                f.get("pattern_name", ""),
                _severity_text(sev),
            )
        if len(added) > 20:
            table.add_row("[dim]...[/dim]", f"[dim]+{len(added) - 20} more[/dim]", "")
        console.print(table)

    # Removed findings
    removed = scan_diff.get("removed", scan_diff.get("removed_findings", []))
    if removed:
        table = Table(title="[green]Resolved Findings[/green]", border_style="green", show_header=True)
        table.add_column("File", style="cyan", max_width=35)
        table.add_column("Finding", max_width=30)
        table.add_column("Severity", max_width=10)

        for f in removed[:20]:
            sev = (f.get("severity") or f.get("pattern_severity") or "info").lower()
            table.add_row(
                _truncate_path(f.get("file_path", "")),
                f.get("pattern_name", ""),
                _severity_text(sev),
            )
        if len(removed) > 20:
            table.add_row("[dim]...[/dim]", f"[dim]+{len(removed) - 20} more[/dim]", "")
        console.print(table)

    console.print()


def _truncate_path(path: str, max_len: int = 35) -> str:
    if len(path) > max_len:
        return "..." + path[-(max_len - 3):]
    return path
