"""scanllm doctor — Check environment and installation health."""

from __future__ import annotations

import sys
from pathlib import Path

import typer
from rich.console import Console

from cli.config import ScanLLMConfig

console = Console()


def doctor(
    path: str = typer.Argument(".", help="Repository path"),
) -> None:
    """Check your ScanLLM installation and environment."""
    repo_path = Path(path).resolve()
    config = ScanLLMConfig(repo_path)
    issues = 0

    console.print("\n[bold cyan]ScanLLM Doctor[/bold cyan]\n")

    # Python version
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= (3, 9):
        console.print(f"  [green]\u2713[/green] Python {py_ver}")
    else:
        console.print(f"  [red]\u2717[/red] Python {py_ver} \u2014 requires 3.9+")
        issues += 1

    # ScanLLM version
    try:
        from core import __version__
        console.print(f"  [green]\u2713[/green] scanllm {__version__}")
    except ImportError:
        console.print("  [red]\u2717[/red] core package not found")
        issues += 1

    # Core dependencies
    core_deps = [
        ("typer", "CLI framework"),
        ("rich", "Terminal formatting"),
        ("yaml", "YAML parsing"),
        ("networkx", "Graph analysis"),
        ("git", "Git operations"),
    ]
    all_core = True
    for mod, desc in core_deps:
        try:
            __import__(mod)
        except ImportError:
            console.print(f"  [red]\u2717[/red] {mod} not installed ({desc})")
            issues += 1
            all_core = False
    if all_core:
        console.print("  [green]\u2713[/green] All core dependencies installed")

    # Optional dependencies
    optional_deps = [
        ("fastapi", "scanllm ui", "pip install scanllm[server]"),
        ("uvicorn", "scanllm ui", "pip install scanllm[server]"),
        ("watchdog", "scanllm watch", "pip install scanllm[watch]"),
        ("xhtml2pdf", "scanllm report pdf", "pip install scanllm[reports]"),
    ]
    for mod, feature, install_cmd in optional_deps:
        try:
            __import__(mod)
            console.print(f"  [green]\u2713[/green] {mod} installed ({feature})")
        except ImportError:
            console.print(f"  [yellow]![/yellow] {mod} not installed (needed for {feature})")
            console.print(f"     [dim]\u2192 {install_cmd}[/dim]")

    # .scanllm directory
    console.print()
    if config.is_initialized():
        console.print(f"  [green]\u2713[/green] .scanllm/ directory initialized")

        # Policies
        policies_path = config.get_policies_path()
        if policies_path:
            console.print(f"  [green]\u2713[/green] policies.yaml found")
        else:
            console.print("  [yellow]![/yellow] No policies.yaml \u2014 using built-in defaults")
            console.print("     [dim]\u2192 scanllm policy init[/dim]")

        # Scans
        scans = config.get_scan_history()
        if scans:
            console.print(f"  [green]\u2713[/green] {len(scans)} saved scan(s) found")
        else:
            console.print("  [yellow]![/yellow] No saved scans")
            console.print("     [dim]\u2192 scanllm scan . --save[/dim]")
    else:
        console.print("  [yellow]![/yellow] .scanllm/ not initialized")
        console.print("     [dim]\u2192 scanllm init[/dim]")

    # Git repo
    git_dir = repo_path / ".git"
    if git_dir.exists():
        console.print(f"  [green]\u2713[/green] Git repository detected")
    else:
        console.print("  [dim]![/dim] Not a git repository")

    # Signatures
    try:
        from core.scanner.engine import ScanEngine
        engine = ScanEngine()
        sig_count = 0
        if hasattr(engine, 'signatures') and engine.signatures:
            for section in engine.signatures.values():
                if isinstance(section, dict):
                    sig_count += len(section)
        if sig_count > 0:
            console.print(f"  [green]\u2713[/green] AI signatures loaded ({sig_count} providers)")
        else:
            console.print(f"  [green]\u2713[/green] AI signatures available")
    except Exception:
        console.print("  [yellow]![/yellow] Could not load AI signatures")

    # Summary
    console.print()
    if issues == 0:
        console.print("  [bold green]All checks passed![/bold green]\n")
    else:
        console.print(f"  [bold red]{issues} issue(s) found.[/bold red]\n")
        raise typer.Exit(code=1)
