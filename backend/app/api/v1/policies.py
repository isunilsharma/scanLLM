"""
Policy management API — /api/v1/policies

CRUD endpoints for user-defined governance policies.
"""
import sys
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# Ensure backend root is importable
_backend_dir = str(Path(__file__).parent.parent.parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from core.database import get_db
from app.models.policy import Policy
from app.api.deps import get_current_user
from models.github_user import GitHubUser

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class PolicyRuleSchema(BaseModel):
    """Schema for a single policy rule within a policy."""
    id: Optional[str] = None
    name: str
    description: Optional[str] = ""
    severity: str = "warning"
    target: Optional[str] = "finding"
    type: Optional[str] = None
    conditions: List[Dict[str, Any]] = []


class PolicyCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = ""
    rules: List[Dict[str, Any]] = []
    is_active: bool = True


class PolicyUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    rules: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = None


class PolicyOut(BaseModel):
    id: str
    github_user_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    rules: List[Dict[str, Any]] = []
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class PolicyListResponse(BaseModel):
    policies: List[PolicyOut]
    total: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _policy_to_out(policy: Policy) -> PolicyOut:
    """Convert a Policy ORM object to a response schema."""
    rules = []
    if policy.rules_json:
        try:
            rules = json.loads(policy.rules_json)
        except (json.JSONDecodeError, TypeError):
            rules = []

    return PolicyOut(
        id=policy.id,
        github_user_id=str(policy.github_user_id) if policy.github_user_id else None,
        name=policy.name,
        description=policy.description,
        rules=rules,
        is_active=policy.is_active,
        created_at=policy.created_at.isoformat() if policy.created_at else None,
        updated_at=policy.updated_at.isoformat() if policy.updated_at else None,
    )


def _get_policy_or_404(
    policy_id: str,
    user: GitHubUser,
    db: Session,
) -> Policy:
    """Fetch a policy by ID, ensuring it belongs to the current user."""
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    if str(policy.github_user_id) != str(user.id):
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=PolicyListResponse)
async def list_policies(
    db: Session = Depends(get_db),
    user: GitHubUser = Depends(get_current_user),
):
    """List all policies belonging to the current user."""
    policies = (
        db.query(Policy)
        .filter(Policy.github_user_id == user.id)
        .order_by(Policy.created_at.desc())
        .all()
    )
    return PolicyListResponse(
        policies=[_policy_to_out(p) for p in policies],
        total=len(policies),
    )


@router.post("", response_model=PolicyOut, status_code=201)
async def create_policy(
    body: PolicyCreateRequest,
    db: Session = Depends(get_db),
    user: GitHubUser = Depends(get_current_user),
):
    """Create a new policy."""
    policy = Policy(
        github_user_id=user.id,
        name=body.name,
        description=body.description or "",
        rules_json=json.dumps(body.rules),
        is_active=body.is_active,
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    logger.info("Policy created: id=%s name=%s user=%s", policy.id, policy.name, user.id)
    return _policy_to_out(policy)


@router.post("/import", response_model=PolicyOut, status_code=201)
async def import_policy(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: GitHubUser = Depends(get_current_user),
):
    """Import a policy from a JSON file upload.

    Expected JSON format:
    {
        "name": "My Policy",
        "description": "...",
        "rules": [...]
    }
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Only JSON files are supported")

    try:
        content = await file.read()
        data = json.loads(content.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON file: {exc}")

    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="JSON must be an object with name, rules fields")

    name = data.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="JSON must contain a 'name' field")

    rules = data.get("rules", [])
    if not isinstance(rules, list):
        raise HTTPException(status_code=400, detail="'rules' must be an array")

    policy = Policy(
        github_user_id=user.id,
        name=name,
        description=data.get("description", ""),
        rules_json=json.dumps(rules),
        is_active=data.get("is_active", True),
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    logger.info(
        "Policy imported: id=%s name=%s user=%s file=%s",
        policy.id, policy.name, user.id, file.filename,
    )
    return _policy_to_out(policy)


@router.get("/{policy_id}", response_model=PolicyOut)
async def get_policy(
    policy_id: str,
    db: Session = Depends(get_db),
    user: GitHubUser = Depends(get_current_user),
):
    """Get a single policy by ID."""
    policy = _get_policy_or_404(policy_id, user, db)
    return _policy_to_out(policy)


@router.put("/{policy_id}", response_model=PolicyOut)
async def update_policy(
    policy_id: str,
    body: PolicyUpdateRequest,
    db: Session = Depends(get_db),
    user: GitHubUser = Depends(get_current_user),
):
    """Update an existing policy."""
    policy = _get_policy_or_404(policy_id, user, db)

    if body.name is not None:
        policy.name = body.name
    if body.description is not None:
        policy.description = body.description
    if body.rules is not None:
        policy.rules_json = json.dumps(body.rules)
    if body.is_active is not None:
        policy.is_active = body.is_active

    db.commit()
    db.refresh(policy)
    logger.info("Policy updated: id=%s name=%s user=%s", policy.id, policy.name, user.id)
    return _policy_to_out(policy)


@router.delete("/{policy_id}", status_code=204)
async def delete_policy(
    policy_id: str,
    db: Session = Depends(get_db),
    user: GitHubUser = Depends(get_current_user),
):
    """Delete a policy."""
    policy = _get_policy_or_404(policy_id, user, db)
    db.delete(policy)
    db.commit()
    logger.info("Policy deleted: id=%s user=%s", policy_id, user.id)
    return None
