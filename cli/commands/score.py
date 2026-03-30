"""scanllm score — Explain and break down the risk score."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress_bar import ProgressBar
from rich.table import Table
from rich.text import Text

from cli.config import ScanLLMConfig

console = Console()

_GRADE_STYLES = {"A": "bold green", "B": "green", "C": "yellow", "D": "red", "F": "bold red"}


def score(
    path: str = typer.Argument(".", help="Repository path"),
) -> None:
    """Show a detailed breakdown of your AI security risk score."""
    repo_path = Path(path).resolve()
    config = ScanLLMConfig(repo_path)
    latest = config.get_latest_scan()

    if latest is None:
        console.print("[bold red]Error:[/bold red] No saved scans found.\n  Run [bold]scanllm scan --save[/bold] first.")
        raise typer.Exit(code=1)

    risk = latest.get("risk", {})
    score_val = risk.get("overall_score", latest.get("risk_score", 0))
    grade = risk.get("grade", "?")
    grade_style = _GRADE_STYLES.get(grade, "white")
    findings = latest.get("findings", [])

    # Calculate breakdown
    secrets = sum(1 for f in findings if "secret" in (f.get("pattern_name", "") or "").lower() or f.get("pattern_category") == "secret")
    critical_owasp = sum(1 for f in findings if (f.get("severity") or f.get("pattern_severity", "")).lower() == "critical")
    high_owasp = sum(1 for f in findings if (f.get("severity") or f.get("pattern_severity", "")).lower() == "high")
    missing_safety = sum(1 for f in findings if "max_tokens" in (f.get("pattern_name", "") or "").lower())
    excessive_agent = sum(1 for f in findings if "excessive" in (f.get("pattern_name", "") or "").lower() or "agency" in (f.get("pattern_name", "") or "").lower())

    providers = set()
    for f in findings:
        p = f.get("provider", "")
        if p:
            providers.add(p)
    concentration = 1 if len(providers) <= 1 and providers else 0

    breakdown = [
        ("Hardcoded secrets", secrets * 25, secrets, "Move keys to environment variables"),
        ("Critical OWASP findings", critical_owasp * 20, critical_owasp, "Fix eval(), exec(), unsanitized output"),
        ("High OWASP findings", high_owasp * 10, high_owasp, "Address prompt injection, agency risks"),
        ("Provider concentration", concentration * 10, concentration, "Add fallback provider"),
        ("Missing safety configs", missing_safety * 3, missing_safety, "Add max_tokens to LLM calls"),
        ("Excessive agent permissions", excessive_agent * 15, excessive_agent, "Restrict agent tool access"),
    ]

    # Filter to non-zero
    active_breakdown = [(name, points, count, fix) for name, points, count, fix in breakdown if points > 0]
    raw_total = sum(p for _, p, _, _ in active_breakdown)

    # Header
    console.print()
    console.print(Panel(
        f"  [bold]Risk Score:[/bold] {score_val}/100  [{grade_style}]Grade {grade}[/{grade_style}]",
        title="[bold cyan]ScanLLM Risk Assessment[/bold cyan]",
        border_style="cyan",
        padding=(0, 2),
    ))

    if not active_breakdown:
        console.print("\n  [bold green]Excellent![/bold green] No risk factors detected.\n")
        return

    # Breakdown table
    table = Table(
        title="Score Breakdown",
        show_header=True,
        header_style="bold",
        border_style="dim",
        padding=(0, 1),
    )
    table.add_column("Risk Factor", max_width=30)
    table.add_column("Points", justify="right", max_width=8)
    table.add_column("Count", justify="right", max_width=6)
    table.add_column("Bar", max_width=20)
    table.add_column("How to Fix", style="dim", max_width=35)

    max_points = max(p for _, p, _, _ in active_breakdown) if active_breakdown else 1
    for name, points, count, fix in sorted(active_breakdown, key=lambda x: -x[1]):
        bar_len = int((points / max_points) * 15)
        bar = "[red]" + "\u2588" * bar_len + "[/red]" + "[dim]" + "\u2591" * (15 - bar_len) + "[/dim]"
        table.add_row(name, f"+{points}", str(count), bar, fix)

    console.print()
    console.print(table)

    # Improvement suggestions
    console.print()
    console.print("[bold]  To improve your score:[/bold]")
    for i, (name, points, count, fix) in enumerate(sorted(active_breakdown, key=lambda x: -x[1])[:3], 1):
        console.print(f"    {i}. {fix} [dim](saves up to {points} points)[/dim]")
    console.print()
