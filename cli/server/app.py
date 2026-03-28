"""Local web server for `scanllm ui` — serves the React dashboard and scan data APIs."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# HTML fallback when the built frontend is not available
_FALLBACK_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>ScanLLM Dashboard</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         background: #0a0a0a; color: #e4e4e7; display: flex; align-items: center;
         justify-content: center; min-height: 100vh; }
  .container { text-align: center; max-width: 600px; padding: 2rem; }
  h1 { font-size: 2rem; margin-bottom: 0.5rem; }
  .subtitle { color: #71717a; margin-bottom: 2rem; }
  .scan-data { background: #18181b; border: 1px solid #27272a; border-radius: 12px;
               padding: 1.5rem; text-align: left; margin-bottom: 1.5rem; }
  .metric { display: flex; justify-content: space-between; padding: 0.5rem 0;
            border-bottom: 1px solid #27272a; }
  .metric:last-child { border-bottom: none; }
  .metric-label { color: #a1a1aa; }
  .metric-value { font-weight: 600; }
  .grade-A, .grade-B { color: #4ade80; }
  .grade-C { color: #facc15; }
  .grade-D, .grade-F { color: #f87171; }
  .info { color: #71717a; font-size: 0.875rem; }
  code { background: #27272a; padding: 2px 6px; border-radius: 4px; font-size: 0.875rem; }
  a { color: #22d3ee; }
</style>
</head>
<body>
<div class="container">
  <h1>ScanLLM Dashboard</h1>
  <p class="subtitle">Local scan results</p>
  <div id="scan-data" class="scan-data">
    <p style="color: #71717a;">Loading scan data...</p>
  </div>
  <p class="info">
    Full interactive dashboard with dependency graph coming soon.<br/>
    Use <code>scanllm scan . --output json</code> for structured output.<br/>
    Visit <a href="https://scanllm.ai" target="_blank">scanllm.ai</a> for the cloud dashboard.
  </p>
</div>
<script>
  fetch('/api/scan/latest')
    .then(r => r.json())
    .then(data => {
      const el = document.getElementById('scan-data');
      if (!data || !data.summary) {
        el.innerHTML = '<p style="color:#71717a">No scan data found. Run <code>scanllm scan . --save</code> first.</p>';
        return;
      }
      const s = data.summary || {};
      const risk = data.risk || {};
      const grade = risk.grade || '?';
      const score = risk.overall_score ?? '?';
      el.innerHTML = `
        <div class="metric"><span class="metric-label">Risk Score</span>
          <span class="metric-value grade-${grade}">${score}/100 (Grade ${grade})</span></div>
        <div class="metric"><span class="metric-label">AI Components</span>
          <span class="metric-value">${s.total_findings || 0} across ${s.ai_files_count || 0} files</span></div>
        <div class="metric"><span class="metric-label">Files Scanned</span>
          <span class="metric-value">${s.files_scanned || 0}</span></div>
        <div class="metric"><span class="metric-label">Providers</span>
          <span class="metric-value">${Object.keys(s.providers || {}).join(', ') || 'None'}</span></div>
        <div class="metric"><span class="metric-label">Severities</span>
          <span class="metric-value">${Object.entries(s.severities || {}).filter(([_,v])=>v>0).map(([k,v])=>`${v} ${k}`).join(', ') || 'None'}</span></div>
      `;
    })
    .catch(() => {
      document.getElementById('scan-data').innerHTML =
        '<p style="color:#f87171">Failed to load scan data.</p>';
    });
</script>
</body>
</html>"""


def create_app(repo_path: Path) -> Any:
    """Create a FastAPI app that serves scan data and the dashboard UI."""
    try:
        from fastapi import FastAPI
        from fastapi.responses import HTMLResponse, JSONResponse
    except ImportError:
        raise ImportError(
            "FastAPI is required for `scanllm ui`. Install with: pip install scanllm[server]"
        )

    from cli.config import ScanLLMConfig

    config = ScanLLMConfig(repo_path)
    app = FastAPI(title="ScanLLM Local Dashboard", docs_url=None, redoc_url=None)

    @app.get("/", response_class=HTMLResponse)
    async def index():
        # Check for built frontend
        dist_dir = Path(__file__).parent.parent.parent / "frontend" / "build"
        index_html = dist_dir / "index.html"
        if index_html.exists():
            return HTMLResponse(index_html.read_text())
        return HTMLResponse(_FALLBACK_HTML)

    @app.get("/api/scan/latest")
    async def latest_scan():
        data = config.get_latest_scan()
        if data is None:
            return JSONResponse({"error": "No scans found"}, status_code=404)
        return JSONResponse(data)

    @app.get("/api/scan/history")
    async def scan_history():
        scans = config.get_scan_history()
        return JSONResponse(scans)

    @app.get("/api/graph")
    async def graph():
        data = config.get_latest_scan()
        if not data:
            return JSONResponse({"nodes": [], "edges": []})
        return JSONResponse(data.get("graph", {"nodes": [], "edges": []}))

    @app.get("/api/risk")
    async def risk():
        data = config.get_latest_scan()
        if not data:
            return JSONResponse({"overall_score": 0, "grade": "A"})
        return JSONResponse(data.get("risk", {"overall_score": 0, "grade": "A"}))

    @app.get("/api/owasp")
    async def owasp():
        data = config.get_latest_scan()
        if not data:
            return JSONResponse({"categories": [], "coverage": {}})
        return JSONResponse(data.get("owasp", {"categories": [], "coverage": {}}))

    @app.get("/api/policy")
    async def policy_eval():
        data = config.get_latest_scan()
        if not data:
            return JSONResponse({"passed": True, "results": []})

        # Run policy evaluation if policies exist
        policies_path = config.get_policies_path()
        if not policies_path:
            return JSONResponse({"passed": True, "results": [], "message": "No policies configured"})

        try:
            from core.policy.engine import PolicyEngine
            engine = PolicyEngine(policies_path=policies_path)
            findings = data.get("findings", [])
            summary = data.get("summary", {})
            result = engine.evaluate(findings, summary)
            return JSONResponse(result.to_dict())
        except Exception as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)

    @app.post("/api/scan")
    async def trigger_scan():
        """Trigger a new scan from the UI."""
        try:
            from core.scanner.engine import ScanEngine
            from core.scoring.risk_engine import RiskEngine
            from core.scoring.owasp_mapper import OwaspMapper
            from core.graph.builder import GraphBuilder
            from core.graph.serializer import GraphSerializer
            from core.graph.analyzer import GraphAnalyzer

            engine = ScanEngine()
            result = engine.scan(repo_path)
            findings = result.get("findings", [])

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

            from datetime import datetime, timezone
            result["risk"] = risk_result
            result["owasp"] = owasp_result
            result["graph"] = graph_data
            result["risk_score"] = risk_result.get("overall_score", 0)
            result["timestamp"] = datetime.now(timezone.utc).isoformat()

            config.save_scan(result)
            return JSONResponse(result)
        except Exception as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)

    return app
