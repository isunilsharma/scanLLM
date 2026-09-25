"""scanllm agent-scan — Discover and scan MCP configs and agent skills."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

from core.scanner._finding import SEVERITY_LEVELS, count_severities

console = Console(stderr=True)
stdout_console = Console()

BANNER = r"""[bold cyan]
  ███████╗ ██████╗ █████╗ ███╗   ██╗██╗     ██╗     ███╗   ███╗
  ██╔════╝██╔════╝██╔══██╗████╗  ██║██║     ██║     ████╗ ████║
  ███████╗██║     ███████║██╔██╗ ██║██║     ██║     ██╔████╔██║
  ╚════██║██║     ██╔══██║██║╚██╗██║██║     ██║     ██║╚██╔╝██║
  ███████║╚██████╗██║  ██║██║ ╚████║███████╗███████╗██║ ╚═╝ ██║
  ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝╚═╝     ╚═╝
[/bold cyan]
  [dim]Agent Security Scanner[/dim]
"""

# ── Severity styling ──────────────────────────────────────────────────────

_SEVERITY_STYLES: dict[str, str] = {
    "critical": "bold red",
    "high": "red",
    "medium": "yellow",
    "low": "cyan",
    "info": "dim",
}

_SEVERITY_ORDER: dict[str, int] = {
    level: index for index, level in enumerate(SEVERITY_LEVELS)
}


def _severity_text(severity: str) -> Text:
    sev = severity.lower()
    style = _SEVERITY_STYLES.get(sev, "dim")
    return Text(sev, style=style)


# ── Remediation hints by risk ID ──────────────────────────────────────────

_RISK_HINTS: dict[str, str] = {
    "MCP-001": "Remove instruction language from descriptions",
    "MCP-002": "Rename tool to match actual behavior",
    "MCP-003": "Use namespaced tool names",
    "MCP-004": "Remove unnecessary servers",
    "MCP-005": "Apply least-privilege to server args",
    "MCP-006": "Audit package source",
    "MCP-007": "Use SSE with TLS",
    "SKILL-001": "Remove override language",
    "SKILL-002": "Remove dynamic code execution",
    "SKILL-003": "Use env vars for credentials",
    "SKILL-004": "Move secrets to env vars",
    "SKILL-005": "Validate remote URLs",
    "SKILL-006": "Restrict file/network access",
    "SKILL-007": "Remove privilege escalation",
    "SKILL-008": "Don't modify other tool configs",
}


# ── Lazy imports ──────────────────────────────────────────────────────────

def _load_mcp_scanner():
    try:
        from core.scanner.mcp_scanner import MCPScanner
        return MCPScanner
    except ImportError as exc:
        console.print(
            f"[bold red]Error:[/bold red] Could not import MCP scanner.\n"
            f"  Detail: {exc}\n"
            f"  Make sure the [cyan]core[/cyan] package is installed.\n"
            f"  Run: [dim]pip install -e .[/dim]"
        )
        raise typer.Exit(code=1)


def _load_skill_scanner():
    try:
        from core.scanner.skill_scanner import SkillScanner
        return SkillScanner
    except ImportError as exc:
        console.print(
            f"[bold red]Error:[/bold red] Could not import skill scanner.\n"
            f"  Detail: {exc}\n"
            f"  Make sure the [cyan]core[/cyan] package is installed.\n"
            f"  Run: [dim]pip install -e .[/dim]"
        )
        raise typer.Exit(code=1)


# ── Main command ──────────────────────────────────────────────────────────

def agent_scan(
    path: str = typer.Argument(".", help="Project directory to scan for project-level MCP configs"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table, json, sarif"),
    platform: str = typer.Option(None, "--platform", "-p", help="Scan specific platform only: cursor, claude_desktop, vscode, windsurf, gemini"),
    skills: bool = typer.Option(False, "--skills", help="Also scan installed agent skill files in the project"),
    skills_dir: str = typer.Option(None, "--skills-dir", help="Directory containing agent skill files to scan"),
    severity: str = typer.Option(None, "--severity", "-s", help="Minimum severity filter: critical, high, medium, low"),
    no_banner: bool = typer.Option(False, "--no-banner", help="Skip the ASCII banner"),
) -> None:
    """Discover and scan MCP server configurations and agent skills for security risks.

    Auto-discovers MCP configs across platforms (Cursor, Claude Desktop, VS Code,
    Windsurf, Gemini CLI) and checks for prompt injection, tool poisoning, toxic flows,
    overprivileged servers, and more.
    """
    project_path = Path(path).resolve()
    if not project_path.exists():
        console.print(f"[bold red]Error:[/bold red] Path not found: {project_path}")
        raise typer.Exit(code=1)

    # Show banner
    if not no_banner and output == "table":
        console.print(BANNER)

    MCPScanner = _load_mcp_scanner()
    start_time = time.monotonic()

    all_findings: list[dict[str, Any]] = []
    mcp_result: dict[str, Any] = {}

    # ── MCP config scan ───────────────────────────────────────────────
    if output == "table":
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("[cyan]Discovering MCP configurations...", total=None)

            scanner = MCPScanner()
            mcp_result = scanner.scan(
                project_dir=project_path if project_path.is_dir() else None,
                platform_filter=platform,
            )
            all_findings.extend(mcp_result.get("findings", []))

            progress.update(task, description="[green]MCP scan complete!")
    else:
        scanner = MCPScanner()
        mcp_result = scanner.scan(
            project_dir=project_path if project_path.is_dir() else None,
            platform_filter=platform,
        )
        all_findings.extend(mcp_result.get("findings", []))

    # ── Skill scan ────────────────────────────────────────────────────
    skill_findings: list[dict[str, Any]] = []
    if skills or skills_dir:
        SkillScanner = _load_skill_scanner()
        skill_scanner = SkillScanner()

        scan_dir = Path(skills_dir) if skills_dir else project_path
        if not scan_dir.is_dir():
            console.print(f"[bold red]Error:[/bold red] Skills directory not found: {scan_dir}")
            raise typer.Exit(code=1)

        if output == "table":
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True,
            ) as progress:
                task = progress.add_task("[cyan]Scanning agent skills...", total=None)
                skill_findings = skill_scanner.scan_directory(scan_dir)
                all_findings.extend(skill_findings)
                progress.update(task, description="[green]Skill scan complete!")
        else:
            skill_findings = skill_scanner.scan_directory(scan_dir)
            all_findings.extend(skill_findings)

    elapsed = time.monotonic() - start_time

    # ── Apply severity filter ─────────────────────────────────────────
    if severity:
        min_order = _SEVERITY_ORDER.get(severity.lower(), 4)
        all_findings = [
            f for f in all_findings
            if _SEVERITY_ORDER.get(
                (f.get("pattern_severity") or "info").lower(), 4
            ) <= min_order
        ]

    # ── Output ────────────────────────────────────────────────────────
    if output == "table":
        _output_table(mcp_result, all_findings, skill_findings, elapsed)
    elif output == "json":
        _output_json(mcp_result, all_findings, skill_findings)
    elif output == "sarif":
        _output_sarif(all_findings, project_path)
    else:
        console.print(f"[bold red]Error:[/bold red] Unknown output format: {output}")
        console.print("  Supported formats: table, json, sarif")
        raise typer.Exit(code=1)


# ── Table output ──────────────────────────────────────────────────────────

def _output_table(
    mcp_result: dict[str, Any],
    all_findings: list[dict[str, Any]],
    skill_findings: list[dict[str, Any]],
    elapsed: float,
) -> None:
    """Render agent scan results as Rich tables."""
    summary = mcp_result.get("summary", {})
    configs = mcp_result.get("configs", [])

    # ── Summary panel ─────────────────────────────────────────────────
    lines: list[str] = []

    configs_count = summary.get("configs_discovered", 0)
    servers_count = summary.get("total_servers", 0)
    platforms = summary.get("platforms", {})
    platform_str = ", ".join(f"{k} ({v})" for k, v in platforms.items()) if platforms else "none"

    lines.append(f"  [bold]MCP Configs:[/bold] {configs_count} discovered ({servers_count} servers)")
    lines.append(f"  [bold]Platforms:[/bold] {platform_str}")

    if skill_findings:
        lines.append(f"  [bold]Skill Files:[/bold] {len(skill_findings)} issues found")

    total_findings = len(all_findings)
    severities: dict[str, int] = count_severities(all_findings)

    parts = [
        f"[{_SEVERITY_STYLES.get(sev, 'dim')}]{count} {sev}[/{_SEVERITY_STYLES.get(sev, 'dim')}]"
        for sev, count in severities.items()
        if count > 0
    ]
    if parts:
        lines.append(f"  [bold]Findings:[/bold] {' | '.join(parts)}")
    else:
        lines.append("  [bold]Findings:[/bold] None")

    console.print(Panel(
        "\n".join(lines),
        title="[bold cyan]Agent Security Scan[/bold cyan]",
        border_style="cyan",
        padding=(1, 2),
    ))

    # ── Configs discovered ────────────────────────────────────────────
    if configs:
        config_table = Table(
            title="MCP Configurations Discovered",
            show_header=True,
            header_style="bold",
            border_style="dim",
            padding=(0, 1),
        )
        config_table.add_column("Platform", style="magenta", max_width=15)
        config_table.add_column("Path", style="cyan", max_width=50)
        config_table.add_column("Servers", max_width=8, justify="right")
        config_table.add_column("Status", max_width=12)

        for cfg in configs:
            path = cfg.get("path", "")
            if len(path) > 50:
                path = "..." + path[-47:]
            error = cfg.get("parse_error")
            server_count = len(cfg.get("servers", []))
            status = Text("OK", style="green") if not error else Text("Error", style="red")
            config_table.add_row(
                cfg.get("platform", ""),
                path,
                str(server_count),
                status,
            )

        console.print()
        console.print(config_table)

    # ── Findings table ────────────────────────────────────────────────
    if all_findings:
        # Sort by severity
        sorted_findings = sorted(
            all_findings,
            key=lambda f: _SEVERITY_ORDER.get(
                (f.get("pattern_severity") or "info").lower(), 4
            ),
        )

        findings_table = Table(
            title=f"Agent Security Findings ({total_findings} total)",
            show_header=True,
            header_style="bold",
            border_style="dim",
            padding=(0, 1),
        )
        findings_table.add_column("Risk", style="cyan", max_width=10)
        findings_table.add_column("Severity", max_width=10)
        findings_table.add_column("Server/File", style="magenta", max_width=20)
        findings_table.add_column("Description", max_width=55)
        findings_table.add_column("Fix", style="dim", max_width=25)

        for f in sorted_findings:
            risk_id = f.get("risk_id", f.get("pattern_name", ""))
            sev = (f.get("pattern_severity") or "info").lower()
            server = f.get("provider", "") or _truncate_path(f.get("file_path", ""), 20)
            desc = f.get("pattern_description", "")
            if len(desc) > 55:
                desc = desc[:52] + "..."
            hint = _RISK_HINTS.get(risk_id, "")

            findings_table.add_row(
                risk_id,
                _severity_text(sev),
                server,
                desc,
                hint,
            )

        console.print()
        console.print(findings_table)
    else:
        console.print()
        console.print(Panel(
            "  [bold green]No agent security issues found.[/bold green]\n\n"
            "  Your MCP configurations and agent skills look clean.",
            title="[bold cyan]Results[/bold cyan]",
            border_style="green",
            padding=(1, 2),
        ))

    # ── Footer ────────────────────────────────────────────────────────
    console.print()
    console.print(
        f"  [dim]Scanned in {elapsed:.1f}s | "
        f"{summary.get('configs_discovered', 0)} configs | "
        f"{summary.get('total_servers', 0)} servers | "
        f"{total_findings} findings[/dim]"
    )
    if not skill_findings and total_findings >= 0:
        console.print("  [dim]Tip: Run [bold]scanllm agent-scan --skills[/bold] to also scan agent skill source files[/dim]")
    console.print()


# ── JSON output ───────────────────────────────────────────────────────────

def _output_json(
    mcp_result: dict[str, Any],
    all_findings: list[dict[str, Any]],
    skill_findings: list[dict[str, Any]],
) -> None:
    """Output results as JSON to stdout."""
    output: dict[str, Any] = {
        "version": "2.3.1",
        "scan_type": "agent_security",
        "configs": mcp_result.get("configs", []),
        "findings": all_findings,
        "summary": mcp_result.get("summary", {}),
    }
    if skill_findings:
        output["summary"]["skill_findings_count"] = len(skill_findings)

    sys.stdout.write(json.dumps(output, indent=2, default=str) + "\n")


# ── SARIF output ──────────────────────────────────────────────────────────

def _output_sarif(
    findings: list[dict[str, Any]],
    scan_path: Path,
) -> None:
    """Output results as SARIF 2.1.0."""
    from cli.output.sarif import to_sarif
    sarif = to_sarif(findings, scan_path)
    sys.stdout.write(json.dumps(sarif, indent=2, default=str) + "\n")


# ── Helpers ───────────────────────────────────────────────────────────────

def _truncate_path(path: str, max_len: int = 35) -> str:
    if len(path) > max_len:
        return "..." + path[-(max_len - 3):]
    return path
