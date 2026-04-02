"""scanllm telemetry [on|off|status] — Manage anonymous telemetry."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from cli.config import ScanLLMConfig

console = Console()

telemetry_app = typer.Typer(help="Manage anonymous telemetry collection.")


@telemetry_app.command(name="status")
def telemetry_status(
    path: str = typer.Argument(".", help="Repository path"),
) -> None:
    """Show whether telemetry is enabled or disabled."""
    from cli.telemetry import is_enabled

    repo_path = Path(path).resolve()
    config = ScanLLMConfig(repo_path)
    config_yaml = config.base_dir / "config.yaml" if config.is_initialized() else None

    enabled = is_enabled(config_yaml)
    if enabled:
        console.print("\n  [bold green]Telemetry is enabled[/bold green]")
        console.print("  Anonymous usage data helps improve ScanLLM.")
    else:
        console.print("\n  [bold yellow]Telemetry is disabled[/bold yellow]")

    console.print(f"  Config: {config_yaml or 'not initialized'}")
    console.print(f"  Env override: SCANLLM_TELEMETRY={__import__('os').environ.get('SCANLLM_TELEMETRY', '(not set)')}")
    console.print()


@telemetry_app.command(name="on")
def telemetry_on(
    path: str = typer.Argument(".", help="Repository path"),
) -> None:
    """Enable anonymous telemetry collection."""
    _set_telemetry(path, True)
    console.print("\n  [bold green]Telemetry enabled.[/bold green]")
    console.print("  Anonymous usage data will be collected to help improve ScanLLM.\n")


@telemetry_app.command(name="off")
def telemetry_off(
    path: str = typer.Argument(".", help="Repository path"),
) -> None:
    """Disable anonymous telemetry collection."""
    _set_telemetry(path, False)
    console.print("\n  [bold yellow]Telemetry disabled.[/bold yellow]")
    console.print("  No usage data will be collected.\n")


def _set_telemetry(path: str, enabled: bool) -> None:
    """Update telemetry.enabled in .scanllm/config.yaml."""
    repo_path = Path(path).resolve()
    config = ScanLLMConfig(repo_path)

    if not config.is_initialized():
        config.initialize()

    config_file = config.base_dir / "config.yaml"
    try:
        import yaml
        data = yaml.safe_load(config_file.read_text()) or {}
        if "telemetry" not in data:
            data["telemetry"] = {}
        data["telemetry"]["enabled"] = enabled
        config_file.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))
    except Exception as exc:
        console.print(f"  [red]Error updating config:[/red] {exc}")
        raise typer.Exit(code=1)
