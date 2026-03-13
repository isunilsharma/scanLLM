"""Organization and team management models"""
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from core.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    github_org_id = Column(String, unique=True, nullable=True)
    github_org_login = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    members = relationship("Membership", back_populates="organization", cascade="all, delete-orphan")


class Membership(Base):
    __tablename__ = "memberships"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    user_id = Column(String, ForeignKey("github_users.id"), nullable=False)
    role = Column(String, default="member", nullable=False)  # owner, admin, member, viewer
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    organization = relationship("Organization", back_populates="members")
