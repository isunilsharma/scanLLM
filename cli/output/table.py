"""Rich table formatting for ScanLLM CLI output."""

from __future__ import annotations

from dataclasses import dataclass
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


# ── Fix hints ──────────────────────────────────────────────────────────────

_FIX_HINTS: dict[str, str] = {
    "hardcoded_secret": "Move to env var",
    "secret": "Move to env var",
    "prompt_injection": "Use template engine",
    "eval_llm_output": "Use json.loads()",
    "exec_llm_output": "Remove exec()",
    "missing_max_tokens": "Add max_tokens=4096",
    "deprecated_model": "Upgrade model version",
    "excessive_agency": "Restrict tool list",
    "unauthenticated_vectordb": "Add auth/API key",
    "system_prompt_leak": "Move secrets to env",
}


def get_fix_hint(finding: dict[str, Any]) -> str:
    """Get a one-line fix hint for a finding."""
    category = (finding.get("pattern_category", "") or finding.get("category", "")).lower()
    owasp = finding.get("owasp_id", "")
    pattern = (finding.get("pattern_name", "") or "").lower()

    # Check pattern name first
    for key, hint in _FIX_HINTS.items():
        if key in pattern or key in category:
            return hint

    # Check OWASP mapping
    owasp_hints = {
        "LLM01": "Sanitize user input",
        "LLM02": "Remove sensitive data",
        "LLM03": "Pin package versions",
        "LLM05": "Validate LLM output",
        "LLM06": "Limit agent permissions",
        "LLM07": "Move secrets to env",
        "LLM08": "Add DB authentication",
        "LLM10": "Add max_tokens limit",
    }
    if owasp:
        return owasp_hints.get(owasp, "")
    return ""


# ── Findings table ──────────────────────────────────────────────────────────

#: Maximum number of (deduplicated) rows rendered before the table is capped.
DEFAULT_MAX_ROWS: int = 25

_ELLIPSIS: str = "…"
_TIMES: str = "×"


def _severity_of(finding: dict[str, Any]) -> str:
    """Normalized severity for a finding ('critical' … 'info')."""
    return (finding.get("severity") or finding.get("pattern_severity") or "info").lower()


def _label_of(finding: dict[str, Any]) -> str:
    """Human-readable name of what was detected."""
    return str(finding.get("pattern_name") or finding.get("message") or "unknown")


def _provider_of(finding: dict[str, Any]) -> str:
    """Provider/framework attributed to a finding, or '' when unknown."""
    return str(finding.get("provider") or finding.get("framework") or "")


@dataclass
class FindingGroup:
    """A display-only roll-up of identical findings within a single file.

    ``finding`` references the first member of the group and is never mutated:
    grouping affects only what the terminal table renders, never the findings
    list used for JSON/SARIF/CycloneDX output, counts, or risk scoring.
    """

    finding: dict[str, Any]
    count: int = 1
    first_line: int | None = None


def group_findings(findings: list[dict[str, Any]]) -> list[FindingGroup]:
    """Collapse repeated detections into one entry per (file, kind, provider).

    Severity and OWASP id are part of the key too, so rows that would render
    differently are never merged. Insertion order is preserved.
    """
    groups: dict[tuple[str, str, str, str, str], FindingGroup] = {}

    for f in findings:
        key = (
            str(f.get("file_path") or ""),
            _label_of(f),
            _provider_of(f),
            _severity_of(f),
            str(f.get("owasp_id") or ""),
        )
        raw_line = f.get("line_number")
        line = raw_line if isinstance(raw_line, int) else None

        existing = groups.get(key)
        if existing is None:
            groups[key] = FindingGroup(finding=f, count=1, first_line=line)
        else:
            existing.count += 1
            if line is not None and (existing.first_line is None or line < existing.first_line):
                existing.first_line = line

    return list(groups.values())


def _sort_groups(groups: list[FindingGroup]) -> list[FindingGroup]:
    """Severity first (critical → info), then most-repeated, then by path."""
    return sorted(
        groups,
        key=lambda g: (
            _SEVERITY_ORDER.get(_severity_of(g.finding), 4),
            -g.count,
            str(g.finding.get("file_path") or ""),
            _label_of(g.finding),
        ),
    )


