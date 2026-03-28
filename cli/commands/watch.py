"""scanllm watch — Watch mode for continuous scanning."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.live import Live
from rich.panel import Panel

console = Console()

# File extensions to watch
WATCHED_EXTENSIONS: set[str] = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".ipynb",
    ".yaml", ".yml", ".json", ".toml", ".env",
}


def watch_cmd(
    path: str = typer.Argument(".", help="Path to watch (default: current directory)"),
    debounce: float = typer.Option(2.0, "--debounce", "-d", help="Seconds to wait after changes before re-scanning"),
    severity: str = typer.Option(None, "--severity", "-s", help="Minimum severity filter"),
    full_scan: bool = typer.Option(False, "--full-scan", "-f", help="Include test/docs/example directories"),
) -> None:
    """Watch for file changes and re-scan automatically."""
    watch_path = Path(path).resolve()
    if not watch_path.is_dir():
        console.print(f"[bold red]Error:[/bold red] Path is not a directory: {watch_path}")
        raise typer.Exit(code=1)

    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler, FileSystemEvent
    except ImportError:
        console.print(
            "[bold red]Error:[/bold red] watchdog is required for watch mode.\n"
            "  Run: [dim]pip install watchdog[/dim]"
        )
        raise typer.Exit(code=1)

    # Load core
    try:
        from core.scanner.engine import ScanEngine
        from core.graph.builder import GraphBuilder
        from core.graph.analyzer import GraphAnalyzer
        from core.scoring.risk_engine import RiskEngine
        from core.scoring.owasp_mapper import OwaspMapper
    except ImportError as exc:
        console.print(
            f"[bold red]Error:[/bold red] Could not import core scanning engine.\n"
            f"  Detail: {exc}"
        )
        raise typer.Exit(code=1)

    console.print(f"\n[bold cyan]ScanLLM Watch Mode[/bold cyan]")
    console.print(f"  Watching: {watch_path}")
    console.print(f"  Debounce: {debounce}s")
    console.print(f"  Press [bold]Ctrl+C[/bold] to stop\n")

    # Run initial scan
    _run_watch_scan(
        watch_path, full_scan, severity,
        ScanEngine, GraphBuilder, GraphAnalyzer, RiskEngine, OwaspMapper,
    )

    last_change_time: float = 0.0
    pending_rescan: bool = False

    class ChangeHandler(FileSystemEventHandler):
        def on_any_event(self, event: FileSystemEvent) -> None:
            nonlocal last_change_time, pending_rescan
            if event.is_directory:
                return
            src = event.src_path
            if any(src.endswith(ext) for ext in WATCHED_EXTENSIONS):
                last_change_time = time.monotonic()
                pending_rescan = True

    observer = Observer()
    observer.schedule(ChangeHandler(), str(watch_path), recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(0.5)
            if pending_rescan and (time.monotonic() - last_change_time) >= debounce:
                pending_rescan = False
                console.print(f"\n[yellow]Changes detected — re-scanning...[/yellow]")
                _run_watch_scan(
                    watch_path, full_scan, severity,
                    ScanEngine, GraphBuilder, GraphAnalyzer, RiskEngine, OwaspMapper,
                )
    except KeyboardInterrupt:
        observer.stop()
        console.print("\n[dim]Watch mode stopped.[/dim]")
    observer.join()


def _run_watch_scan(
    scan_path: Path,
    full_scan: bool,
    severity_filter: str | None,
    ScanEngine: type,
    GraphBuilder: type,
    GraphAnalyzer: type,
    RiskEngine: type,
    OwaspMapper: type,
) -> None:
    """Execute a scan and display results inline."""
    from cli.output.table import print_summary_panel, print_findings_table

    start = time.monotonic()

    try:
        engine = ScanEngine()
        scan_result = engine.scan(scan_path, full_scan=full_scan)
        findings = scan_result.get("findings", [])

        builder = GraphBuilder()
        graph = builder.build(findings)

        analyzer = GraphAnalyzer()
        graph_analysis = analyzer.analyze(graph)

        risk_engine = RiskEngine()
        risk_result = risk_engine.score(findings, graph_analysis)

        owasp_mapper = OwaspMapper()
        owasp_result = owasp_mapper.map_findings(findings)

        elapsed = time.monotonic() - start
        summary = scan_result.get("summary", {})

        now = datetime.now(timezone.utc).strftime("%H:%M:%S")
        console.print(f"\n  [dim]{now} | Scanned in {elapsed:.1f}s[/dim]")
        print_summary_panel(summary, risk_result, owasp_result)

        if severity_filter:
            print_findings_table(findings, severity_filter)
        elif findings:
            # In watch mode, only show high+ by default to keep output compact
            print_findings_table(findings, "high")

    except Exception as exc:
        console.print(f"[red]Scan error:[/red] {exc}")
