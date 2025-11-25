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
from services.scanner import Scanner
from core.config import config
from sqlalchemy.orm import Session

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
        
        # Run scanner
        scanner = Scanner(db)
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
    Retrieve a previously completed scan.
    """
    scan_job = db.query(ScanJob).filter(ScanJob.id == scan_id).first()
    if not scan_job:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    if scan_job.status == ScanStatus.FAILED:
        raise HTTPException(
            status_code=500,
            detail=scan_job.error_message or "Scan failed"
        )
    
    # Get findings
    findings = db.query(Finding).filter(Finding.scan_id == scan_id).all()
    
    # Build response
    files_map = {}
    for finding in findings:
        if finding.file_path not in files_map:
            files_map[finding.file_path] = {
                'file_path': finding.file_path,
                'frameworks': set(),
                'occurrences': []
            }
        
        files_map[finding.file_path]['frameworks'].add(finding.framework)
        files_map[finding.file_path]['occurrences'].append({
            'line_number': finding.line_number,
            'line_text': finding.line_text,
            'framework': finding.framework,
            'pattern_name': finding.pattern_name
        })
    
    files_list = []
    for file_data in files_map.values():
        file_data['frameworks'] = sorted(list(file_data['frameworks']))
        files_list.append(file_data)
    
    files_list.sort(key=lambda x: x['file_path'])
    
    return {
        'scan_id': scan_job.id,
        'status': scan_job.status.value,
        'repo_url': scan_job.repo_url,
        'total_occurrences': scan_job.total_occurrences,
        'files_count': scan_job.files_count,
        'files': files_list
    }

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

# Include router
app.include_router(api_router)

@app.get("/health")
async def health():
    return {"status": "ok"}
