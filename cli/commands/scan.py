"""scanllm scan [path] — Core scan command."""

from __future__ import annotations

import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel

from cli.config import ScanLLMConfig

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
  [dim]AI Dependency Intelligence[/dim] [bold white]v2.0.0[/bold white]
"""


def _load_core() -> tuple[Any, Any, Any, Any, Any, Any]:
    """Import core modules with a helpful error if missing."""
    try:
        from core.scanner.engine import ScanEngine
        from core.graph.builder import GraphBuilder
        from core.graph.analyzer import GraphAnalyzer
        from core.graph.serializer import GraphSerializer
        from core.scoring.risk_engine import RiskEngine
        from core.scoring.owasp_mapper import OwaspMapper
        return ScanEngine, GraphBuilder, GraphAnalyzer, GraphSerializer, RiskEngine, OwaspMapper
    except ImportError as exc:
        console.print(
            f"[bold red]Error:[/bold red] Could not import core scanning engine.\n"
            f"  Detail: {exc}\n"
            f"  Make sure the [cyan]core[/cyan] package is installed or in your PYTHONPATH.\n"
            f"  Run: [dim]pip install -e .[/dim]"
        )
        raise typer.Exit(code=1)


def _load_policy_engine() -> Any:
    """Import the policy engine."""
    try:
        from core.policy.engine import PolicyEngine
        return PolicyEngine
    except ImportError:
        return None


def scan(
    path: str = typer.Argument(".", help="Path to scan (default: current directory)"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table, json, sarif, cyclonedx"),
    severity: str = typer.Option(None, "--severity", "-s", help="Minimum severity filter: critical, high, medium, low"),
    full_scan: bool = typer.Option(False, "--full-scan", "-f", help="Include test/docs/example directories"),
    save: bool = typer.Option(False, "--save", help="Save scan results to .scanllm/scans/"),
    policy: str = typer.Option(None, "--policy", "-p", help="Policy file to evaluate against"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Minimal output (just summary)"),
    no_banner: bool = typer.Option(False, "--no-banner", help="Skip the ASCII banner"),
) -> None:
    """Scan a codebase for AI/LLM dependencies, risks, and policy violations."""
    # Resolve path
    scan_path = Path(path).resolve()
    if not scan_path.exists():
        console.print(f"[bold red]Error:[/bold red] Path not found: {scan_path}")
        raise typer.Exit(code=1)
    if not scan_path.is_dir():
        console.print(f"[bold red]Error:[/bold red] Path is not a directory: {scan_path}")
        raise typer.Exit(code=1)

    # Show banner (only for table output, not piped formats)
    if not no_banner and output == "table" and not quiet:
        console.print(BANNER)

    # Load core modules
    ScanEngine, GraphBuilder, GraphAnalyzer, GraphSerializer, RiskEngine, OwaspMapper = _load_core()

    # Run the scan with progress indication
    scan_result: dict[str, Any] = {}
    risk_result: dict[str, Any] | None = None
    owasp_result: dict[str, Any] | None = None
    graph_data: dict[str, Any] | None = None
    policy_result: dict[str, Any] | None = None

    start_time = time.monotonic()

    if output == "table" and not quiet:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=30),
            TaskProgressColumn(),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("[cyan]Scanning repository...", total=100)

            # Step 1: Scan files
            progress.update(task, description="[cyan]Scanning files for AI components...")
            engine = ScanEngine()
            scan_result = engine.scan(scan_path, full_scan=full_scan)
            progress.update(task, completed=40)

            # Step 2: Build dependency graph
            progress.update(task, description="[cyan]Building dependency graph...")
            findings = scan_result.get("findings", [])
            builder = GraphBuilder()
            graph = builder.build(findings)
            serializer = GraphSerializer()
            graph_data = serializer.to_react_flow(graph)
            progress.update(task, completed=60)

            # Step 3: Analyze graph and score
            progress.update(task, description="[cyan]Analyzing risk and scoring...")
            analyzer = GraphAnalyzer()
            graph_analysis = analyzer.analyze(graph)
            risk_engine = RiskEngine()
            risk_result = risk_engine.score(findings, graph_analysis)
            progress.update(task, completed=80)

            # Step 4: Map OWASP
            progress.update(task, description="[cyan]Mapping OWASP LLM Top 10...")
            owasp_mapper = OwaspMapper()
            owasp_result = owasp_mapper.map_findings(findings)
            progress.update(task, completed=90)

            # Step 5: Policy check
            if policy:
                progress.update(task, description="[cyan]Evaluating policies...")
                policy_result = _run_policy_check(policy, findings, scan_result, risk_result)
            elif ScanLLMConfig(scan_path).get_policies_path():
                progress.update(task, description="[cyan]Evaluating policies...")
                policies_path = str(ScanLLMConfig(scan_path).get_policies_path())
                policy_result = _run_policy_check(policies_path, findings, scan_result, risk_result)

            progress.update(task, completed=100, description="[green]Scan complete!")
    else:
        # Quiet / non-table mode: no progress bar
        engine = ScanEngine()
        scan_result = engine.scan(scan_path, full_scan=full_scan)
        findings = scan_result.get("findings", [])

        builder = GraphBuilder()
        graph = builder.build(findings)
        serializer = GraphSerializer()
        graph_data = serializer.to_react_flow(graph)

        analyzer = GraphAnalyzer()
        graph_analysis = analyzer.analyze(graph)
        risk_engine = RiskEngine()
        risk_result = risk_engine.score(findings, graph_analysis)

        owasp_mapper = OwaspMapper()
        owasp_result = owasp_mapper.map_findings(findings)

        if policy:
            policy_result = _run_policy_check(policy, findings, scan_result, risk_result)
        elif ScanLLMConfig(scan_path).get_policies_path():
            policies_path = str(ScanLLMConfig(scan_path).get_policies_path())
            policy_result = _run_policy_check(policies_path, findings, scan_result, risk_result)

    elapsed = time.monotonic() - start_time

    # Record telemetry (fire-and-forget)
    try:
        from cli.telemetry import record_event
        providers_list = list((scan_result.get("summary", {}).get("providers", {})).keys())
        config_obj = ScanLLMConfig(scan_path)
        record_event(
            event_type="scan",
            command="scan",
            scan_duration_ms=int(elapsed * 1000),
            finding_count=len(scan_result.get("findings", [])),
            risk_score=risk_result.get("overall_score") if risk_result else None,
            providers=providers_list or None,
            config_dir=config_obj.base_dir if config_obj.is_initialized() else None,
        )
    except Exception:
        pass

    # Add metadata to scan result for saving
    scan_result["risk_score"] = risk_result.get("overall_score") if risk_result else None
    scan_result["timestamp"] = datetime.now(timezone.utc).isoformat()
    scan_result["path"] = str(scan_path)
    scan_result["risk"] = risk_result
    scan_result["owasp"] = owasp_result
    if graph_data:
        scan_result["graph"] = graph_data

    # Save scan if requested
    if save:
        config = ScanLLMConfig(scan_path)
        if not config.is_initialized():
            config.initialize()
        saved_path = config.save_scan(scan_result)
        if output == "table":
            console.print(f"  [dim]Scan saved to {saved_path}[/dim]\n")

    # Output results
    if output == "table":
        _output_table(scan_result, risk_result, owasp_result, policy_result, severity, quiet, elapsed)
    elif output == "json":
        from cli.output.json_out import print_json
        print_json(scan_result, risk_result, owasp_result, policy_result, graph_data)
    elif output == "sarif":
        from cli.output.sarif import print_sarif
        print_sarif(scan_result.get("findings", []), scan_path)
    elif output == "cyclonedx":
        _output_cyclonedx(scan_result)
    else:
        console.print(f"[bold red]Error:[/bold red] Unknown output format: {output}")
        console.print("  Supported formats: table, json, sarif, cyclonedx")
        raise typer.Exit(code=1)

    # Exit with non-zero code if policy failed
    if policy_result and not policy_result.get("passed", True):
        raise typer.Exit(code=1)


def _run_policy_check(
    policy_path: str,
    findings: list[dict[str, Any]],
    scan_result: dict[str, Any],
    risk_result: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Run policy evaluation and return serialized result."""
    PolicyEngine = _load_policy_engine()
    if PolicyEngine is None:
        console.print("[yellow]Warning:[/yellow] Policy engine not available.")
        return None

    try:
        engine = PolicyEngine(policies_path=policy_path)
        scan_summary = dict(scan_result.get("summary", {}))
        if risk_result:
            scan_summary["risk_score"] = risk_result.get("overall_score", 0)
        result = engine.evaluate(findings, scan_summary)

        # Serialize to dict for display
        result_dict = result.to_dict()

        # Build a format compatible with table.print_policy_result
        errors = result.error_count
        warnings = result.warning_count
        passes = len(result.passed_rules)

        policy_out: dict[str, Any] = {
            "passed": result.is_passing,
            "errors": errors,
            "warnings": warnings,
            "passes": passes,
            "results": [],
        }

        # Group violations by rule name
        rule_violations: dict[str, list[dict[str, Any]]] = {}
        for v in result.violations:
            if v.rule_name not in rule_violations:
                rule_violations[v.rule_name] = []
            rule_violations[v.rule_name].append(v.to_dict())

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

        return policy_out

    except Exception as exc:
        console.print(f"[yellow]Warning:[/yellow] Policy evaluation failed: {exc}")
        return None


