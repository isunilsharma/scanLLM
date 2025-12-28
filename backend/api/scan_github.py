from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any

from core.database import get_db
from models.scan import ScanJob, ScanStatus
from models.github_user import GitHubUser
from models.github_token import GitHubToken
from services.token_encryption import decrypt_token
from api.github_endpoints import get_current_user, get_github_token
from services.github_scanner import GitHubScanner

router = APIRouter(prefix="/api/scan")

class GitHubScanRequest(BaseModel):
    owner: str
    repo: str
    branch: str = 'main'
    full_scan: bool = False

@router.post("/github")
async def scan_github_repo(
    request: GitHubScanRequest,
    user: GitHubUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        scan_job = ScanJob(
            repo_url=f"https://github.com/{request.owner}/{request.repo}",
            status=ScanStatus.PENDING,
            github_user_id=user.id,
            repo_owner=request.owner,
            repo_name=request.repo,
            repo_private=1,
            source='github_oauth'
        )
        db.add(scan_job)
        db.commit()
        db.refresh(scan_job)
        
        access_token = get_github_token(user, db)
        scanner = GitHubScanner(db, access_token)
        result = scanner.scan_repo(scan_job.id, request.owner, request.repo, request.branch, request.full_scan)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
