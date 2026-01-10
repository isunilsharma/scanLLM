from fastapi import APIRouter, HTTPException, Response, Request, Depends
from fastapi.responses import RedirectResponse
import requests
import os
import json
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from core.database import get_db
from models.github_user import GitHubUser
from models.github_token import GitHubToken
from services.token_encryption import encrypt_token
from services.session_manager import create_session_token, SESSION_SECRET, ALGORITHM
from jose import jwt

load_dotenv()

router = APIRouter(prefix="/api/auth")

GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET')
GITHUB_REDIRECT_URI = os.getenv('GITHUB_REDIRECT_URI')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'https://scanllm.ai')

@router.get("/github/login")
async def github_login():
    # Create JWT-based state (stateless, no database needed)
    state_payload = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'purpose': 'github_oauth'
    }
    state = jwt.encode(state_payload, SESSION_SECRET, algorithm=ALGORITHM)
    
    auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        f"&redirect_uri={GITHUB_REDIRECT_URI}"
        f"&state={state}"
        f"&scope=repo read:org"
    )
    return RedirectResponse(auth_url)

@router.get("/github/callback")
async def github_callback(code: str, state: str, db: Session = Depends(get_db)):
    # Verify JWT state
    try:
        payload = jwt.decode(state, SESSION_SECRET, algorithms=[ALGORITHM])
        state_time = datetime.fromisoformat(payload['timestamp'])
        if datetime.now(timezone.utc) - state_time > timedelta(minutes=10):
            raise HTTPException(status_code=400, detail="State expired")
    except jwt.JWTError:
        raise HTTPException(status_code=400, detail="Invalid state")
    
    # Exchange code for token
    token_response = requests.post(
        "https://github.com/login/oauth/access_token",
        data={
            'client_id': GITHUB_CLIENT_ID,
            'client_secret': GITHUB_CLIENT_SECRET,
            'code': code,
            'redirect_uri': GITHUB_REDIRECT_URI
        },
        headers={'Accept': 'application/json'},
        timeout=10
    )
    token_data = token_response.json()
    access_token = token_data.get('access_token')
    
    if not access_token:
        raise HTTPException(status_code=400, detail="Failed to get access token")
    
    # Get user info
    user_response = requests.get(
        "https://api.github.com/user",
        headers={'Authorization': f'Bearer {access_token}', 'Accept': 'application/vnd.github+json'},
        timeout=10
    )
    user_data = user_response.json()
    
    # Store user
    github_user = db.query(GitHubUser).filter(GitHubUser.github_user_id == str(user_data['id'])).first()
    if not github_user:
        github_user = GitHubUser(
            github_user_id=str(user_data['id']),
            login=user_data['login'],
            name=user_data.get('name'),
            email=user_data.get('email'),
            avatar_url=user_data.get('avatar_url')
        )
        db.add(github_user)
        db.commit()
        db.refresh(github_user)
    
    # Store token
    existing_token = db.query(GitHubToken).filter(GitHubToken.github_user_id == github_user.id).first()
    if existing_token:
        db.delete(existing_token)
    
    encrypted = encrypt_token(access_token)
    new_token = GitHubToken(
        github_user_id=github_user.id,
        encrypted_token=encrypted,
        scope=token_data.get('scope', 'repo')
    )
    db.add(new_token)
    db.commit()
    
    # Create session token
    session_jwt = create_session_token(github_user.id, github_user.github_user_id)
    
    user_json = {
        'id': github_user.id,
        'github_user_id': github_user.github_user_id,
        'login': github_user.login,
        'name': github_user.name,
        'email': github_user.email,
        'avatar_url': github_user.avatar_url
    }
    
    # Return HTML page that stores token and redirects
    user_json_str = json.dumps(user_json)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Completing sign-in...</title>
        <style>
            body {{ font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; background: #f5f7fb; }}
            .spinner {{ border: 4px solid #e5e7eb; border-top: 4px solid #1C4CE0; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto 20px; }}
            @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
        </style>
    </head>
    <body>
        <div>
            <div class="spinner"></div>
            <h2>Completing sign-in...</h2>
            <p>Redirecting to your repositories...</p>
        </div>
        <script>
            localStorage.setItem('auth_token', '{session_jwt}');
            localStorage.setItem('user', '{user_json_str}');
            setTimeout(function() {{ window.location.href = '{FRONTEND_URL}/app/repos'; }}, 500);
        </script>
    </body>
    </html>
    """
    
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content)
