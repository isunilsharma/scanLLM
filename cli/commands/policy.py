"""scanllm policy [init|check|list] — Policy management commands."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table
from rich.text import Text

from cli.config import ScanLLMConfig

console = Console()

policy_app = typer.Typer(help="Policy management commands.")


@policy_app.command(name="init")
def policy_init(
    path: str = typer.Argument(".", help="Repository path"),
) -> None:
    """Create default policies.yaml in .scanllm/ directory."""
    repo_path = Path(path).resolve()
    config = ScanLLMConfig(repo_path)

    if not config.is_initialized():
        console.print(
            "[yellow]Warning:[/yellow] .scanllm/ not found. Initializing first..."
        )
        config.initialize()
    else:
        # Write or overwrite policies.yaml with defaults
        policies_path = config.scanllm_dir / "policies.yaml"
        try:
            from core.policy.defaults import DEFAULT_POLICIES_YAML
            policies_path.write_text(DEFAULT_POLICIES_YAML, encoding="utf-8")
        except ImportError:
            import yaml
            policies_path.write_text(
                yaml.dump({"policies": []}, default_flow_style=False),
                encoding="utf-8",
            )

    console.print("[bold green]Policy file created:[/bold green] .scanllm/policies.yaml")
    console.print("  Edit this file to customize policies for your team.")
    console.print("  Run [bold]scanllm policy list[/bold] to see all rules.\n")


@policy_app.command(name="check")
def policy_check(
    path: str = typer.Argument(".", help="Repository path"),
    policy_file: str = typer.Option(None, "--policy", "-p", help="Path to policy file (default: .scanllm/policies.yaml)"),
) -> None:
    """Evaluate policies against the latest scan. Exits with code 1 on failure (for CI)."""
    repo_path = Path(path).resolve()
    config = ScanLLMConfig(repo_path)

    # Load latest scan
    latest = config.get_latest_scan()
    if latest is None:
        console.print(
            "[bold red]Error:[/bold red] No saved scans found.\n"
            "  Run [bold]scanllm scan --save[/bold] first."
        )
        raise typer.Exit(code=1)

    # Determine policy file
    if policy_file:
        p_path = Path(policy_file).resolve()
    else:
        p_path_opt = config.get_policies_path()
        if p_path_opt is None:
            console.print(
                "[bold red]Error:[/bold red] No policies.yaml found.\n"
                "  Run [bold]scanllm policy init[/bold] to create one."
            )
            raise typer.Exit(code=1)
        p_path = p_path_opt

    if not p_path.exists():
        console.print(f"[bold red]Error:[/bold red] Policy file not found: {p_path}")
        raise typer.Exit(code=1)

    # Load policy engine
    try:
        from core.policy.engine import PolicyEngine
    except ImportError:
        console.print(
            "[bold red]Error:[/bold red] Could not import core policy engine.\n"
            "  Make sure the [cyan]core[/cyan] package is installed."
        )
        raise typer.Exit(code=1)

    engine = PolicyEngine(policies_path=str(p_path))
    findings = latest.get("findings", [])
    scan_summary = dict(latest.get("summary", {}))
    risk_score = latest.get("risk_score")
    if risk_score is not None:
        scan_summary["risk_score"] = risk_score

    result = engine.evaluate(findings, scan_summary)

    # Display using table formatter
    from cli.output.table import print_policy_result as _print_policy

    # Build display dict
    rule_violations: dict[str, list[dict[str, Any]]] = {}
    for v in result.violations:
        if v.rule_name not in rule_violations:
            rule_violations[v.rule_name] = []
        rule_violations[v.rule_name].append(v.to_dict())

    policy_out: dict[str, Any] = {
        "passed": result.is_passing,
        "errors": result.error_count,
        "warnings": result.warning_count,
        "passes": len(result.passed_rules),
        "results": [],
    }

    for rule_name, violations in rule_violations.items():
        first_v = violations[0]
        policy_out["results"].append({
            "name": rule_name,
            "passed": False,
            "severity": first_v.get("severity", "warning"),
            "violation_count": len(violations),
            "violations": violations,
        })

    for rule_name in result.passed_rules:
        policy_out["results"].append({
            "name": rule_name,
            "passed": True,
            "severity": "info",
            "violation_count": 0,
            "violations": [],
        })

    _print_policy(policy_out)

    if not result.is_passing:
        raise typer.Exit(code=1)


@policy_app.command(name="list")
def policy_list(
    path: str = typer.Argument(".", help="Repository path"),
    policy_file: str = typer.Option(None, "--policy", "-p", help="Path to policy file"),
) -> None:
    """Show all configured policy rules."""
    repo_path = Path(path).resolve()
    config = ScanLLMConfig(repo_path)

    # Determine policy file
    if policy_file:
        p_path = Path(policy_file).resolve()
    else:
        p_path_opt = config.get_policies_path()
        if p_path_opt is None:
            console.print(
                "[yellow]No policies.yaml found.[/yellow]\n"
                "  Run [bold]scanllm policy init[/bold] to create one."
            )
            return
        p_path = p_path_opt

    if not p_path.exists():
        console.print(f"[bold red]Error:[/bold red] Policy file not found: {p_path}")
        raise typer.Exit(code=1)

    try:
        from core.policy.engine import PolicyEngine
    except ImportError:
        console.print(
            "[bold red]Error:[/bold red] Could not import core policy engine.\n"
            "  Make sure the [cyan]core[/cyan] package is installed."
        )
        raise typer.Exit(code=1)

    engine = PolicyEngine(policies_path=str(p_path))

    if not engine.rules:
        console.print("[dim]No policy rules configured.[/dim]")
        return

    table = Table(
        title=f"Policy Rules ({len(engine.rules)} total)",
        show_header=True,
        header_style="bold",
        border_style="dim",
    )
    table.add_column("Name", style="cyan", max_width=30)
    table.add_column("Description", max_width=50)
    table.add_column("Severity", max_width=10)
    table.add_column("Type", max_width=15, style="dim")
    table.add_column("Conditions", max_width=6, justify="right")

    severity_styles = {
        "error": "bold red",
        "warning": "yellow",
        "info": "dim",
    }

    for rule in engine.rules:
        sev_style = severity_styles.get(rule.severity, "dim")
        table.add_row(
            rule.name,
            rule.description,
            Text(rule.severity, style=sev_style),
            rule.type,
            str(len(rule.conditions)),
        )

    console.print()
    console.print(table)
    console.print(f"\n  [dim]Source: {p_path}[/dim]\n")
