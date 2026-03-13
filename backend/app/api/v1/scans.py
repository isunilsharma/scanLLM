"""
Versioned scan API — /api/v1/scans

Provides all existing scan functionality plus new endpoints for
dependency graphs, risk scoring, and OWASP mapping.
"""
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Ensure backend root is importable
_backend_dir = str(Path(__file__).parent.parent.parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from core.database import get_db
from models.scan import ScanJob, ScanStatus
from models.finding import Finding

import json
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy imports for modules that may not exist yet
# ---------------------------------------------------------------------------

def _get_scanner_engine():
    """Import app.scanner.engine if available."""
    try:
        from app.scanner.engine import ScanEngine
        return ScanEngine
    except ImportError:
        return None


def _get_graph_builder():
    try:
        from app.graph.builder import GraphBuilder
        return GraphBuilder
    except ImportError:
        return None


def _get_graph_analyzer():
    try:
        from app.graph.analyzer import GraphAnalyzer
        return GraphAnalyzer
    except ImportError:
        return None


def _get_graph_serializer():
    try:
        from app.graph.serializer import GraphSerializer
        return GraphSerializer
    except ImportError:
        return None


def _get_risk_engine():
    try:
        from app.scoring.risk_engine import RiskEngine
        return RiskEngine
    except ImportError:
        return None


def _get_owasp_mapper():
    try:
        from app.scoring.owasp_mapper import OwaspMapper
        return OwaspMapper
    except ImportError:
        return None


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class ScanCreateRequest(BaseModel):
    repo_url: str
    full_scan: bool = False


class FindingOut(BaseModel):
    file_path: str
    line_number: int
    line_text: str
    framework: str
    pattern_name: str
    pattern_category: Optional[str] = None
    pattern_severity: Optional[str] = None
    pattern_description: Optional[str] = None
    snippet: Optional[str] = None
    model_name: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    is_streaming: Optional[bool] = None
    has_tools: Optional[bool] = None
    owner_name: Optional[str] = None
    owner_email: Optional[str] = None
    owner_committed_at: Optional[str] = None


class ScanSummary(BaseModel):
    scan_id: str
    repo_url: str
    status: str
    created_at: Optional[str] = None
    total_occurrences: int = 0
    files_count: int = 0


class ScanDetailResponse(BaseModel):
    scan_id: str
    status: str
    repo_url: str
    total_occurrences: int = 0
    files_count: int = 0
    files: List[Dict[str, Any]] = []
    frameworks_summary: List[Dict[str, Any]] = []
    hotspots: List[Dict[str, Any]] = []
    risk_flags: List[Dict[str, Any]] = []
    recommended_actions: List[Dict[str, Any]] = []
    policies_result: Dict[str, Any] = {}
    blast_radius_summary: Dict[str, int] = {}
    contracts: Dict[str, Any] = {}
    ownership_summary: List[Dict[str, Any]] = []
    heatmap: Dict[str, Dict[str, int]] = {}
    # New v1 fields
    graph: Optional[Dict[str, Any]] = None
    risk_score: Optional[Dict[str, Any]] = None
    owasp: Optional[List[Dict[str, Any]]] = None
    cached: bool = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _finding_to_dict(f: Finding) -> Dict[str, Any]:
    """Convert a Finding ORM object to a plain dict."""
    return {
        "file_path": f.file_path,
        "line_number": f.line_number,
        "line_text": f.line_text,
        "framework": f.framework,
        "pattern_name": f.pattern_name,
        "pattern_category": f.pattern_category,
        "pattern_severity": f.pattern_severity,
        "pattern_description": f.pattern_description,
        "snippet": f.snippet,
        "model_name": f.model_name,
        "temperature": f.temperature,
        "max_tokens": f.max_tokens,
        "is_streaming": f.is_streaming,
        "has_tools": f.has_tools,
        "owner_name": f.owner_name,
        "owner_email": f.owner_email,
        "owner_committed_at": (
            f.owner_committed_at.isoformat() if f.owner_committed_at else None
        ),
    }


def _get_scan_or_404(scan_id: str, db: Session) -> ScanJob:
    """Fetch a ScanJob or raise 404."""
    scan_job = db.query(ScanJob).filter(ScanJob.id == scan_id).first()
    if not scan_job:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan_job


def _enrich_with_graph(scan_id: str, findings: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Build dependency graph if the graph modules are available."""
    BuilderCls = _get_graph_builder()
    SerializerCls = _get_graph_serializer()
    if BuilderCls is None or SerializerCls is None:
        return None
    try:
        builder = BuilderCls()
        graph = builder.build(findings)
        serializer = SerializerCls()
        return serializer.to_react_flow(graph)
    except Exception as exc:
        logger.warning("Graph generation failed: %s", exc)
        return None


def _enrich_with_risk(scan_id: str, findings: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Compute risk score if the scoring module is available."""
    EngineCls = _get_risk_engine()
    if EngineCls is None:
        return None
    try:
        engine = EngineCls()
        return engine.score(findings)
    except Exception as exc:
        logger.warning("Risk scoring failed: %s", exc)
        return None


def _enrich_with_owasp(findings: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
    """Map findings to OWASP LLM Top 10 if the mapper is available."""
    MapperCls = _get_owasp_mapper()
    if MapperCls is None:
        return None
    try:
        mapper = MapperCls()
        return mapper.map_findings(findings)
    except Exception as exc:
        logger.warning("OWASP mapping failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/api/v1", tags=["scans-v1"])


@router.post("/scans", response_model=ScanDetailResponse)
async def create_scan(request: ScanCreateRequest, db: Session = Depends(get_db)):
    """Create and execute a repository scan."""
    if "github.com" not in request.repo_url.lower():
        raise HTTPException(status_code=400, detail="Only GitHub URLs are supported")

    try:
        # Check demo cache (same logic as existing server.py)
        from core.constants import SAMPLE_REPOS, SCAN_VERSION
        from models.demo_scan_cache import DemoScanCache
        from datetime import datetime, timezone

        if request.repo_url in SAMPLE_REPOS:
            scan_mode = "full" if request.full_scan else "journal"
            try:
                cached = (
                    db.query(DemoScanCache)
                    .filter(
                        DemoScanCache.repo_url == request.repo_url,
                        DemoScanCache.scan_mode == scan_mode,
                        DemoScanCache.scan_version == SCAN_VERSION,
                        DemoScanCache.status == "COMPLETE",
                    )
                    .first()
                )
                if cached and cached.result_payload_json:
                    if cached.expires_at is None or cached.expires_at > datetime.now(
                        timezone.utc
                    ):
                        logger.info("Demo cache HIT for %s (mode=%s)", request.repo_url, scan_mode)
                        result = json.loads(cached.result_payload_json)
                        result["cached"] = True
                        return result
            except Exception:
                logger.warning("Cache lookup failed, falling back to live scan")

        # Create scan job
        scan_job = ScanJob(repo_url=request.repo_url, status=ScanStatus.PENDING)
        db.add(scan_job)
        db.commit()
        db.refresh(scan_job)

        logger.info(
            "Starting v1 scan %s for %s (full_scan=%s)",
            scan_job.id,
            request.repo_url,
            request.full_scan,
        )

        # Run scanner (use existing ScannerV2)
        from services.scanner_v2 import ScannerV2

        scanner = ScannerV2(db)
        result = scanner.scan_repository(scan_job.id, request.repo_url, request.full_scan)

        # Enrich with new v1 data (graph, risk, owasp)
        findings_dicts = result.get("files", [])
        result["graph"] = _enrich_with_graph(scan_job.id, findings_dicts)
        result["risk_score"] = _enrich_with_risk(scan_job.id, findings_dicts)
        result["owasp"] = _enrich_with_owasp(findings_dicts)

        # Cache if sample repo
        if request.repo_url in SAMPLE_REPOS:
            try:
                scan_mode = "full" if request.full_scan else "journal"
                repo_parts = request.repo_url.replace("https://github.com/", "").split("/")
                from datetime import timedelta

                db.query(DemoScanCache).filter(
                    DemoScanCache.repo_url == request.repo_url,
                    DemoScanCache.scan_mode == scan_mode,
                    DemoScanCache.scan_version == SCAN_VERSION,
                ).delete()

                cache_entry = DemoScanCache(
                    repo_url=request.repo_url,
                    repo_owner=repo_parts[0] if len(repo_parts) > 0 else None,
                    repo_name=repo_parts[1] if len(repo_parts) > 1 else None,
                    scan_mode=scan_mode,
                    scan_version=SCAN_VERSION,
                    status="COMPLETE",
                    scan_id=scan_job.id,
                    result_payload_json=json.dumps(result),
                    expires_at=datetime.now(timezone.utc) + timedelta(days=7),
                )
                db.add(cache_entry)
                db.commit()
            except Exception as exc:
                logger.warning("Failed to cache scan result: %s", exc)

        return result

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Scan failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/scans", response_model=Dict[str, Any])
async def list_scans(
    repo_full_name: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List scans with pagination."""
    query = db.query(ScanJob)
    if repo_full_name:
        query = query.filter(ScanJob.repo_url.contains(repo_full_name))

    total = query.count()
    scans = query.order_by(ScanJob.created_at.desc()).offset(offset).limit(limit).all()

    items = []
    for scan in scans:
        items.append(
            {
                "id": scan.id,
                "repo_url": scan.repo_url,
                "repo_owner": scan.repo_owner,
                "repo_name": scan.repo_name,
                "status": scan.status.value,
                "created_at": scan.created_at.isoformat() if scan.created_at else None,
                "total_matches": scan.total_matches or scan.total_occurrences,
                "files_count": scan.files_count,
            }
        )

    return {"scans": items, "total": total, "limit": limit, "offset": offset}


@router.get("/scans/{scan_id}")
async def get_scan(scan_id: str, db: Session = Depends(get_db)):
    """Get a single scan with full detail."""
    scan_job = _get_scan_or_404(scan_id, db)

    if scan_job.status == ScanStatus.FAILED:
        raise HTTPException(
            status_code=500,
            detail=scan_job.error_message or "Scan failed",
        )

    findings_objs = db.query(Finding).filter(Finding.scan_id == scan_id).all()
    findings = [_finding_to_dict(f) for f in findings_objs]

    # Build base response via ScannerV2
    from services.scanner_v2 import ScannerV2

    scanner = ScannerV2(db)
    result = scanner._build_response_v2(scan_job, findings)

    # Enrich
    result["graph"] = _enrich_with_graph(scan_id, findings)
    result["risk_score"] = _enrich_with_risk(scan_id, findings)
    result["owasp"] = _enrich_with_owasp(findings)

    return result


@router.get("/scans/{scan_id}/graph")
async def get_scan_graph(scan_id: str, db: Session = Depends(get_db)):
    """Get the dependency graph for a scan in React Flow format."""
    scan_job = _get_scan_or_404(scan_id, db)

    findings_objs = db.query(Finding).filter(Finding.scan_id == scan_id).all()
    findings = [_finding_to_dict(f) for f in findings_objs]

    graph_data = _enrich_with_graph(scan_id, findings)
    if graph_data is None:
        return {
            "nodes": [],
            "edges": [],
            "message": "Graph module not yet available. Install app.graph to enable.",
        }
    return graph_data


@router.get("/scans/{scan_id}/findings")
async def get_scan_findings(
    scan_id: str,
    severity: Optional[str] = Query(None),
    component_type: Optional[str] = Query(None),
    owasp_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Get findings for a scan with optional filters."""
    _get_scan_or_404(scan_id, db)

    query = db.query(Finding).filter(Finding.scan_id == scan_id)

    if severity:
        query = query.filter(Finding.pattern_severity == severity)
    if component_type:
        query = query.filter(Finding.pattern_category == component_type)

    total = query.count()
    findings_objs = query.offset(offset).limit(limit).all()
    findings = [_finding_to_dict(f) for f in findings_objs]

    # If owasp_id filter is requested, post-filter via the mapper
    if owasp_id:
        mapped = _enrich_with_owasp(findings)
        if mapped:
            findings = [
                f
                for f, m in zip(findings, mapped)
                if m.get("owasp_id") == owasp_id
            ]
            total = len(findings)

    return {"findings": findings, "total": total, "limit": limit, "offset": offset}


@router.get("/scans/{scan_id}/risk")
async def get_scan_risk(scan_id: str, db: Session = Depends(get_db)):
    """Get the risk score breakdown for a scan."""
    _get_scan_or_404(scan_id, db)

    findings_objs = db.query(Finding).filter(Finding.scan_id == scan_id).all()
    findings = [_finding_to_dict(f) for f in findings_objs]

    risk_data = _enrich_with_risk(scan_id, findings)
    if risk_data is None:
        return {
            "score": None,
            "breakdown": {},
            "message": "Risk scoring module not yet available. Install app.scoring to enable.",
        }
    return risk_data


@router.get("/scans/{scan_id}/owasp")
async def get_scan_owasp(scan_id: str, db: Session = Depends(get_db)):
    """Get OWASP LLM Top 10 mapping for a scan."""
    _get_scan_or_404(scan_id, db)

    findings_objs = db.query(Finding).filter(Finding.scan_id == scan_id).all()
    findings = [_finding_to_dict(f) for f in findings_objs]

    owasp_data = _enrich_with_owasp(findings)
    if owasp_data is None:
        return {
            "mappings": [],
            "message": "OWASP mapper module not yet available. Install app.scoring to enable.",
        }
    return {"mappings": owasp_data}
