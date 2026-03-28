"""
Audit log API — /api/v1/audit

Paginated audit log with filters and internal logging endpoint.
"""
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Ensure backend root is importable
_backend_dir = str(Path(__file__).parent.parent.parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from core.database import get_db
from app.models.audit_log import AuditAction, AuditLog, AuditResourceType
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class AuditLogOut(BaseModel):
    id: str
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: Optional[str] = None


class AuditLogListResponse(BaseModel):
    logs: List[AuditLogOut]
    total: int
    limit: int
    offset: int


class AuditLogCreateRequest(BaseModel):
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    action: str  # Must match AuditAction enum value
    resource_type: str  # Must match AuditResourceType enum value
    resource_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AuditLogCreateResponse(BaseModel):
    id: str
    action: str
    resource_type: str
    created_at: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _audit_log_to_out(entry: AuditLog) -> AuditLogOut:
    """Convert an AuditLog ORM object to a response dict."""
    metadata_parsed = None
    if entry.metadata_json:
        try:
            metadata_parsed = json.loads(entry.metadata_json)
        except (json.JSONDecodeError, TypeError):
            metadata_parsed = {"raw": entry.metadata_json}

    return AuditLogOut(
        id=entry.id,
        user_id=entry.user_id,
        organization_id=entry.organization_id,
        action=entry.action.value if entry.action else None,
        resource_type=entry.resource_type.value if entry.resource_type else None,
        resource_id=entry.resource_id,
        metadata=metadata_parsed,
        ip_address=entry.ip_address,
        user_agent=entry.user_agent,
        created_at=entry.created_at.isoformat() if entry.created_at else None,
    )


def _parse_action(action_str: str) -> AuditAction:
    """Parse action string to enum, raise 400 on invalid."""
    try:
        return AuditAction(action_str)
    except ValueError:
        valid = [a.value for a in AuditAction]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action '{action_str}'. Valid actions: {valid}",
        )


def _parse_resource_type(rt_str: str) -> AuditResourceType:
    """Parse resource type string to enum, raise 400 on invalid."""
    try:
        return AuditResourceType(rt_str)
    except ValueError:
        valid = [r.value for r in AuditResourceType]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid resource_type '{rt_str}'. Valid types: {valid}",
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/logs", response_model=AuditLogListResponse)
async def list_audit_logs(
    action: Optional[str] = Query(None, description="Filter by action (e.g. scan_created)"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type (e.g. scan)"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    organization_id: Optional[str] = Query(None, description="Filter by organization ID"),
    date_from: Optional[str] = Query(None, description="Filter from date (ISO format)"),
    date_to: Optional[str] = Query(None, description="Filter to date (ISO format)"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Get paginated audit logs with optional filters."""
    query = db.query(AuditLog)

    if action:
        parsed_action = _parse_action(action)
        query = query.filter(AuditLog.action == parsed_action)

    if resource_type:
        parsed_rt = _parse_resource_type(resource_type)
        query = query.filter(AuditLog.resource_type == parsed_rt)

    if user_id:
        query = query.filter(AuditLog.user_id == user_id)

    if organization_id:
        query = query.filter(AuditLog.organization_id == organization_id)

    if date_from:
        try:
            dt_from = datetime.fromisoformat(date_from)
            query = query.filter(AuditLog.created_at >= dt_from)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_from format. Use ISO format.")

    if date_to:
        try:
            dt_to = datetime.fromisoformat(date_to)
            query = query.filter(AuditLog.created_at <= dt_to)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_to format. Use ISO format.")

    total = query.count()
    entries = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()

    logs = [_audit_log_to_out(e) for e in entries]
    return AuditLogListResponse(logs=logs, total=total, limit=limit, offset=offset)


@router.post("/log", response_model=AuditLogCreateResponse)
async def create_audit_log(
    body: AuditLogCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Record an audit event (internal endpoint, called by other services)."""
    parsed_action = _parse_action(body.action)
    parsed_rt = _parse_resource_type(body.resource_type)

    entry = await AuditService.log(
        db=db,
        user_id=body.user_id,
        org_id=body.organization_id,
        action=parsed_action,
        resource_type=parsed_rt,
        resource_id=body.resource_id,
        metadata=body.metadata,
        request=request,
    )

    return AuditLogCreateResponse(
        id=entry.id,
        action=entry.action.value,
        resource_type=entry.resource_type.value,
        created_at=entry.created_at.isoformat() if entry.created_at else None,
    )
