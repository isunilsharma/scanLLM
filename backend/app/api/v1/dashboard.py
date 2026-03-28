"""
Multi-repo Dashboard API — /api/v1/dashboard

Org-wide AI inventory, trends, and compliance overview.
"""
import sys
import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session

# Ensure backend root is importable
_backend_dir = str(Path(__file__).parent.parent.parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from core.database import get_db
from models.scan import ScanJob, ScanStatus
from models.finding import Finding

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic response models
# ---------------------------------------------------------------------------

class ProviderStat(BaseModel):
    provider: str
    count: int


class OverviewResponse(BaseModel):
    total_repos_scanned: int = 0
    total_findings: int = 0
    avg_risk_score: Optional[float] = None
    top_providers: List[ProviderStat] = []
    total_ai_components: int = 0


class RepoSummary(BaseModel):
    repo_url: str
    repo_owner: Optional[str] = None
    repo_name: Optional[str] = None
    latest_scan_id: Optional[str] = None
    risk_score: Optional[float] = None
    grade: Optional[str] = None
    findings_count: int = 0
    last_scanned: Optional[str] = None


class ReposResponse(BaseModel):
    repos: List[RepoSummary]
    total: int


class TrendPoint(BaseModel):
    week: str  # ISO date of week start
    avg_risk_score: Optional[float] = None
    total_findings: int = 0
    scans_count: int = 0


class TrendsResponse(BaseModel):
    trends: List[TrendPoint]


class ProviderRepo(BaseModel):
    provider: str
    repos: List[str]
    total_occurrences: int = 0


class ProvidersResponse(BaseModel):
    providers: List[ProviderRepo]


class ComplianceResponse(BaseModel):
    total_repos: int = 0
    repos_with_critical_findings: int = 0
    repos_with_aibom: int = 0
    aibom_coverage_pct: float = 0.0
    policy_pass_rate: Optional[float] = None
    repos_by_grade: Dict[str, int] = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _score_to_grade(score: float) -> str:
    """Convert a 0-100 risk score to a letter grade (A=best, F=worst)."""
    if score <= 20:
        return "A"
    elif score <= 40:
        return "B"
    elif score <= 60:
        return "C"
    elif score <= 80:
        return "D"
    return "F"


def _parse_risk_score(risk_score_json: Optional[str]) -> Optional[float]:
    """Extract overall_score from the risk_score JSON column."""
    if not risk_score_json:
        return None
    try:
        data = json.loads(risk_score_json)
        return data.get("overall_score")
    except (json.JSONDecodeError, TypeError):
        return None


def _get_latest_scans_per_repo(db: Session) -> List[ScanJob]:
    """Return the most recent successful scan for each unique repo_url."""
    # Subquery: max created_at per repo_url among successful scans
    subq = (
        db.query(
            ScanJob.repo_url,
            sa_func.max(ScanJob.created_at).label("max_created"),
        )
        .filter(ScanJob.status == ScanStatus.SUCCESS)
        .group_by(ScanJob.repo_url)
        .subquery()
    )

    scans = (
        db.query(ScanJob)
        .join(
            subq,
            (ScanJob.repo_url == subq.c.repo_url)
            & (ScanJob.created_at == subq.c.max_created),
        )
        .filter(ScanJob.status == ScanStatus.SUCCESS)
        .all()
    )
    return scans


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/overview", response_model=OverviewResponse)
async def dashboard_overview(db: Session = Depends(get_db)):
    """Org-wide stats: total repos, findings, avg risk score, top providers, total AI components."""
    latest_scans = _get_latest_scans_per_repo(db)

    if not latest_scans:
        return OverviewResponse()

    total_repos = len(latest_scans)
    scan_ids = [s.id for s in latest_scans]

    # Total findings across latest scans
    total_findings = (
        db.query(sa_func.count(Finding.id))
        .filter(Finding.scan_id.in_(scan_ids))
        .scalar()
        or 0
    )

    # Average risk score
    risk_scores = [_parse_risk_score(s.risk_score_json) for s in latest_scans]
    valid_scores = [s for s in risk_scores if s is not None]
    avg_risk = round(sum(valid_scores) / len(valid_scores), 1) if valid_scores else None

    # Top providers
    provider_counts = (
        db.query(Finding.provider, sa_func.count(Finding.id))
        .filter(Finding.scan_id.in_(scan_ids), Finding.provider.isnot(None))
        .group_by(Finding.provider)
        .order_by(sa_func.count(Finding.id).desc())
        .limit(10)
        .all()
    )
    top_providers = [ProviderStat(provider=p, count=c) for p, c in provider_counts]

    # Total AI components (distinct component_type + provider combos)
    total_components = (
        db.query(sa_func.count(sa_func.distinct(Finding.provider)))
        .filter(Finding.scan_id.in_(scan_ids), Finding.provider.isnot(None))
        .scalar()
        or 0
    )

    return OverviewResponse(
        total_repos_scanned=total_repos,
        total_findings=total_findings,
        avg_risk_score=avg_risk,
        top_providers=top_providers,
        total_ai_components=total_components,
    )


@router.get("/repos", response_model=ReposResponse)
async def dashboard_repos(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List all repos with their latest scan summary."""
    latest_scans = _get_latest_scans_per_repo(db)

    # Sort by last scanned descending
    latest_scans.sort(key=lambda s: s.created_at or datetime.min, reverse=True)

    total = len(latest_scans)
    page = latest_scans[offset : offset + limit]

    repos = []
    for scan in page:
        risk_val = _parse_risk_score(scan.risk_score_json)
        grade = _score_to_grade(risk_val) if risk_val is not None else None

        findings_count = (
            db.query(sa_func.count(Finding.id))
            .filter(Finding.scan_id == scan.id)
            .scalar()
            or 0
        )

        repos.append(
            RepoSummary(
                repo_url=scan.repo_url,
                repo_owner=scan.repo_owner,
                repo_name=scan.repo_name,
                latest_scan_id=scan.id,
                risk_score=risk_val,
                grade=grade,
                findings_count=findings_count,
                last_scanned=scan.created_at.isoformat() if scan.created_at else None,
            )
        )

    return ReposResponse(repos=repos, total=total)


@router.get("/trends", response_model=TrendsResponse)
async def dashboard_trends(
    days: int = Query(30, ge=7, le=90, description="Number of days to look back"),
    db: Session = Depends(get_db),
):
    """Risk score trend over time across all repos (weekly aggregation)."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    scans = (
        db.query(ScanJob)
        .filter(ScanJob.status == ScanStatus.SUCCESS, ScanJob.created_at >= cutoff)
        .order_by(ScanJob.created_at.asc())
        .all()
    )

    if not scans:
        return TrendsResponse(trends=[])

    # Group by ISO week
    weekly: Dict[str, List[ScanJob]] = defaultdict(list)
    for scan in scans:
        if scan.created_at:
            # Week start (Monday)
            week_start = scan.created_at - timedelta(days=scan.created_at.weekday())
            week_key = week_start.strftime("%Y-%m-%d")
            weekly[week_key].append(scan)

    trends = []
    for week_key in sorted(weekly.keys()):
        week_scans = weekly[week_key]
        risk_scores = [_parse_risk_score(s.risk_score_json) for s in week_scans]
        valid_scores = [s for s in risk_scores if s is not None]

        scan_ids = [s.id for s in week_scans]
        total_findings = (
            db.query(sa_func.count(Finding.id))
            .filter(Finding.scan_id.in_(scan_ids))
            .scalar()
            or 0
        )

        trends.append(
            TrendPoint(
                week=week_key,
                avg_risk_score=round(sum(valid_scores) / len(valid_scores), 1) if valid_scores else None,
                total_findings=total_findings,
                scans_count=len(week_scans),
            )
        )

    return TrendsResponse(trends=trends)


@router.get("/providers", response_model=ProvidersResponse)
async def dashboard_providers(db: Session = Depends(get_db)):
    """Provider distribution across org: which repos use which AI providers."""
    latest_scans = _get_latest_scans_per_repo(db)

    if not latest_scans:
        return ProvidersResponse(providers=[])

    scan_id_to_repo: Dict[str, str] = {s.id: s.repo_url for s in latest_scans}
    scan_ids = list(scan_id_to_repo.keys())

    # Query all findings with providers for these scans
    rows = (
        db.query(Finding.scan_id, Finding.provider, sa_func.count(Finding.id))
        .filter(Finding.scan_id.in_(scan_ids), Finding.provider.isnot(None))
        .group_by(Finding.scan_id, Finding.provider)
        .all()
    )

    # Aggregate: provider -> {repos, total_occurrences}
    provider_map: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"repos": set(), "total": 0}
    )
    for scan_id, provider, count in rows:
        repo_url = scan_id_to_repo.get(scan_id, "unknown")
        provider_map[provider]["repos"].add(repo_url)
        provider_map[provider]["total"] += count

    providers = []
    for provider, data in sorted(provider_map.items(), key=lambda x: x[1]["total"], reverse=True):
        providers.append(
            ProviderRepo(
                provider=provider,
                repos=sorted(data["repos"]),
                total_occurrences=data["total"],
            )
        )

    return ProvidersResponse(providers=providers)


