"""scanllm fix — Show auto-remediation suggestions for scan findings."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel

from cli.config import ScanLLMConfig

console = Console()

_MODEL_UPGRADES: dict[str, str] = {
    "gpt-3.5-turbo": "gpt-4o-mini",
    "text-davinci-003": "gpt-4o-mini",
    "text-davinci-002": "gpt-4o-mini",
    "code-davinci-002": "gpt-4o-mini",
}

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


def _apply_fixes(findings: list[dict[str, Any]], repo_path: Path, skip_confirm: bool) -> int:
    """Apply auto-fixes to files."""
    applied = 0
    fixes_by_file: dict[str, list[dict[str, Any]]] = {}

    for f in findings:
        file_path = f.get("file_path", "")
        if not file_path:
            continue
        pattern = (f.get("pattern_name", "") or "").lower()
        category = (f.get("pattern_category", "") or "").lower()

        # Only fix certain categories
        if not any(
            k in pattern or k in category
            for k in ("deprecated_model", "missing_max_tokens")
        ):
            continue

        if file_path not in fixes_by_file:
            fixes_by_file[file_path] = []
        fixes_by_file[file_path].append(f)

    if not fixes_by_file:
        console.print("[dim]No auto-fixable issues found.[/dim]")
        return 0

    total_fixable = sum(len(v) for v in fixes_by_file.values())
    console.print(
        f"\n[bold]Found {total_fixable} auto-fixable issue(s) "
        f"in {len(fixes_by_file)} file(s):[/bold]\n"
    )

    for file_path, file_findings in fixes_by_file.items():
        full_path = (
            repo_path / file_path
            if not Path(file_path).is_absolute()
            else Path(file_path)
        )
        if not full_path.exists():
            continue

        content = full_path.read_text(encoding="utf-8")
        new_content = content
        changes: list[str] = []

        for f in file_findings:
            pattern = (f.get("pattern_name", "") or "").lower()
            category = (f.get("pattern_category", "") or "").lower()

            # Fix deprecated models
            if "deprecated" in pattern or "deprecated_model" in pattern:
                for old_model, new_model in _MODEL_UPGRADES.items():
                    if old_model in new_content:
                        new_content = new_content.replace(
                            f'"{old_model}"', f'"{new_model}"'
                        )
                        new_content = new_content.replace(
                            f"'{old_model}'", f"'{new_model}'"
                        )
                        changes.append(
                            f"  [yellow]~[/yellow] Replace {old_model} -> {new_model}"
                        )

            # Fix missing max_tokens
            if "missing_max_tokens" in pattern or "missing_max_tokens" in category:
                line_no = f.get("line_number")
                matched = f.get("matched_value", "") or f.get("matched_text", "")
                # Try to add max_tokens=4096 to LLM calls missing it
                # Look for common patterns: .create(...) calls without max_tokens
                for call_pattern in [
                    r"(\.create\()([^)]*)\)",
                    r"(\.generate\()([^)]*)\)",
                ]:
                    def _add_max_tokens(m: re.Match[str]) -> str:
                        opener = m.group(1)
                        args = m.group(2)
                        if "max_tokens" in args:
                            return m.group(0)
                        if args.strip():
                            return f"{opener}{args}, max_tokens=4096)"
                        return f"{opener}max_tokens=4096)"

                    updated = re.sub(call_pattern, _add_max_tokens, new_content)
                    if updated != new_content:
                        new_content = updated
                        changes.append(
                            f"  [yellow]~[/yellow] Add max_tokens=4096 to LLM call"
                        )
                        break

        if new_content != content:
            console.print(f"  [bold]{file_path}[/bold]")
            for change in changes:
                console.print(change)

            if not skip_confirm:
                confirm = typer.confirm(f"  Apply changes to {file_path}?")
                if not confirm:
                    continue

            full_path.write_text(new_content, encoding="utf-8")
            console.print(f"  [green]v[/green] Fixed {file_path}")
            applied += len(changes)

    return applied


def fix(
    path: str = typer.Argument(".", help="Path to the scanned repo"),
    severity: str = typer.Option(None, "--severity", "-s", help="Filter by minimum severity"),
    apply: bool = typer.Option(False, "--apply", help="Actually apply fixes to files"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
) -> None:
    """Show auto-remediation suggestions for the latest scan findings."""
    config = ScanLLMConfig(Path(path).resolve())
    repo_path = Path(path).resolve()
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

    # Apply mode — actually modify files
    if apply:
        applied = _apply_fixes(findings, repo_path, yes)
        console.print(f"\n[bold green]{applied} fix(es) applied.[/bold green]\n")
        return

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
