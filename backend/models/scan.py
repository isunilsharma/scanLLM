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
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    repo_url = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(SQLEnum(ScanStatus), default=ScanStatus.PENDING, nullable=False)
    error_message = Column(Text, nullable=True)
    total_occurrences = Column(Integer, default=0)
    files_count = Column(Integer, default=0)
