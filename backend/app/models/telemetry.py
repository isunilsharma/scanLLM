"""
Telemetry and user feedback models.

Stores anonymous usage analytics and user-submitted feedback so admins
can query product health and user sentiment.
"""
from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from sqlalchemy.sql import func

# Ensure the backend root is on sys.path so core.database is importable
_backend_dir = str(Path(__file__).parent.parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from core.database import Base


class TelemetryEvent(Base):
    __tablename__ = "telemetry_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(50), nullable=False)       # "scan", "fix", "export", "score", "ui_view"
    command = Column(String(100))                          # Full command name
    scan_duration_ms = Column(Integer)                     # Duration in ms
    finding_count = Column(Integer)                        # Number of findings
    risk_score = Column(Integer)                           # 0-100
    python_version = Column(String(20))                    # "3.11.5"
    os_platform = Column(String(50))                       # "linux", "darwin", "win32"
    scanllm_version = Column(String(20))                   # "2.2.0"
    session_id = Column(String(64))                        # Anonymous UUID
    providers_detected = Column(Text, nullable=True)       # JSON list of provider names
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserFeedback(Base):
    __tablename__ = "user_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rating = Column(Integer)                               # 1-5 stars
    category = Column(String(50))                          # "bug", "feature", "general"
    message = Column(Text)                                 # Feedback text
    email = Column(String(255), nullable=True)             # Optional contact
    page = Column(String(100))                             # Which page/command triggered this
    scanllm_version = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
