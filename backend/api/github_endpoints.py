from fastapi import APIRouter, HTTPException, Depends, Request, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import logging

from core.database import get_db
from models.github_user import GitHubUser
from models.github_token import GitHubToken
from services.token_encryption import decrypt_token
from services.session_manager import verify_session_token
from services.github_api import GitHubAPI

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/github")

def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    """Get current user from Authorization header (Bearer token)"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.replace('Bearer ', '')
    payload = verify_session_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user = db.query(GitHubUser).filter(GitHubUser.id == payload['user_id']).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

def get_github_token(user: GitHubUser, db: Session) -> str:
    token_obj = db.query(GitHubToken).filter(GitHubToken.github_user_id == user.id).first()
    if not token_obj:
        raise HTTPException(status_code=401, detail="No GitHub token found")
    return decrypt_token(token_obj.encrypted_token)

@router.get("/user")
async def get_user(user: GitHubUser = Depends(get_current_user), db: Session = Depends(get_db)):
    # Check admin status
    admin = False
    try:
        from app.api.deps import is_admin as check_admin
        admin = check_admin(user, db)
    except Exception:
        pass

    return {
        'id': user.id,
        'github_user_id': user.github_user_id,
        'login': user.login,
        'name': user.name,
        'email': user.email,
        'avatar_url': user.avatar_url,
        'is_admin': admin,
    }

@router.get("/repos")
async def get_repos(
    visibility: str = 'all',
    user: GitHubUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user repositories with strict user isolation"""
    logger.info(f"Fetching repos for user {user.login} (visibility={visibility})")
    
    access_token = get_github_token(user, db)
    github_api = GitHubAPI(access_token)
    
    try:
        repos = github_api.get_repos(visibility)
        logger.info(f"✓ Fetched {len(repos)} repos for user {user.login}")
    except Exception as e:
        logger.error(f"Failed to fetch repos for user {user.login}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch repositories")
    
    simplified = []
    for repo in repos:
        simplified.append({
            'owner': repo['owner']['login'],
            'name': repo['name'],
            'full_name': repo['full_name'],
            'private': repo['private'],
            'default_branch': repo.get('default_branch', 'main'),
            'updated_at': repo.get('updated_at'),
            'description': repo.get('description')
        })
    
    # Strict caching headers for user isolation
    from fastapi import Response as FastAPIResponse
    response = FastAPIResponse(
        content=json.dumps({'repos': simplified}),
        media_type='application/json',
        headers={
            'Cache-Control': 'no-store, no-cache, must-revalidate, private',
            'Pragma': 'no-cache',
            'Vary': 'Authorization',
            'X-User-ID': user.id  # For debugging (never expose sensitive data)
        }
    )
    return response

@router.post("/revoke")
async def revoke_github(
    request: Request,
    user: GitHubUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    token_obj = db.query(GitHubToken).filter(GitHubToken.github_user_id == user.id).first()
    if token_obj:
        db.delete(token_obj)
    
    db.delete(user)
    db.commit()
    
    from fastapi.responses import JSONResponse
    response = JSONResponse({'message': 'GitHub access revoked'})
    response.delete_cookie("session_token")
    return response
