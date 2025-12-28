from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
import uuid
from core.database import Base

class GitHubUser(Base):
    __tablename__ = "github_users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    github_user_id = Column(String, unique=True, nullable=False)
    login = Column(String, nullable=False)
    name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
