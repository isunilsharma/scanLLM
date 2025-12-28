from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any

from core.database import get_db
from models.github_user import GitHubUser
from models.github_token import GitHubToken
from services.token_encryption import decrypt_token
from services.session_manager import verify_session_token
from services.github_api import GitHubAPI

router = APIRouter(prefix="/api/github")

def get_current_user(request: Request, db: Session = Depends(get_db)):
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    payload = verify_session_token(session_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid session")
    
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
async def get_user(user: GitHubUser = Depends(get_current_user)):
    return {
        'id': user.id,
        'github_user_id': user.github_user_id,
        'login': user.login,
        'name': user.name,
        'email': user.email,
        'avatar_url': user.avatar_url
    }

@router.get("/repos")
async def get_repos(
    visibility: str = 'all',
    user: GitHubUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    access_token = get_github_token(user, db)
    github_api = GitHubAPI(access_token)
    
    repos = github_api.get_repos(visibility)
    
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
    
    return {'repos': simplified}

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
