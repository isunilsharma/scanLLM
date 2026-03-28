"""scanllm fix — Show auto-remediation suggestions for scan findings."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel

from cli.config import ScanLLMConfig

console = Console()

_REMEDIATIONS: dict[str, dict[str, str]] = {
    "LLM01": {
        "title": "Prompt Injection",
        "fix": "Use parameterized prompts or template engines instead of f-strings/format().\n"
               "  Separate user input from system instructions with clear boundaries.",
    },
    "LLM02": {
        "title": "Sensitive Information Disclosure",
        "fix": "Remove credentials and PII from system prompts.\n"
               "  Use environment variables: os.environ['API_KEY']",
    },
    "LLM03": {
        "title": "Supply Chain Vulnerabilities",
        "fix": "Pin package versions in requirements.txt. Run 'pip audit' for CVEs.",
    },
    "LLM05": {
        "title": "Improper Output Handling",
        "fix": "Never pass LLM output to eval(), exec(), or subprocess.\n"
               "  Use json.loads() or ast.literal_eval() for safe parsing.",
    },
    "LLM06": {
        "title": "Excessive Agency",
        "fix": "Apply least-privilege to agent tools. Add human-in-the-loop.\n"
               "  Example: tools=[read_only_tool] instead of tools=[all_tools]",
    },
    "LLM07": {
        "title": "System Prompt Leakage",
        "fix": "Move secrets to environment variables or a secrets manager.",
    },
    "LLM08": {
        "title": "Vector/Embedding Weaknesses",
        "fix": "Authenticate vector DB connections. Use API keys or TLS.",
    },
    "LLM10": {
        "title": "Unbounded Consumption",
        "fix": "Set max_tokens on all LLM calls. Add rate limiting and timeouts.",
    },
}

_CATEGORY_FIXES: dict[str, str] = {
    "secret": "Move this key to an environment variable. Add the file to .gitignore.",
    "missing_max_tokens": "Add max_tokens parameter to this LLM call.",
    "prompt_injection": "Use a template engine instead of string concatenation with user input.",
    "eval_llm_output": "Replace eval() with json.loads() or ast.literal_eval().",
    "exec_llm_output": "Never exec() LLM output. Use structured outputs with validation.",
    "excessive_agency": "Reduce the tool list to minimum required permissions.",
    "broad_tool_access": "Apply least-privilege: only grant tools the agent needs.",
}


def fix(
    path: str = typer.Argument(".", help="Path to the scanned repo"),
    severity: str = typer.Option(None, "--severity", "-s", help="Filter by minimum severity"),
) -> None:
    """Show auto-remediation suggestions for the latest scan findings."""
    config = ScanLLMConfig(Path(path).resolve())
    latest = config.get_latest_scan()

    if not latest:
        console.print(
            "[yellow]No scan results found.[/yellow]\n"
            "  Run [cyan]scanllm scan --save[/cyan] first."
        )
        raise typer.Exit(code=1)

    findings = latest.get("findings", [])
    if not findings:
        console.print("[green]No findings to fix.[/green]")
        return

    sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    if severity:
        min_order = sev_order.get(severity.lower(), 4)
        findings = [f for f in findings if sev_order.get((f.get("severity") or "info").lower(), 4) <= min_order]

    findings.sort(key=lambda f: sev_order.get((f.get("severity") or "info").lower(), 4))

    shown = 0
    for finding in findings:
        owasp_id = finding.get("owasp_id", "")
        category = finding.get("pattern_category", "")
        sev = (finding.get("severity") or "info").lower()
        file_path = finding.get("file_path", "<unknown>")
        line = finding.get("line_number", "?")
        name = finding.get("pattern_name", finding.get("message", ""))

        remediation = None
        if owasp_id and owasp_id in _REMEDIATIONS:
            remediation = _REMEDIATIONS[owasp_id]["fix"]
        elif category in _CATEGORY_FIXES:
            remediation = _CATEGORY_FIXES[category]

        if not remediation:
            continue

        sev_styles = {"critical": "red", "high": "red", "medium": "yellow", "low": "cyan", "info": "dim"}
        sev_style = sev_styles.get(sev, "dim")

        console.print(Panel(
            f"  [bold]{name}[/bold]\n"
            f"  [cyan]{file_path}:{line}[/cyan]  [{sev_style}]{sev}[/{sev_style}]"
            f"{'  [yellow]' + owasp_id + '[/yellow]' if owasp_id else ''}\n\n"
            f"  [bold green]Fix:[/bold green] {remediation}",
            border_style=sev_style,
            padding=(0, 1),
        ))
        shown += 1
        if shown >= 20:
            remaining = len(findings) - shown
            if remaining > 0:
                console.print(f"  [dim]... and {remaining} more. Use --severity to filter.[/dim]")
            break

    if shown == 0:
        console.print("[green]No actionable findings to fix.[/green]")
