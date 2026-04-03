"""
Policy model for storing user-defined governance policies.

Each policy belongs to a GitHub user and contains a set of rules
that can be evaluated against scan findings.
"""
import uuid

from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func

from core.database import Base


class Policy(Base):
    __tablename__ = "policies"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    github_user_id = Column(String, ForeignKey("github_users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    rules_json = Column(Text, nullable=False, default="[]")  # JSON-encoded rules array
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
