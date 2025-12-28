from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.sql import func
import uuid
from core.database import Base

class GitHubToken(Base):
    __tablename__ = "github_tokens"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    github_user_id = Column(String, ForeignKey('github_users.id'), nullable=False)
    encrypted_token = Column(String, nullable=False)
    scope = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), onupdate=func.now())
