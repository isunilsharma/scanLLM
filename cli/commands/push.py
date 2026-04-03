"""scanllm push — Push local scan results to the ScanLLM cloud platform."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
from rich.console import Console

from cli.config import ScanLLMConfig

console = Console()


def push(
    path: str = typer.Argument(".", help="Repository path containing .scanllm/ directory"),
    scan_id: str = typer.Option(
        None,
        "--scan-id",
        help="Timestamp of a specific scan to push (e.g. 20260328T230000Z). Defaults to latest.",
    ),
    cloud_url: str = typer.Option(
        None,
        "--cloud-url",
        help="Cloud platform URL (default: stored URL or https://scanllm.ai)",
    ),
    token: str = typer.Option(
        None,
        "--token",
        "-t",
        help="API token (default: read from ~/.scanllm/credentials)",
    ),
) -> None:
    """Push a local scan to the ScanLLM cloud platform."""
    # Resolve auth token
    api_token = _resolve_token(token)
    if not api_token:
        console.print(
            "[bold red]Error:[/bold red] No API token provided.\n"
            "  Either pass [bold]--token <token>[/bold] or run "
            "[bold]scanllm auth login --token <token>[/bold] first."
        )
        raise typer.Exit(code=1)

    # Resolve cloud URL
    base_url = _resolve_cloud_url(cloud_url)

    # Load the scan data
    repo_path = Path(path).resolve()
    config = ScanLLMConfig(repo_path)

    if not config.is_initialized():
        console.print(
            "[bold red]Error:[/bold red] No .scanllm/ directory found.\n"
            "  Run [bold]scanllm scan --save[/bold] first."
        )
        raise typer.Exit(code=1)

    scan_data = _load_scan(config, scan_id)
    if scan_data is None:
        if scan_id:
            console.print(
                f"[bold red]Error:[/bold red] Scan with ID [cyan]{scan_id}[/cyan] not found.\n"
                f"  Available scans:"
            )
            for entry in config.get_scan_history():
                console.print(f"    - {entry['timestamp']}  ({entry['total_findings']} findings)")
        else:
            console.print(
                "[bold red]Error:[/bold red] No saved scans found.\n"
                "  Run [bold]scanllm scan --save[/bold] first."
            )
        raise typer.Exit(code=1)

    # Display what we're pushing
    summary = scan_data.get("summary", {})
    total_findings = summary.get("total_findings", len(scan_data.get("findings", [])))
    scan_timestamp = scan_data.get("timestamp", "unknown")
    scan_path_str = scan_data.get("path", str(repo_path))

    console.print(f"\n  [bold cyan]ScanLLM Push[/bold cyan]")
    console.print(f"  Scan:      [dim]{scan_timestamp}[/dim]")
    console.print(f"  Path:      [dim]{scan_path_str}[/dim]")
    console.print(f"  Findings:  [dim]{total_findings}[/dim]")
    console.print(f"  Cloud URL: [cyan]{base_url}[/cyan]")
    console.print()

    # POST to the import endpoint
    import_url = f"{base_url}/api/v1/scans/import"

    try:
        import httpx
    except ImportError:
        console.print(
            "[bold red]Error:[/bold red] [cyan]httpx[/cyan] is required for cloud sync.\n"
            "  Install with: [dim]pip install httpx[/dim]"
        )
        raise typer.Exit(code=1)

    try:
        with console.status("[cyan]Uploading scan to cloud...[/cyan]"):
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    import_url,
                    json=scan_data,
                    headers={
                        "Authorization": f"Bearer {api_token}",
                        "Content-Type": "application/json",
                    },
                )

        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            cloud_scan_id = result.get("scan_id", "unknown")
            console.print(f"  [green]Scan pushed successfully.[/green]")
            console.print(f"  Cloud scan ID: [cyan]{cloud_scan_id}[/cyan]")
            console.print(
                f"  View at: [link={base_url}/scans/{cloud_scan_id}]{base_url}/scans/{cloud_scan_id}[/link]"
            )
        elif response.status_code == 401:
            console.print(
                "[bold red]Error:[/bold red] Authentication failed (401).\n"
                "  Check your API token with [bold]scanllm auth status[/bold]."
            )
            raise typer.Exit(code=1)
        elif response.status_code == 422:
            detail = response.json().get("detail", "Validation error")
            console.print(
                f"[bold red]Error:[/bold red] Invalid scan data (422).\n"
                f"  Detail: {detail}"
            )
            raise typer.Exit(code=1)
        else:
            console.print(
                f"[bold red]Error:[/bold red] Push failed with status {response.status_code}.\n"
                f"  Response: {response.text[:500]}"
            )
            raise typer.Exit(code=1)

    except httpx.ConnectError:
        console.print(
            f"[bold red]Error:[/bold red] Could not connect to [cyan]{base_url}[/cyan].\n"
            f"  Check the URL and your network connection."
        )
        raise typer.Exit(code=1)
    except httpx.TimeoutException:
        console.print(
            "[bold red]Error:[/bold red] Request timed out.\n"
            "  The scan may be too large. Try again or contact support."
        )
        raise typer.Exit(code=1)

    console.print()


def _resolve_token(cli_token: str | None) -> str | None:
    """Get the API token from CLI arg or stored credentials."""
    if cli_token:
        return cli_token.strip()

    try:
        from cli.commands.auth import get_stored_token
        return get_stored_token()
    except ImportError:
        return None


def _resolve_cloud_url(cli_url: str | None) -> str:
    """Get the cloud URL from CLI arg or stored credentials."""
    if cli_url:
        return cli_url.rstrip("/")

    try:
        from cli.commands.auth import get_stored_cloud_url
        return get_stored_cloud_url()
    except ImportError:
        return "https://scanllm.ai"


def _load_scan(config: ScanLLMConfig, scan_id: str | None) -> dict[str, Any] | None:
    """Load a specific scan by timestamp or the latest scan."""
    if scan_id is None:
        return config.get_latest_scan()

    # Look for a scan file matching the given timestamp/ID
    scans_dir = config.scanllm_dir / "scans"
    if not scans_dir.is_dir():
        return None

    # Try exact filename match: scan_<scan_id>.json
    target = scans_dir / f"scan_{scan_id}.json"
    if target.exists():
        try:
            return json.loads(target.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    # Try partial match (prefix)
    for scan_file in sorted(scans_dir.glob("scan_*.json")):
        if scan_id in scan_file.stem:
            try:
                return json.loads(scan_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue

    return None