@router.get("/compliance", response_model=ComplianceResponse)
async def dashboard_compliance(db: Session = Depends(get_db)):
    """Org-wide compliance status: policy pass rate, critical findings, AI-BOM coverage."""
    latest_scans = _get_latest_scans_per_repo(db)

    if not latest_scans:
        return ComplianceResponse()

    total_repos = len(latest_scans)
    repos_with_critical = 0
    repos_with_aibom = 0
    policy_passes = 0
    policy_total = 0
    grade_counts: Dict[str, int] = defaultdict(int)

    for scan in latest_scans:
        # Check for critical findings
        critical_count = (
            db.query(sa_func.count(Finding.id))
            .filter(
                Finding.scan_id == scan.id,
                Finding.pattern_severity == "critical",
            )
            .scalar()
            or 0
        )
        if critical_count > 0:
            repos_with_critical += 1

        # Grade distribution
        risk_val = _parse_risk_score(scan.risk_score_json)
        if risk_val is not None:
            grade = _score_to_grade(risk_val)
            grade_counts[grade] += 1

        # AI-BOM coverage: check if graph_json exists (indicates full scan with component data)
        if scan.graph_json:
            repos_with_aibom += 1

        # Policy pass rate from policies_result_json
        if scan.policies_result_json:
            try:
                policies = json.loads(scan.policies_result_json)
                if isinstance(policies, dict):
                    passed = policies.get("passed", policies.get("pass", None))
                    if passed is not None:
                        policy_total += 1
                        if passed:
                            policy_passes += 1
            except (json.JSONDecodeError, TypeError):
                pass

    aibom_coverage = round((repos_with_aibom / total_repos) * 100, 1) if total_repos > 0 else 0.0
    policy_pass_rate = round((policy_passes / policy_total) * 100, 1) if policy_total > 0 else None

    return ComplianceResponse(
        total_repos=total_repos,
        repos_with_critical_findings=repos_with_critical,
        repos_with_aibom=repos_with_aibom,
        aibom_coverage_pct=aibom_coverage,
        policy_pass_rate=policy_pass_rate,
        repos_by_grade=dict(grade_counts),
    )
