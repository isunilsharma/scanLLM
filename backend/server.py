from fastapi import FastAPI, APIRouter, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Any
import logging
import os
from pathlib import Path

from core.database import get_db, init_db
from models.scan import ScanJob, ScanStatus
from models.finding import Finding
from services.scanner_v2 import ScannerV2
from services.llm_explainer import explain_scan
from core.config import config
from sqlalchemy.orm import Session
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize database
init_db()

# Create FastAPI app
app = FastAPI(title="AI Dependency Scanner")
api_router = APIRouter(prefix="/api")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class ScanRequest(BaseModel):
    repo_url: str

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
    # v2 fields
    policies_result: Dict[str, Any] = {}
    blast_radius_summary: Dict[str, int] = {}
    contracts: Dict[str, Any] = {}
    ownership_summary: List[Dict[str, Any]] = []
    heatmap: Dict[str, Dict[str, int]] = {}

class PatternConfigResponse(BaseModel):
    frameworks: List[Dict[str, Any]]

# API Endpoints
@api_router.post("/scans", response_model=ScanResponse)
async def create_scan(request: ScanRequest, db: Session = Depends(get_db)):
    """
    Start a new repository scan.
    """
    try:
        # Validate GitHub URL (basic check)
        if "github.com" not in request.repo_url.lower():
            raise HTTPException(status_code=400, detail="Only GitHub URLs are supported")
        
        # Create scan job
        scan_job = ScanJob(
            repo_url=request.repo_url,
            status=ScanStatus.PENDING
        )
        db.add(scan_job)
        db.commit()
        db.refresh(scan_job)
        
        logger.info(f"Starting scan {scan_job.id} for {request.repo_url}")
        
        # Run scanner v2
        scanner = ScannerV2(db)
        result = scanner.scan_repository(scan_job.id, request.repo_url)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Scan failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/scans/{scan_id}", response_model=ScanResponse)
async def get_scan(scan_id: str, db: Session = Depends(get_db)):
    """
    Retrieve a previously completed scan with v2 data.
    """
    from services.scanner_v2 import ScannerV2
    
    scan_job = db.query(ScanJob).filter(ScanJob.id == scan_id).first()
    if not scan_job:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    if scan_job.status == ScanStatus.FAILED:
        raise HTTPException(
            status_code=500,
            detail=scan_job.error_message or "Scan failed"
        )
    
    # Get findings
    findings_objs = db.query(Finding).filter(Finding.scan_id == scan_id).all()
    
    # Convert to dict format with all v2 fields
    findings = []
    for f in findings_objs:
        findings.append({
            'file_path': f.file_path,
            'line_number': f.line_number,
            'line_text': f.line_text,
            'framework': f.framework,
            'pattern_name': f.pattern_name,
            'pattern_category': f.pattern_category,
            'pattern_severity': f.pattern_severity,
            'pattern_description': f.pattern_description,
            'snippet': f.snippet,
            'model_name': f.model_name,
            'temperature': f.temperature,
            'max_tokens': f.max_tokens,
            'is_streaming': f.is_streaming,
            'has_tools': f.has_tools,
            'owner_name': f.owner_name,
            'owner_email': f.owner_email,
            'owner_committed_at': f.owner_committed_at.isoformat() if f.owner_committed_at else None
        })
    
    # Use ScannerV2 to build response
    scanner = ScannerV2(db)
    return scanner._build_response_v2(scan_job, findings)

@api_router.get("/config/patterns", response_model=PatternConfigResponse)
async def get_patterns():
    """
    Return current pattern configuration.
    """
    frameworks_list = []
    for framework, data in config.patterns.get('frameworks', {}).items():
        framework_info = {
            'name': framework,
            'description': data.get('description', ''),
            'patterns': [
                {
                    'name': p['name'],
                    'regex': p['regex'],
                    'enabled': p.get('enabled', True)
                }
                for p in data.get('patterns', [])
            ]
        }
        frameworks_list.append(framework_info)
    
    return {'frameworks': frameworks_list}

# v2 Endpoints

class ExplainRequest(BaseModel):
    scan_id: str

class ExplainResponse(BaseModel):
    scan_id: str
    explanation: str

@api_router.post("/explain-scan", response_model=ExplainResponse)
async def explain_scan_endpoint(request: ExplainRequest, db: Session = Depends(get_db)):
    """
    Generate LLM-powered explanation of scan results.
    """
    scan_job = db.query(ScanJob).filter(ScanJob.id == request.scan_id).first()
    if not scan_job:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    if scan_job.status != ScanStatus.SUCCESS:
        raise HTTPException(status_code=400, detail="Scan not completed successfully")
    
    # Get the full scan data (reuse GET /scans/{id} logic)
    from services.scanner_v2 import ScannerV2
    scanner = ScannerV2(db)
    
    # Get findings for this scan
    findings_objs = db.query(Finding).filter(Finding.scan_id == request.scan_id).all()
    findings = []
    for f in findings_objs:
        findings.append({
            'file_path': f.file_path,
            'line_number': f.line_number,
            'line_text': f.line_text,
            'framework': f.framework,
            'pattern_name': f.pattern_name,
            'pattern_category': f.pattern_category,
            'pattern_severity': f.pattern_severity,
            'pattern_description': f.pattern_description,
            'snippet': f.snippet,
            'model_name': f.model_name,
            'temperature': f.temperature,
            'max_tokens': f.max_tokens,
            'is_streaming': f.is_streaming,
            'has_tools': f.has_tools,
            'owner_name': f.owner_name,
            'owner_email': f.owner_email,
            'owner_committed_at': f.owner_committed_at.isoformat() if f.owner_committed_at else None
        })
    
    # Build scan data for LLM
    scan_data = scanner._build_response_v2(scan_job, findings)
    
    # Generate explanation
    explanation = await explain_scan(scan_data)
    
    return {
        'scan_id': request.scan_id,
        'explanation': explanation
    }

class ScanHistoryItem(BaseModel):
    id: str
    repo_url: str
    created_at: str
    status: str
    total_matches: int
    ai_files_count: int
    frameworks_json: str

@api_router.get("/scan-history")
async def get_scan_history(repo_url: str, db: Session = Depends(get_db)):
    """
    Get scan history for a repository.
    Returns last 10 scans.
    """
    scans = db.query(ScanJob).filter(
        ScanJob.repo_url == repo_url,
        ScanJob.status == ScanStatus.SUCCESS
    ).order_by(ScanJob.created_at.desc()).limit(10).all()
    
    history = []
    for scan in scans:
        history.append({
            'id': scan.id,
            'repo_url': scan.repo_url,
            'created_at': scan.created_at.isoformat() if scan.created_at else None,
            'status': scan.status.value,
            'total_matches': scan.total_matches or scan.total_occurrences,
            'ai_files_count': scan.ai_files_count or scan.files_count,
            'frameworks_json': scan.frameworks_json or '{}'
        })
    
    return {'scans': history}


# Include router
app.include_router(api_router)

@app.get("/health")
async def health():
    return {"status": "ok"}