# ── Width-aware column layout ───────────────────────────────────────────────


@dataclass(frozen=True)
class _ColumnSpec:
    """Layout rules for one findings-table column.

    ``priority`` 0 means the column is never dropped; higher numbers are
    dropped first when the terminal is too narrow to fit every minimum width.
    ``flex`` is the share of any leftover width the column claims.
    """

    key: str
    header: str
    min_width: int
    max_width: int
    flex: int = 0
    priority: int = 0
    style: str = ""
    justify: str = "left"


_COLUMN_SPECS: tuple[_ColumnSpec, ...] = (
    _ColumnSpec("file", "File", 22, 60, flex=3, priority=0, style="cyan"),
    _ColumnSpec("finding", "Finding", 22, 44, flex=2, priority=0),
    _ColumnSpec("count", "Count", 5, 7, flex=0, priority=1, style="dim", justify="right"),
    # Severity is short and load-bearing: fixed at exactly len("critical").
    _ColumnSpec("severity", "Severity", 8, 8, flex=0, priority=0),
    _ColumnSpec("owasp", "OWASP", 5, 6, flex=0, priority=2, style="yellow"),
    _ColumnSpec("provider", "Provider", 9, 16, flex=1, priority=3, style="magenta"),
    _ColumnSpec("fix", "Fix", 14, 34, flex=2, priority=4, style="dim"),
)

# Rich renders 2 cells of padding plus one border per column, plus a trailing border.
_PER_COLUMN_CHROME: int = 3
_TABLE_EDGE_CHROME: int = 1

#: Absolute floor a flexible column may be shrunk to on very narrow terminals.
_FLOOR_WIDTH: int = 8


