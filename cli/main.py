#!/usr/bin/env python3
"""ScanLLM -- AI Dependency Intelligence Platform CLI."""

from __future__ import annotations

import typer
from rich.console import Console

from cli.commands import scan, init_cmd, policy, diff, ui, watch, report, fix

app = typer.Typer(
    name="scanllm",
    help="AI Dependency Intelligence -- scan, govern, and visualize AI in your code.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

console = Console()

BANNER = r"""
[bold cyan]
  ███████╗ ██████╗ █████╗ ███╗   ██╗██╗     ██╗     ███╗   ███╗
  ██╔════╝██╔════╝██╔══██╗████╗  ██║██║     ██║     ████╗ ████║
  ███████╗██║     ███████║██╔██╗ ██║██║     ██║     ██╔████╔██║
  ╚════██║██║     ██╔══██║██║╚██╗██║██║     ██║     ██║╚██╔╝██║
  ███████║╚██████╗██║  ██║██║ ╚████║███████╗███████╗██║ ╚═╝ ██║
  ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝╚═╝     ╚═╝
[/bold cyan]
  [dim]AI Dependency Intelligence[/dim] [bold white]v2.0.0[/bold white]
"""

VERSION = "2.0.0"

# ── Register top-level commands ─────────────────────────────────────────────
app.command(name="scan")(scan.scan)
app.command(name="init")(init_cmd.init)
app.command(name="diff")(diff.diff_cmd)
app.command(name="ui")(ui.ui)
app.command(name="watch")(watch.watch_cmd)
app.command(name="fix")(fix.fix)

# ── Register sub-command groups ─────────────────────────────────────────────
app.add_typer(policy.policy_app, name="policy", help="Policy management commands.")
app.add_typer(report.report_app, name="report", help="Report generation commands.")


# ── Version callback ────────────────────────────────────────────────────────

def _version_callback(value: bool) -> None:
    if value:
        console.print(f"scanllm v{VERSION}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None, "--version", "-v", callback=_version_callback, is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """ScanLLM -- Know every AI dependency. Enforce every policy."""


def entry_point() -> None:
    """Package entry-point (used by ``console_scripts``)."""
    app()


if __name__ == "__main__":
    entry_point()
