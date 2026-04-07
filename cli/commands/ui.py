"""scanllm ui — Launch local dashboard server."""

from __future__ import annotations

import webbrowser
from pathlib import Path

import typer
from rich.console import Console

console = Console()

DEFAULT_PORT = 5787
DEFAULT_HOST = "127.0.0.1"


def ui(
    path: str = typer.Argument(".", help="Repository path to serve"),
    port: int = typer.Option(DEFAULT_PORT, "--port", help="Port number"),
    host: str = typer.Option(DEFAULT_HOST, "--host", help="Host to bind to"),
    no_open: bool = typer.Option(False, "--no-open", help="Do not open browser automatically"),
) -> None:
    """Launch the local ScanLLM dashboard in your browser."""
    repo_path = Path(path).resolve()

    try:
        import fastapi  # noqa: F401
        import uvicorn
    except ImportError:
        console.print(
            "[bold red]Error:[/bold red] FastAPI and uvicorn are required for the local dashboard.\n"
            "  Run: [dim]pip install 'scanllm\\[server]'[/dim]"
        )
        raise typer.Exit(code=1)

    url = f"http://{host}:{port}"

    console.print(f"\n[bold cyan]ScanLLM Dashboard[/bold cyan]")
    console.print(f"  Running at [bold]{url}[/bold]")
    console.print(f"  Serving data from: {repo_path}")
    console.print(f"  Press [bold]Ctrl+C[/bold] to stop\n")

    # Set the repo path for the server to use
    import os
    os.environ["SCANLLM_REPO_PATH"] = str(repo_path)

    if not no_open:
        # Open browser after a short delay (server needs to start)
        import threading

        def _open_browser() -> None:
            import time
            time.sleep(1.5)
            webbrowser.open(url)

        threading.Thread(target=_open_browser, daemon=True).start()

    try:
        uvicorn.run(
            "cli.server.app:app",
            host=host,
            port=port,
            log_level="warning",
        )
    except KeyboardInterrupt:
        console.print("\n[dim]Dashboard stopped.[/dim]")
