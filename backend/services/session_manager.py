from jose import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

SESSION_SECRET = os.getenv('SESSION_SECRET')
if not SESSION_SECRET:
    import warnings
    warnings.warn("SESSION_SECRET not set - using insecure default. Set this in production!", stacklevel=2)
    SESSION_SECRET = 'dev-only-insecure-default'

ALGORITHM = "HS256"
EXPIRE_HOURS = 24 * 7  # 7 days

def create_session_token(user_id: str, github_user_id: str) -> str:
    expires = datetime.utcnow() + timedelta(hours=EXPIRE_HOURS)
    payload = {'user_id': user_id, 'github_user_id': github_user_id, 'exp': expires}
    return jwt.encode(payload, SESSION_SECRET, algorithm=ALGORITHM)

def verify_session_token(token: str):
    try:
        return jwt.decode(token, SESSION_SECRET, algorithms=[ALGORITHM])
    except jwt.JWTError:
        return None
