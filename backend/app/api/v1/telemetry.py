"""
Telemetry and feedback API — /api/v1/telemetry

Records anonymous usage analytics and user feedback.
Admin endpoints expose aggregated stats and feedback listings.
"""
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session

# Ensure backend root is importable
_backend_dir = str(Path(__file__).parent.parent.parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from core.database import get_db
from app.models.telemetry import TelemetryEvent, UserFeedback

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class TelemetryEventCreate(BaseModel):
    event_type: str
    command: Optional[str] = None
    scan_duration_ms: Optional[int] = None
    finding_count: Optional[int] = None
    risk_score: Optional[int] = None
    python_version: Optional[str] = None
    os_platform: Optional[str] = None
    scanllm_version: Optional[str] = None
    session_id: Optional[str] = None


class TelemetryEventOut(BaseModel):
    id: int
    event_type: str
    command: Optional[str] = None
    scan_duration_ms: Optional[int] = None
    finding_count: Optional[int] = None
    risk_score: Optional[int] = None
    created_at: Optional[str] = None


class FeedbackCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    category: str = Field(pattern=r"^(bug|feature|general)$")
    message: str
    email: Optional[str] = None
    page: Optional[str] = None
    scanllm_version: Optional[str] = None


class FeedbackItem(BaseModel):
    id: int
    rating: int
    category: str
    message: str
    email: Optional[str] = None
    page: Optional[str] = None
    created_at: Optional[str] = None


class FeedbackListResponse(BaseModel):
    feedback: List[FeedbackItem]
    total: int


class CommandCount(BaseModel):
    command: Optional[str]
    count: int


class DayCount(BaseModel):
    date: str
    count: int


class TelemetryStats(BaseModel):
    total_events: int
    total_scans: int
    avg_risk_score: Optional[float] = None
    avg_scan_duration_ms: Optional[float] = None
    top_commands: List[CommandCount]
    events_by_day: List[DayCount]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/events")
async def record_event(
    event: TelemetryEventCreate,
    db: Session = Depends(get_db),
):
    """Record an anonymous telemetry event. No auth required."""
    entry = TelemetryEvent(
        event_type=event.event_type,
        command=event.command,
        scan_duration_ms=event.scan_duration_ms,
        finding_count=event.finding_count,
        risk_score=event.risk_score,
        python_version=event.python_version,
        os_platform=event.os_platform,
        scanllm_version=event.scanllm_version,
        session_id=event.session_id,
    )
    db.add(entry)
    db.commit()
    logger.info("Telemetry event recorded: %s", event.event_type)
    return {"status": "ok"}


@router.post("/feedback")
async def submit_feedback(
    feedback: FeedbackCreate,
    db: Session = Depends(get_db),
):
    """Submit user feedback. No auth required."""
    entry = UserFeedback(
        rating=feedback.rating,
        category=feedback.category,
        message=feedback.message,
        email=feedback.email,
        page=feedback.page,
        scanllm_version=feedback.scanllm_version,
    )
    db.add(entry)
    db.commit()
    logger.info("Feedback submitted: category=%s rating=%s", feedback.category, feedback.rating)
    return {"status": "ok", "message": "Thanks for your feedback!"}


@router.get("/stats", response_model=TelemetryStats)
async def get_telemetry_stats(
    db: Session = Depends(get_db),
):
    """Get aggregated telemetry statistics. For admin use."""
    total_events = db.query(sa_func.count(TelemetryEvent.id)).scalar() or 0
    total_scans = (
        db.query(sa_func.count(TelemetryEvent.id))
        .filter(TelemetryEvent.event_type == "scan")
        .scalar()
        or 0
    )
    avg_risk = (
        db.query(sa_func.avg(TelemetryEvent.risk_score))
        .filter(TelemetryEvent.risk_score.isnot(None))
        .scalar()
    )
    avg_duration = (
        db.query(sa_func.avg(TelemetryEvent.scan_duration_ms))
        .filter(TelemetryEvent.scan_duration_ms.isnot(None))
        .scalar()
    )

    # Top commands (top 10)
    top_commands_rows = (
        db.query(TelemetryEvent.command, sa_func.count(TelemetryEvent.id).label("cnt"))
        .filter(TelemetryEvent.command.isnot(None))
        .group_by(TelemetryEvent.command)
        .order_by(sa_func.count(TelemetryEvent.id).desc())
        .limit(10)
        .all()
    )
    top_commands = [CommandCount(command=row[0], count=row[1]) for row in top_commands_rows]

    # Events by day (last 30 days)
    day_rows = (
        db.query(
            sa_func.date(TelemetryEvent.created_at).label("day"),
            sa_func.count(TelemetryEvent.id).label("cnt"),
        )
        .group_by(sa_func.date(TelemetryEvent.created_at))
        .order_by(sa_func.date(TelemetryEvent.created_at).desc())
        .limit(30)
        .all()
    )
    events_by_day = [
        DayCount(date=str(row[0]) if row[0] else "unknown", count=row[1])
        for row in day_rows
    ]

    return TelemetryStats(
        total_events=total_events,
        total_scans=total_scans,
        avg_risk_score=round(avg_risk, 1) if avg_risk is not None else None,
        avg_scan_duration_ms=round(avg_duration, 1) if avg_duration is not None else None,
        top_commands=top_commands,
        events_by_day=events_by_day,
    )


@router.get("/feedback", response_model=FeedbackListResponse)
async def list_feedback(
    limit: int = Query(50, ge=1, le=500),
    category: Optional[str] = Query(None, description="Filter by category (bug, feature, general)"),
    db: Session = Depends(get_db),
):
    """List user feedback. For admin use."""
    query = db.query(UserFeedback)

    if category:
        query = query.filter(UserFeedback.category == category)

    total = query.count()
    entries = query.order_by(UserFeedback.created_at.desc()).limit(limit).all()

    feedback = [
        FeedbackItem(
            id=e.id,
            rating=e.rating,
            category=e.category,
            message=e.message,
            email=e.email,
            page=e.page,
            created_at=e.created_at.isoformat() if e.created_at else None,
        )
        for e in entries
    ]
    return FeedbackListResponse(feedback=feedback, total=total)