def _layout_columns(
    specs: tuple[_ColumnSpec, ...] | list[_ColumnSpec],
    total_width: int,
) -> list[tuple[_ColumnSpec, int]]:
    """Pick which columns fit in ``total_width`` and how wide each should be."""
    columns: list[_ColumnSpec] = list(specs)

    def chrome(count: int) -> int:
        return _PER_COLUMN_CHROME * count + _TABLE_EDGE_CHROME

    # Drop the least important columns until every minimum width fits.
    while len(columns) > 1:
        if chrome(len(columns)) + sum(c.min_width for c in columns) <= total_width:
            break
        droppable = [c for c in columns if c.priority > 0]
        if not droppable:
            break
        columns.remove(max(droppable, key=lambda c: c.priority))

    widths: dict[str, int] = {c.key: c.min_width for c in columns}
    leftover = total_width - chrome(len(columns)) - sum(widths.values())

    # Very narrow terminal: even the undroppable columns overflow. Shrink the
    # flexible ones toward a hard floor; fixed columns (Severity) stay intact.
    deficit = -leftover
    while deficit > 0:
        shrinkable = [c for c in columns if c.flex and widths[c.key] > _FLOOR_WIDTH]
        if not shrinkable:
            break
        widths[max(shrinkable, key=lambda c: widths[c.key]).key] -= 1
        deficit -= 1

    # Hand leftover space to flexible columns, capped at their max width.
    while leftover > 0:
        growable = [c for c in columns if c.flex and widths[c.key] < c.max_width]
        if not growable:
            break
        flex_total = sum(c.flex for c in growable)
        handed_out = 0
        for c in growable:
            share = min(leftover * c.flex // flex_total, c.max_width - widths[c.key])
            widths[c.key] += share
            handed_out += share
        if handed_out == 0:
            # Integer division starved everyone; give the remainder to the
            # widest-flex column so the space is not wasted.
            best = max(growable, key=lambda c: c.flex)
            widths[best.key] += min(leftover, best.max_width - widths[best.key])
            break
        leftover -= handed_out

    return [(c, widths[c.key]) for c in columns]


def _truncate_left(text: str, max_len: int) -> str:
    """Trim from the left so the tail (filename, line number) stays visible."""
    if max_len <= 0:
        return ""
    if len(text) <= max_len:
        return text
    if max_len == 1:
        return _ELLIPSIS
    tail = text[-(max_len - 1):]
    # Prefer starting at a path separator so whole segments are shown.
    sep = tail.find("/")
    if 0 <= sep < max(1, max_len // 3):
        tail = tail[sep:]
    return _ELLIPSIS + tail


def _truncate_right(text: str, max_len: int) -> str:
    """Trim from the right, keeping the most significant prefix."""
    if max_len <= 0:
        return ""
    if len(text) <= max_len:
        return text
    if max_len == 1:
        return _ELLIPSIS
    return text[: max_len - 1] + _ELLIPSIS


def _location_cell(group: FindingGroup, width: int) -> str:
    """'path/to/file.py:42', left-truncated to keep the filename readable."""
    location = str(group.finding.get("file_path") or "")
    if group.first_line is not None:
        location = f"{location}:{group.first_line}"
    return _truncate_left(location, width)


def print_findings_table(
    findings: list[dict[str, Any]],
    severity_filter: str | None = None,
    show_hints: bool = True,
    max_rows: int = DEFAULT_MAX_ROWS,
) -> None:
    """Print findings as a deduplicated, severity-sorted, width-aware table.

    Repeated detections of the same thing in the same file collapse into a
    single row carrying an occurrence count, and the table is capped at
    ``max_rows`` rows (pass 0 for no cap). Display-only: ``findings`` is never
    mutated, so every other output format and all counts are unaffected.
    """
    # Apply severity filter
    if severity_filter:
        min_order = _SEVERITY_ORDER.get(severity_filter.lower(), 4)
        findings = [
            f for f in findings
            if _SEVERITY_ORDER.get(_severity_of(f), 4) <= min_order
        ]

    if not findings:
        console.print("\n  [dim]No findings to display.[/dim]\n")
        return

    groups = _sort_groups(group_findings(findings))
    total_findings = len(findings)

    visible = groups if max_rows <= 0 else groups[:max_rows]
    hidden_findings = sum(g.count for g in groups[len(visible):])

    if len(groups) < total_findings:
        title = f"Findings ({total_findings} total, {len(groups)} unique)"
    else:
        title = f"Findings ({total_findings} total)"

    caption: str | None = None
    if hidden_findings:
        caption = (
            f"{_ELLIPSIS} and {hidden_findings} more findings "
            f"(use -o json for the full list)"
        )

    specs = _COLUMN_SPECS if show_hints else tuple(c for c in _COLUMN_SPECS if c.key != "fix")
    layout = _layout_columns(specs, console.width)
    widths: dict[str, int] = {spec.key: width for spec, width in layout}

    table = Table(
        title=title,
        caption=caption,
        caption_style="dim",
        show_header=True,
        header_style="bold",
        border_style="dim",
        padding=(0, 1),
    )
    for spec, width in layout:
        table.add_column(
            spec.header,
            style=spec.style or None,
            width=width,
            justify=spec.justify,  # type: ignore[arg-type]
            no_wrap=True,
            overflow="ellipsis",
        )

    for group in visible:
        f = group.finding
        label = _label_of(f)
        # If the terminal was too narrow for a Count column, keep the
        # occurrence count visible by folding it into the finding name.
        if "count" not in widths and group.count > 1:
            label = f"{label} {_TIMES}{group.count}"

        cells: dict[str, Any] = {
            "file": _location_cell(group, widths.get("file", 0)),
            "finding": _truncate_right(label, widths.get("finding", 0)),
            "count": f"{_TIMES}{group.count}" if group.count > 1 else "",
            "severity": _severity_text(_severity_of(f)),
            "owasp": str(f.get("owasp_id") or ""),
            "provider": _provider_of(f) or "-",
            "fix": _truncate_right(get_fix_hint(f), widths.get("fix", 0)),
        }
        table.add_row(*(cells[spec.key] for spec, _ in layout))

    console.print()
    console.print(table)
    console.print()


# ── Action summary ─────────────────────────────────────────────────────────


def print_action_summary(
    findings: list[dict[str, Any]],
    risk_result: dict[str, Any] | None = None,
) -> None:
    """Print a prioritized action summary with fixes and next steps."""
    if not findings:
        console.print(Panel(
            "  [bold green]No AI security issues found.[/bold green]\n\n"
            "  Your codebase looks clean. Run [bold]scanllm report aibom[/bold] to generate\n"
            "  an AI Bill of Materials for compliance documentation.",
            title="[bold cyan]Action Summary[/bold cyan]",
            border_style="green",
            padding=(1, 2),
        ))
        return

    # Group by severity
    critical: list[dict[str, Any]] = []
    high: list[dict[str, Any]] = []
    medium: list[dict[str, Any]] = []
    low: list[dict[str, Any]] = []

    for f in findings:
        sev = (f.get("severity") or f.get("pattern_severity") or "info").lower()
        if sev == "critical":
            critical.append(f)
        elif sev == "high":
            high.append(f)
        elif sev == "medium":
            medium.append(f)
        else:
            low.append(f)

    lines: list[str] = []

    # Critical issues
    if critical:
        lines.append(f"  [bold red]Critical Issues ({len(critical)}) — fix these first[/bold red]")
        for f in critical[:5]:
            file_path = f.get("file_path", "")
            line = f.get("line_number", "")
            loc = f"{file_path}:{line}" if line else file_path
            if len(loc) > 45:
                loc = "..." + loc[-42:]
            name = f.get("pattern_name", f.get("message", "unknown"))
            hint = get_fix_hint(f)
            lines.append(f"    [red]•[/red] {name} in [cyan]{loc}[/cyan]")
            if hint:
                lines.append(f"      [dim]→ {hint}[/dim]")
        if len(critical) > 5:
            lines.append(f"      [dim]... and {len(critical) - 5} more[/dim]")
        lines.append("")

    # High issues
    if high:
        lines.append(f"  [bold yellow]High Severity ({len(high)})[/bold yellow]")
        for f in high[:3]:
            file_path = f.get("file_path", "")
            line = f.get("line_number", "")
            loc = f"{file_path}:{line}" if line else file_path
            if len(loc) > 45:
                loc = "..." + loc[-42:]
            name = f.get("pattern_name", f.get("message", "unknown"))
            hint = get_fix_hint(f)
            lines.append(f"    [yellow]•[/yellow] {name} in [cyan]{loc}[/cyan]")
            if hint:
                lines.append(f"      [dim]→ {hint}[/dim]")
        if len(high) > 3:
            lines.append(f"      [dim]... and {len(high) - 3} more[/dim]")
        lines.append("")

    # Medium/Low summary
    if medium or low:
        parts = []
        if medium:
            parts.append(f"{len(medium)} medium")
        if low:
            parts.append(f"{len(low)} low")
        lines.append(f"  [dim]{', '.join(parts)} severity issues (run scanllm fix for details)[/dim]")
        lines.append("")

    # What's good section
    all_owasp = set(f.get("owasp_id", "") for f in findings if f.get("owasp_id"))
    good_things = []
    if "LLM01" not in all_owasp:
        good_things.append("No prompt injection risks detected")
    if "LLM05" not in all_owasp:
        good_things.append("No unsafe output handling (eval/exec)")
    if not any(f.get("pattern_category") == "secret" or "secret" in (f.get("pattern_name", "") or "").lower() for f in findings):
        good_things.append("No hardcoded API keys found")

    if good_things:
        lines.append("  [bold green]What's good[/bold green]")
        for g in good_things[:3]:
            lines.append(f"    [green]✓[/green] {g}")
        lines.append("")

    # Next steps
    lines.append("  [bold]Next Steps[/bold]")
    lines.append("    [cyan]scanllm fix[/cyan]          [dim]← Detailed fix suggestions with code examples[/dim]")
    lines.append("    [cyan]scanllm policy check[/cyan]  [dim]← Enforce team security policies[/dim]")
    lines.append("    [cyan]scanllm report aibom[/cyan]  [dim]← Generate AI-BOM for compliance[/dim]")
    lines.append("    [cyan]scanllm ui[/cyan]            [dim]← Interactive dashboard + dependency graph[/dim]")

    console.print(Panel(
        "\n".join(lines),
        title="[bold cyan]Action Summary[/bold cyan]",
        border_style="cyan",
        padding=(1, 2),
    ))


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
    """Shorten a path from the left, keeping the filename visible."""
    return _truncate_left(path, max_len)
