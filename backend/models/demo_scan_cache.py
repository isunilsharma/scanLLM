from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.sql import func
import uuid
from core.database import Base

class DemoScanCache(Base):
    __tablename__ = "demo_scan_cache"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    repo_url = Column(String, nullable=False)
    repo_owner = Column(String, nullable=True)
    repo_name = Column(String, nullable=True)
    scan_mode = Column(String, nullable=False)  # 'journal' or 'full'
    scan_version = Column(String, nullable=False)
    status = Column(String, nullable=False)  # 'COMPLETE' or 'ERROR'
    
    # Cached results
    scan_id = Column(String, nullable=False)  # Reference to actual scan_job
    result_payload_json = Column(Text, nullable=True)
    
    # Cache metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_refreshed_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    source = Column(String, default='demo_precomputed')
