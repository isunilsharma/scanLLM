"""scanllm diff — Compare scan results to detect drift."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer
from rich.console import Console

from cli.config import ScanLLMConfig

console = Console()


def diff_cmd(
    path: str = typer.Argument(".", help="Repository path"),
    baseline: str = typer.Option(None, "--baseline", "-b", help="Path to baseline scan JSON file"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table, json"),
) -> None:
    """Compare latest scan against previous scan or a baseline to detect drift."""
    repo_path = Path(path).resolve()
    config = ScanLLMConfig(repo_path)

    # Load scans to compare
    new_scan = config.get_latest_scan()
    if new_scan is None:
        console.print(
            "[bold red]Error:[/bold red] No saved scans found.\n"
            "  Run [bold]scanllm scan --save[/bold] first."
        )
        raise typer.Exit(code=1)

    if baseline:
        baseline_path = Path(baseline).resolve()
        if not baseline_path.exists():
            console.print(f"[bold red]Error:[/bold red] Baseline file not found: {baseline_path}")
            raise typer.Exit(code=1)
        import json
        try:
            with open(baseline_path, encoding="utf-8") as fh:
                old_scan = json.load(fh)
        except Exception as exc:
            console.print(f"[bold red]Error:[/bold red] Failed to load baseline: {exc}")
            raise typer.Exit(code=1)
    else:
        old_scan = config.get_previous_scan()
        if old_scan is None:
            console.print(
                "[yellow]No previous scan found for comparison.[/yellow]\n"
                "  Run [bold]scanllm scan --save[/bold] again to create a second scan for diff."
            )
            raise typer.Exit(code=0)

    # Run diff
    try:
        from core.diff.differ import ScanDiffer
    except ImportError:
        console.print(
            "[bold red]Error:[/bold red] Could not import core diff engine.\n"
            "  Make sure the [cyan]core[/cyan] package is installed."
        )
        raise typer.Exit(code=1)

    differ = ScanDiffer()
    scan_diff = differ.diff(old_scan, new_scan)
    diff_dict = scan_diff.to_dict()

    if output == "json":
        import json
        import sys
        sys.stdout.write(json.dumps(diff_dict, indent=2, default=str) + "\n")
    else:
        from cli.output.table import print_diff_result
        print_diff_result(diff_dict)
