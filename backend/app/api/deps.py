"""
Shared FastAPI dependencies for the v1 API.

Usage:
    from app.api.deps import get_db, get_current_user, get_scan_or_404
"""
import sys
from pathlib import Path
from typing import Optional

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

_backend_dir = str(Path(__file__).parent.parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

# ---------------------------------------------------------------------------
# Database session
# ---------------------------------------------------------------------------
from core.database import get_db  # noqa: F401, E402

# ---------------------------------------------------------------------------
# Current user (GitHub OAuth)
# ---------------------------------------------------------------------------
from models.github_user import GitHubUser  # noqa: E402
from models.github_token import GitHubToken  # noqa: E402
from services.token_encryption import decrypt_token  # noqa: E402
from services.session_manager import verify_session_token  # noqa: E402


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> GitHubUser:
    """Extract and validate the current user from the Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.replace("Bearer ", "")
    payload = verify_session_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.query(GitHubUser).filter(GitHubUser.id == payload["user_id"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


def is_admin(user: GitHubUser, db: Session) -> bool:
    """Check if a user has admin/owner role via Membership or ADMIN_EMAILS config."""
    from app.config import get_admin_emails
    # Check config-based admin list first
    if user.email and user.email.lower() in get_admin_emails():
        return True
    # Check Membership table for admin/owner role
    try:
        from models.organization import Membership
        membership = (
            db.query(Membership)
            .filter(Membership.user_id == user.id, Membership.role.in_(["owner", "admin"]))
            .first()
        )
        return membership is not None
    except Exception:
        return False


def get_admin_user(
    user: GitHubUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GitHubUser:
    """Require the current user to be an admin. Raises 403 if not."""
    if not is_admin(user, db):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# ---------------------------------------------------------------------------
# Scan lookup helper
# ---------------------------------------------------------------------------
from models.scan import ScanJob  # noqa: E402


def get_scan_or_404(
    scan_id: str,
    db: Session = Depends(get_db),
) -> ScanJob:
    """Fetch a ScanJob by id or raise HTTP 404."""
    scan_job = db.query(ScanJob).filter(ScanJob.id == scan_id).first()
    if not scan_job:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan_job


# ---------------------------------------------------------------------------
# GitHub token helper
# ---------------------------------------------------------------------------

def get_github_token(user: GitHubUser, db: Session) -> str:
    """Retrieve and decrypt the GitHub token for the given user."""
    token_obj = (
        db.query(GitHubToken).filter(GitHubToken.github_user_id == user.id).first()
    )
    if not token_obj:
        raise HTTPException(status_code=401, detail="No GitHub token found")
    return decrypt_token(token_obj.encrypted_token)
