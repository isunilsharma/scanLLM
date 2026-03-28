"""scanllm init — Initialize .scanllm/ directory."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from cli.config import ScanLLMConfig

console = Console()


def init(
    path: str = typer.Argument(".", help="Path to initialize (default: current directory)"),
    force: bool = typer.Option(False, "--force", help="Re-initialize even if .scanllm/ already exists"),
) -> None:
    """Initialize ScanLLM in a repository. Creates .scanllm/ with default configuration."""
    repo_path = Path(path).resolve()
    if not repo_path.is_dir():
        console.print(f"[bold red]Error:[/bold red] Path is not a directory: {repo_path}")
        raise typer.Exit(code=1)

    config = ScanLLMConfig(repo_path)

    if config.is_initialized() and not force:
        console.print(
            f"[yellow]Already initialized:[/yellow] {config.scanllm_dir}\n"
            f"  Use [bold]--force[/bold] to re-initialize."
        )
        raise typer.Exit(code=0)

    config.initialize()

    console.print(f"\n[bold green]Initialized ScanLLM[/bold green] in {config.scanllm_dir}\n")
    console.print("  Created:")
    console.print(f"    [cyan].scanllm/config.yaml[/cyan]    — scan settings")
    console.print(f"    [cyan].scanllm/policies.yaml[/cyan]  — policy rules")
    console.print(f"    [cyan].scanllm/scans/[/cyan]         — scan history")
    console.print(f"    [cyan].scanllm/baselines/[/cyan]     — baseline scans")
    console.print(f"    [cyan].scanllmignore[/cyan]          — files to skip")
    console.print()
    console.print("  Next steps:")
    console.print("    [bold]scanllm scan[/bold]              Run your first scan")
    console.print("    [bold]scanllm scan --save[/bold]       Scan and save results")
    console.print("    [bold]scanllm policy list[/bold]       View configured policies")
    console.print()
