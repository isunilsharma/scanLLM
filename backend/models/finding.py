from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Float, Boolean
from sqlalchemy.sql import func
import uuid
from core.database import Base

class Finding(Base):
    __tablename__ = "findings"
    
    # Original fields
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scan_id = Column(String, ForeignKey('scan_jobs.id'), nullable=False)
    file_path = Column(String, nullable=False)
    line_number = Column(Integer, nullable=False)
    line_text = Column(Text, nullable=False)
    framework = Column(String, nullable=False)
    pattern_name = Column(String, nullable=False)
    
    # Enhanced fields v1
    pattern_category = Column(String, nullable=True)
    pattern_severity = Column(String, nullable=True)
    pattern_description = Column(Text, nullable=True)
    snippet = Column(Text, nullable=True)
    
    # Contract extraction v2
    model_name = Column(String, nullable=True)
    temperature = Column(Float, nullable=True)
    max_tokens = Column(Integer, nullable=True)
    is_streaming = Column(Boolean, nullable=True)
    has_tools = Column(Boolean, nullable=True)
    
    # Ownership mapping v2
    owner_name = Column(String, nullable=True)
    owner_email = Column(String, nullable=True)
    owner_committed_at = Column(DateTime, nullable=True)

    # v3 fields - component classification, OWASP mapping
    component_type = Column(String, nullable=True)  # llm_provider, vector_db, orchestration_framework, agent_tool, etc.
    provider = Column(String, nullable=True)  # openai, anthropic, google, etc.
    owasp_id = Column(String, nullable=True)  # LLM01, LLM05, LLM06, etc.

    created_at = Column(DateTime(timezone=True), server_default=func.now())
