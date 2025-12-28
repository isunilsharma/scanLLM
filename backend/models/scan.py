from sqlalchemy import Column, String, Integer, DateTime, Text, Enum as SQLEnum
from sqlalchemy.sql import func
import uuid
import enum
from core.database import Base

class ScanStatus(enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class ScanJob(Base):
    __tablename__ = "scan_jobs"
    
    # Original fields
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    repo_url = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(SQLEnum(ScanStatus), default=ScanStatus.PENDING, nullable=False)
    error_message = Column(Text, nullable=True)
    total_occurrences = Column(Integer, default=0)
    files_count = Column(Integer, default=0)
    
    # Enhanced fields v2
    total_matches = Column(Integer, default=0)
    ai_files_count = Column(Integer, default=0)
    frameworks_json = Column(Text, nullable=True)  # JSON string
    risk_flags_json = Column(Text, nullable=True)  # JSON string
    policies_result_json = Column(Text, nullable=True)  # JSON string
    summary_json = Column(Text, nullable=True)  # JSON string
    
    # GitHub OAuth fields
    github_user_id = Column(String, nullable=True)
    repo_owner = Column(String, nullable=True)
    repo_name = Column(String, nullable=True)
    repo_private = Column(Integer, default=0)
    source = Column(String, default='public_url')
