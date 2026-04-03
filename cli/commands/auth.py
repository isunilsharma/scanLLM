"""scanllm auth — Manage cloud authentication credentials."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
from rich.console import Console

console = Console()

auth_app = typer.Typer(help="Manage cloud authentication for ScanLLM.")

# Credentials are stored in ~/.scanllm/credentials
CREDENTIALS_DIR = Path.home() / ".scanllm"
CREDENTIALS_FILE = CREDENTIALS_DIR / "credentials"


def _load_credentials() -> dict[str, Any]:
    """Load stored credentials, or return empty dict."""
    if not CREDENTIALS_FILE.exists():
        return {}
    try:
        return json.loads(CREDENTIALS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_credentials(data: dict[str, Any]) -> None:
    """Save credentials to ~/.scanllm/credentials."""
    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
    CREDENTIALS_FILE.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )
    # Restrict file permissions (owner read/write only)
    try:
        CREDENTIALS_FILE.chmod(0o600)
    except OSError:
        pass


def get_stored_token() -> str | None:
    """Return the stored API token, or None if not authenticated."""
    creds = _load_credentials()
    return creds.get("token")


def get_stored_cloud_url() -> str:
    """Return the stored cloud URL, or the default."""
    creds = _load_credentials()
    return creds.get("cloud_url", "https://scanllm.ai")


@auth_app.command(name="login")
def login(
    token: str = typer.Option(..., "--token", "-t", help="API token from scanllm.ai"),
    cloud_url: str = typer.Option(
        "https://scanllm.ai",
        "--cloud-url",
        help="Cloud platform URL",
    ),
) -> None:
    """Authenticate with the ScanLLM cloud platform."""
    if not token.strip():
        console.print("[bold red]Error:[/bold red] Token cannot be empty.")
        raise typer.Exit(code=1)

    creds = _load_credentials()
    creds["token"] = token.strip()
    creds["cloud_url"] = cloud_url.rstrip("/")
    _save_credentials(creds)

    console.print(
        f"\n  [green]Authenticated successfully.[/green]\n"
        f"  Cloud URL: [cyan]{cloud_url}[/cyan]\n"
        f"  Credentials saved to: [dim]{CREDENTIALS_FILE}[/dim]\n"
    )


@auth_app.command(name="status")
def status() -> None:
    """Show current authentication status."""
    creds = _load_credentials()
    token = creds.get("token")
    cloud_url = creds.get("cloud_url", "https://scanllm.ai")

    console.print("\n  [bold cyan]ScanLLM Auth Status[/bold cyan]\n")

    if token:
        # Mask the token, showing only first 4 and last 4 characters
        if len(token) > 12:
            masked = token[:4] + "*" * (len(token) - 8) + token[-4:]
        else:
            masked = "****"
        console.print(f"  Status:    [green]Authenticated[/green]")
        console.print(f"  Token:     [dim]{masked}[/dim]")
        console.print(f"  Cloud URL: [cyan]{cloud_url}[/cyan]")
        console.print(f"  File:      [dim]{CREDENTIALS_FILE}[/dim]")
    else:
        console.print(f"  Status:    [yellow]Not authenticated[/yellow]")
        console.print(
            f"\n  Run [bold]scanllm auth login --token <token>[/bold] to authenticate."
        )

    console.print()


@auth_app.command(name="logout")
def logout() -> None:
    """Remove stored credentials."""
    if CREDENTIALS_FILE.exists():
        CREDENTIALS_FILE.unlink()
        console.print("\n  [green]Logged out.[/green] Credentials removed.\n")
    else:
        console.print("\n  [dim]No credentials found. Already logged out.[/dim]\n")
