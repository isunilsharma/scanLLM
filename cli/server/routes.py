"""API routes for the ScanLLM local dashboard server."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, BackgroundTasks

router = APIRouter()


def _get_config() -> Any:
    """Get a ScanLLMConfig for the current repo path."""
    from cli.config import ScanLLMConfig

    repo_path = os.environ.get("SCANLLM_REPO_PATH", ".")
    return ScanLLMConfig(Path(repo_path).resolve())


@router.get("/scan/latest")
async def get_latest_scan() -> dict[str, Any]:
    """Return the latest saved scan result."""
    config = _get_config()
    latest = config.get_latest_scan()
    if latest is None:
        raise HTTPException(
            status_code=404,
            detail="No saved scans found. Run `scanllm scan --save` first.",
        )
    return latest


@router.get("/scan/history")
async def get_scan_history() -> list[dict[str, Any]]:
    """Return metadata for all saved scans."""
    config = _get_config()
    return config.get_scan_history()


@router.get("/graph")
async def get_graph() -> dict[str, Any]:
    """Return the dependency graph for the latest scan."""
    config = _get_config()
    latest = config.get_latest_scan()
    if latest is None:
        raise HTTPException(status_code=404, detail="No saved scans found.")

    graph = latest.get("graph")
    if graph:
        return graph

    # Build graph on the fly from findings
    findings = latest.get("findings", [])
    if not findings:
        return {"nodes": [], "edges": []}

    try:
        from core.graph.builder import GraphBuilder
        from core.graph.serializer import GraphSerializer

        builder = GraphBuilder()
        graph_nx = builder.build(findings)
        serializer = GraphSerializer()
        return serializer.to_react_flow(graph_nx)
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Core graph modules not available.",
        )


@router.get("/risk")
async def get_risk() -> dict[str, Any]:
    """Return risk scoring for the latest scan."""
    config = _get_config()
    latest = config.get_latest_scan()
    if latest is None:
        raise HTTPException(status_code=404, detail="No saved scans found.")

    # Return cached risk if available
    risk = latest.get("risk")
    if risk:
        return risk

    # Compute on the fly
    findings = latest.get("findings", [])
    try:
        from core.scoring.risk_engine import RiskEngine

        engine = RiskEngine()
        return engine.score(findings)
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Core scoring modules not available.",
        )


@router.get("/owasp")
async def get_owasp() -> dict[str, Any]:
    """Return OWASP LLM Top 10 mapping for the latest scan."""
    config = _get_config()
    latest = config.get_latest_scan()
    if latest is None:
        raise HTTPException(status_code=404, detail="No saved scans found.")

    owasp = latest.get("owasp")
    if owasp:
        return owasp

    findings = latest.get("findings", [])
    try:
        from core.scoring.owasp_mapper import OwaspMapper

        mapper = OwaspMapper()
        return mapper.map_findings(findings)
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Core OWASP mapper not available.",
        )


@router.get("/policy")
async def get_policy() -> dict[str, Any]:
    """Return policy evaluation for the latest scan."""
    config = _get_config()
    latest = config.get_latest_scan()
    if latest is None:
        raise HTTPException(status_code=404, detail="No saved scans found.")

    policies_path = config.get_policies_path()
    if policies_path is None:
        return {"message": "No policies configured. Run `scanllm policy init`."}

    findings = latest.get("findings", [])
    scan_summary = dict(latest.get("summary", {}))
    risk_score = latest.get("risk_score")
    if risk_score is not None:
        scan_summary["risk_score"] = risk_score

    try:
        from core.policy.engine import PolicyEngine

        engine = PolicyEngine(policies_path=str(policies_path))
        result = engine.evaluate(findings, scan_summary)
        return result.to_dict()
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Core policy engine not available.",
        )


@router.get("/diff")
async def get_diff() -> dict[str, Any]:
    """Return diff between latest and previous scan."""
    config = _get_config()
    latest = config.get_latest_scan()
    previous = config.get_previous_scan()

    if latest is None:
        raise HTTPException(status_code=404, detail="No saved scans found.")
    if previous is None:
        return {"has_changes": False, "message": "Only one scan available. No diff possible."}

    try:
        from core.diff.differ import ScanDiffer

        differ = ScanDiffer()
        diff_result = differ.diff(previous, latest)
        return diff_result.to_dict()
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Core diff module not available.",
        )


@router.post("/scan")
async def trigger_scan(background_tasks: BackgroundTasks) -> dict[str, str]:
    """Trigger a new scan in the background."""
    repo_path = os.environ.get("SCANLLM_REPO_PATH", ".")

    try:
        from core.scanner.engine import ScanEngine
        from core.graph.builder import GraphBuilder
        from core.graph.analyzer import GraphAnalyzer
        from core.graph.serializer import GraphSerializer
        from core.scoring.risk_engine import RiskEngine
        from core.scoring.owasp_mapper import OwaspMapper
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Core scanning modules not available.",
        )

    def _run_scan() -> None:
        from datetime import datetime, timezone

        config = _get_config()
        scan_path = Path(repo_path).resolve()

        engine = ScanEngine()
        scan_result = engine.scan(scan_path)
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

        scan_result["risk_score"] = risk_result.get("overall_score")
        scan_result["risk"] = risk_result
        scan_result["owasp"] = owasp_result
        scan_result["graph"] = graph_data
        scan_result["timestamp"] = datetime.now(timezone.utc).isoformat()
        scan_result["path"] = str(scan_path)

        if not config.is_initialized():
            config.initialize()
        config.save_scan(scan_result)

    background_tasks.add_task(_run_scan)
    return {"status": "scan_started", "message": "Scan triggered in background."}