def _output_table(
    scan_result: dict[str, Any],
    risk_result: dict[str, Any] | None,
    owasp_result: dict[str, Any] | None,
    policy_result: dict[str, Any] | None,
    severity_filter: str | None,
    quiet: bool,
    elapsed: float,
) -> None:
    """Render results as Rich tables."""
    from cli.output.table import print_summary_panel, print_findings_table, print_policy_result, print_action_summary

    summary = scan_result.get("summary", {})

    # Always print summary panel
    print_summary_panel(summary, risk_result, owasp_result)

    if not quiet:
        # Findings table
        findings = scan_result.get("findings", [])
        print_findings_table(findings, severity_filter)

        # Policy result
        if policy_result:
            print_policy_result(policy_result)

        # Action summary with prioritized fixes and next steps
        print_action_summary(findings, risk_result)

    # Footer
    total_findings = summary.get("total_findings", 0)
    console.print(
        f"  [dim]Scanned in {elapsed:.1f}s | "
        f"{summary.get('files_scanned', 0)} files | "
        f"{total_findings} findings[/dim]"
    )
    console.print("  [dim]Run [bold]scanllm ui[/bold] to explore the interactive dashboard[/dim]\n")


def _output_cyclonedx(scan_result: dict[str, Any]) -> None:
    """Output findings as CycloneDX AI-BOM JSON."""
    import json

    findings = scan_result.get("findings", [])
    summary = scan_result.get("summary", {})

    bom: dict[str, Any] = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "version": 1,
        "metadata": {
            "timestamp": scan_result.get("timestamp", ""),
            "tools": [{
                "vendor": "ScanLLM",
                "name": "scanllm",
                "version": "2.0.0",
            }],
        },
        "components": [],
        "dependencies": [],
    }

    seen_components: set[str] = set()
    for finding in findings:
        component_type = finding.get("component_type", "unknown")
        provider = finding.get("provider", "")
        name = finding.get("pattern_name", "")
        comp_key = f"{component_type}:{provider}:{name}"

        if comp_key in seen_components:
            continue
        seen_components.add(comp_key)

        component: dict[str, Any] = {
            "type": "machine-learning-model" if component_type in ("llm_provider", "embedding_service") else "library",
            "name": name or provider or component_type,
            "group": provider,
            "properties": [
                {"name": "scanllm:component_type", "value": component_type},
                {"name": "scanllm:provider", "value": provider},
            ],
        }

        model_name = finding.get("model_name", "")
        if model_name:
            component["properties"].append(
                {"name": "scanllm:model_name", "value": model_name}
            )

        bom["components"].append(component)

    sys.stdout.write(json.dumps(bom, indent=2, default=str) + "\n")
