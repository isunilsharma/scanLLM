from fastapi import APIRouter, HTTPException, Response, Request, Depends
from fastapi.responses import RedirectResponse
import requests
import os
import json
import logging
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

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth")

GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET')
GITHUB_REDIRECT_URI = os.getenv('GITHUB_REDIRECT_URI')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'https://scanllm.ai')

@router.get("/github/login")
async def github_login():
    logger.info("=== GitHub OAuth Login Started ===")
    logger.info(f"GITHUB_CLIENT_ID: {GITHUB_CLIENT_ID[:10]}...")
    logger.info(f"GITHUB_REDIRECT_URI: {GITHUB_REDIRECT_URI}")
    
    # Create JWT-based state
    state_payload = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'purpose': 'github_oauth'
    }
    state = jwt.encode(state_payload, SESSION_SECRET, algorithm=ALGORITHM)
    logger.info(f"Generated state token: {state[:50]}...")
    
    auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        f"&redirect_uri={GITHUB_REDIRECT_URI}"
        f"&state={state}"
        f"&scope=repo read:org"
    )
    logger.info(f"Redirecting to GitHub OAuth: {auth_url[:100]}...")
    return RedirectResponse(auth_url)

@router.get("/github/callback")
async def github_callback(code: str, state: str, db: Session = Depends(get_db)):
    logger.info("=== GitHub OAuth Callback Received ===")
    logger.info(f"Code: {code[:20]}...")
    logger.info(f"State: {state[:50]}...")
    
    # Verify JWT state
    try:
        logger.info("Verifying state token...")
        payload = jwt.decode(state, SESSION_SECRET, algorithms=[ALGORITHM])
        state_time = datetime.fromisoformat(payload['timestamp'])
        age = (datetime.now(timezone.utc) - state_time).total_seconds()
        logger.info(f"State age: {age}s")
        
        if datetime.now(timezone.utc) - state_time > timedelta(minutes=10):
            logger.error("State expired!")
            raise HTTPException(status_code=400, detail="State expired")
        logger.info("✓ State validated")
    except jwt.JWTError as e:
        logger.error(f"State validation failed: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid state")
    
    # Exchange code for token
    logger.info("Exchanging code for access token...")
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
        logger.error(f"Failed to get access token: {token_data}")
        raise HTTPException(status_code=400, detail="Failed to get access token")
    logger.info(f"✓ Access token received: {access_token[:20]}...")
    
    # Get user info
    logger.info("Fetching user info from GitHub...")
    user_response = requests.get(
        "https://api.github.com/user",
        headers={'Authorization': f'Bearer {access_token}', 'Accept': 'application/vnd.github+json'},
        timeout=10
    )
    user_data = user_response.json()
    logger.info(f"✓ User: @{user_data.get('login')} (ID: {user_data.get('id')})")
    
    # Store user
    logger.info("Storing user in database...")
    github_user = db.query(GitHubUser).filter(GitHubUser.github_user_id == str(user_data['id'])).first()
    if not github_user:
        logger.info("Creating new user record")
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
        logger.info(f"✓ User created: {github_user.id}")
    else:
        logger.info(f"✓ Existing user found: {github_user.id}")
    
    # Store token
    logger.info("Storing encrypted GitHub token...")
    existing_token = db.query(GitHubToken).filter(GitHubToken.github_user_id == github_user.id).first()
    if existing_token:
        db.delete(existing_token)
        logger.info("Deleted old token")
    
    encrypted = encrypt_token(access_token)
    new_token = GitHubToken(
        github_user_id=github_user.id,
        encrypted_token=encrypted,
        scope=token_data.get('scope', 'repo')
    )
    db.add(new_token)
    db.commit()
    logger.info("✓ Token stored")
    
    # Create session token
    logger.info("Creating session JWT...")
    session_jwt = create_session_token(github_user.id, github_user.github_user_id)
    logger.info(f"✓ Session token created: {session_jwt[:50]}...")
    
    user_json = {
        'id': github_user.id,
        'github_user_id': github_user.github_user_id,
        'login': github_user.login,
        'name': github_user.name,
        'email': github_user.email,
        'avatar_url': github_user.avatar_url
    }
    
    logger.info(f"Preparing HTML redirect to: {FRONTEND_URL}/app/repos")
    
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
            console.log('OAuth callback: Storing auth data');
            try {{
                localStorage.setItem('auth_token', '{session_jwt}');
                localStorage.setItem('user', '{user_json_str}');
                console.log('OAuth callback: Token stored');
                console.log('OAuth callback: Redirecting to {FRONTEND_URL}/app/repos');
                setTimeout(function() {{ window.location.href = '{FRONTEND_URL}/app/repos'; }}, 500);
            }} catch(e) {{
                console.error('OAuth callback error:', e);
                alert('Failed to complete sign-in. Error: ' + e.message);
            }}
        </script>
    </body>
    </html>
    """
    
    logger.info("=== OAuth callback complete - returning HTML redirect ===")
    
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content)
