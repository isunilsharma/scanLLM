"""
ScanLLM API — Restructured Entry Point

Drop-in replacement for server.py that includes both the existing (legacy)
routers and the new /api/v1 routers.

Run with:
    cd backend && uvicorn app.main:app --reload --port 8000
"""
import sys
import os
import logging
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup — ensure the backend root is importable so that the existing
# code (core.*, models.*, services.*, api.*) works unchanged.
# ---------------------------------------------------------------------------
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi import FastAPI, APIRouter, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
from sqlalchemy.orm import Session

# ---------------------------------------------------------------------------
# Existing imports (backward compatibility)
# ---------------------------------------------------------------------------
from core.database import get_db, init_db
from models.scan import ScanJob, ScanStatus
from models.finding import Finding
from services.scanner_v2 import ScannerV2
from services.llm_explainer import explain_scan
from core.config import config
from core.constants import SAMPLE_REPOS, SCAN_VERSION
from models.demo_scan_cache import DemoScanCache
from datetime import datetime, timezone, timedelta
import json

# Existing routers
from api.auth_github import router as auth_router
from api.github_endpoints import router as github_router
from api.scan_github import router as scan_github_router

# ---------------------------------------------------------------------------
# New v1 routers
# ---------------------------------------------------------------------------
from app.api.v1.scans import router as v1_scans_router
from app.api.v1.reports import router as v1_reports_router

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Initialize database
# ---------------------------------------------------------------------------
init_db()

