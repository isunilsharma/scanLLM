"""
Audit service — centralized helper for recording audit events.

Usage from any endpoint:
    await AuditService.log(
        db=db,
        user_id=current_user.id,
        org_id=org.id,
        action=AuditAction.SCAN_CREATED,
        resource_type=AuditResourceType.SCAN,
        resource_id=scan_job.id,
        metadata={"repo_url": "https://github.com/..."},
        request=request,
    )
"""
import json
import logging
from typing import Any, Dict, Optional

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.audit_log import AuditAction, AuditLog, AuditResourceType

logger = logging.getLogger(__name__)


class AuditService:
    """Static helper for writing audit log entries."""

    @staticmethod
    async def log(
        db: Session,
        user_id: Optional[str],
        org_id: Optional[str],
        action: AuditAction,
        resource_type: AuditResourceType,
        resource_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
    ) -> AuditLog:
        """Record an audit event. Call this from other endpoints."""
        ip_address: Optional[str] = None
        user_agent: Optional[str] = None

        if request is not None:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")

        entry = AuditLog(
            user_id=user_id,
            organization_id=org_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata_json=json.dumps(metadata) if metadata else None,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        try:
            db.add(entry)
            db.commit()
            db.refresh(entry)
            logger.info(
                "Audit event: action=%s resource_type=%s resource_id=%s user=%s",
                action.value,
                resource_type.value,
                resource_id,
                user_id,
            )
        except Exception as exc:
            db.rollback()
            logger.error("Failed to record audit event: %s", exc)
            raise

        return entry
