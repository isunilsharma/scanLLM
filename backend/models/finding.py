from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
import uuid
from core.database import Base

class Finding(Base):
    __tablename__ = "findings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scan_id = Column(String, ForeignKey('scan_jobs.id'), nullable=False)
    file_path = Column(String, nullable=False)
    line_number = Column(Integer, nullable=False)
    line_text = Column(Text, nullable=False)
    framework = Column(String, nullable=False)
    pattern_name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
