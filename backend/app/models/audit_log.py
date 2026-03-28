"""
Audit log model for enterprise audit trail.

Tracks all significant user actions for compliance and governance.
"""
import enum
import uuid

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func

from core.database import Base


class AuditAction(enum.Enum):
    SCAN_CREATED = "scan_created"
    POLICY_UPDATED = "policy_updated"
    REPORT_GENERATED = "report_generated"
    SETTINGS_CHANGED = "settings_changed"
    MEMBER_INVITED = "member_invited"
    REPO_ADDED = "repo_added"


class AuditResourceType(enum.Enum):
    SCAN = "scan"
    POLICY = "policy"
    REPORT = "report"
    REPO = "repo"
    ORG = "org"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("github_users.id"), nullable=True)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=True)
    action = Column(SQLEnum(AuditAction), nullable=False)
    resource_type = Column(SQLEnum(AuditResourceType), nullable=False)
    resource_id = Column(String, nullable=True)
    metadata_json = Column(Text, nullable=True)  # JSON string for flexible metadata
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