# ---------------------------------------------------------------------------
# Create FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="ScanLLM — AI Dependency Intelligence",
    description="Scan codebases to discover, map, and govern all AI/LLM dependencies.",
    version="0.2.0",
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
cors_origins = os.getenv(
    "CORS_ORIGINS", "https://scanllm.ai,http://localhost:3000"
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=[origin.strip() for origin in cors_origins],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Legacy API router (preserves existing /api/* endpoints)
# ---------------------------------------------------------------------------
api_router = APIRouter(prefix="/api")


class ScanRequest(BaseModel):
    repo_url: str
    full_scan: bool = False


class ScanResponse(BaseModel):
    scan_id: str
    status: str
    repo_url: str
    total_occurrences: int
    files_count: int
    files: List[Dict[str, Any]]
    frameworks_summary: List[Dict[str, Any]] = []
    hotspots: List[Dict[str, Any]] = []
    risk_flags: List[Dict[str, Any]] = []
    recommended_actions: List[Dict[str, Any]] = []
    policies_result: Dict[str, Any] = {}
    blast_radius_summary: Dict[str, int] = {}
    contracts: Dict[str, Any] = {}
    ownership_summary: List[Dict[str, Any]] = []
    heatmap: Dict[str, Dict[str, int]] = {}
    cached: bool = False


class PatternConfigResponse(BaseModel):
    frameworks: List[Dict[str, Any]]


@api_router.post("/scans", response_model=ScanResponse)
async def create_scan(request: ScanRequest, db: Session = Depends(get_db)):
    """Start a new repository scan with demo caching support."""
    try:
        if "github.com" not in request.repo_url.lower():
            raise HTTPException(status_code=400, detail="Only GitHub URLs are supported")

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
                        logger.info(
                            "Demo cache HIT for %s (mode=%s)",
                            request.repo_url,
                            scan_mode,
                        )
                        result = json.loads(cached.result_payload_json)
                        result["cached"] = True
                        return result
                logger.info(
                    "Demo cache MISS for %s (mode=%s) - running live scan",
                    request.repo_url,
                    scan_mode,
                )
            except Exception as e:
                logger.warning("Cache lookup failed: %s - falling back to live scan", e)

        scan_job = ScanJob(repo_url=request.repo_url, status=ScanStatus.PENDING)
        db.add(scan_job)
        db.commit()
        db.refresh(scan_job)

        logger.info(
            "Starting scan %s for %s (full_scan=%s)",
            scan_job.id,
            request.repo_url,
            request.full_scan,
        )

        scanner = ScannerV2(db)
        result = scanner.scan_repository(scan_job.id, request.repo_url, request.full_scan)

        if request.repo_url in SAMPLE_REPOS:
            scan_mode = "full" if request.full_scan else "journal"
            repo_parts = request.repo_url.replace("https://github.com/", "").split("/")
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
            logger.info("Cached result for %s (mode=%s)", request.repo_url, scan_mode)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Scan failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/scans/{scan_id}", response_model=ScanResponse)
async def get_scan(scan_id: str, db: Session = Depends(get_db)):
    """Retrieve a previously completed scan with v2 data."""
    scan_job = db.query(ScanJob).filter(ScanJob.id == scan_id).first()
    if not scan_job:
        raise HTTPException(status_code=404, detail="Scan not found")

    if scan_job.status == ScanStatus.FAILED:
        raise HTTPException(
            status_code=500,
            detail=scan_job.error_message or "Scan failed",
        )

    findings_objs = db.query(Finding).filter(Finding.scan_id == scan_id).all()
    findings = []
    for f in findings_objs:
        findings.append(
            {
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
        )

    scanner = ScannerV2(db)
    return scanner._build_response_v2(scan_job, findings)


@api_router.get("/config/patterns", response_model=PatternConfigResponse)
async def get_patterns():
    """Return current pattern configuration."""
    frameworks_list = []
    for framework, data in config.patterns.get("frameworks", {}).items():
        framework_info = {
            "name": framework,
            "description": data.get("description", ""),
            "patterns": [
                {
                    "name": p["name"],
                    "regex": p["regex"],
                    "enabled": p.get("enabled", True),
                }
                for p in data.get("patterns", [])
            ],
        }
        frameworks_list.append(framework_info)
    return {"frameworks": frameworks_list}


class ExplainRequest(BaseModel):
    scan_id: str


class ExplainResponse(BaseModel):
    scan_id: str
    explanation: str


@api_router.post("/explain-scan", response_model=ExplainResponse)
async def explain_scan_endpoint(
    request: ExplainRequest, db: Session = Depends(get_db)
):
    """Generate LLM-powered explanation of scan results."""
    scan_job = db.query(ScanJob).filter(ScanJob.id == request.scan_id).first()
    if not scan_job:
        raise HTTPException(status_code=404, detail="Scan not found")

    if scan_job.status != ScanStatus.SUCCESS:
        raise HTTPException(status_code=400, detail="Scan not completed successfully")

    findings_objs = (
        db.query(Finding).filter(Finding.scan_id == request.scan_id).all()
    )
    findings = []
    for f in findings_objs:
        findings.append(
            {
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
        )

    scanner = ScannerV2(db)
    scan_data = scanner._build_response_v2(scan_job, findings)
    explanation = await explain_scan(scan_data)

    return {"scan_id": request.scan_id, "explanation": explanation}


@api_router.get("/scans")
async def get_scan_history(
    repo_full_name: str = None,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """Get scan history, optionally filtered by repo."""
    query = db.query(ScanJob)
    if repo_full_name:
        query = query.filter(ScanJob.repo_url.contains(repo_full_name))

    scans = query.order_by(ScanJob.created_at.desc()).limit(limit).all()
    scan_list = []
    for scan in scans:
        scan_list.append(
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
    return {"scans": scan_list}


@api_router.get("/scan-history")
async def get_repo_scan_history(repo_url: str, db: Session = Depends(get_db)):
    """Get scan history for a repository. Returns last 10 scans."""
    scans = (
        db.query(ScanJob)
        .filter(ScanJob.repo_url == repo_url, ScanJob.status == ScanStatus.SUCCESS)
        .order_by(ScanJob.created_at.desc())
        .limit(10)
        .all()
    )

    history = []
    for scan in scans:
        history.append(
            {
                "id": scan.id,
                "repo_url": scan.repo_url,
                "created_at": scan.created_at.isoformat() if scan.created_at else None,
                "status": scan.status.value,
                "total_matches": scan.total_matches or scan.total_occurrences,
                "ai_files_count": scan.ai_files_count or scan.files_count,
                "frameworks_json": scan.frameworks_json or "{}",
            }
        )
    return {"scans": history}


# ---------------------------------------------------------------------------
# Mount all routers
# ---------------------------------------------------------------------------

# Legacy /api/* endpoints (backward compat with server.py)
app.include_router(api_router)

# Existing OAuth & GitHub routers
app.include_router(auth_router)
app.include_router(github_router)
app.include_router(scan_github_router)

# New v1 routers
app.include_router(v1_scans_router)
app.include_router(v1_reports_router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.2.0"}
