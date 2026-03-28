"""
Cost Insights API — /api/v1/cost

Estimate AI costs based on scan findings, flag unbounded cost risks,
and suggest cheaper alternatives.
"""
import sys
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
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
# Model pricing data (per 1M tokens, USD)
# ---------------------------------------------------------------------------

MODEL_PRICING: Dict[str, Dict[str, float]] = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
    "claude-haiku-4-5-20251001": {"input": 0.25, "output": 1.25},
    "claude-opus-4-20250514": {"input": 15.00, "output": 75.00},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "llama-3.1-70b": {"input": 0.00, "output": 0.00},
    "llama-3.1-8b": {"input": 0.00, "output": 0.00},
    "mistral-large": {"input": 2.00, "output": 6.00},
    "command-r-plus": {"input": 2.50, "output": 10.00},
}

# Cheaper alternatives mapping: model -> list of cheaper alternatives
CHEAPER_ALTERNATIVES: Dict[str, List[str]] = {
    "gpt-4-turbo": ["gpt-4o", "gpt-4o-mini"],
    "gpt-4o": ["gpt-4o-mini"],
    "claude-opus-4-20250514": ["claude-sonnet-4-20250514", "claude-haiku-4-5-20251001"],
    "claude-sonnet-4-20250514": ["claude-haiku-4-5-20251001"],
    "gemini-1.5-pro": ["gemini-1.5-flash"],
    "mistral-large": ["llama-3.1-70b"],
    "command-r-plus": ["llama-3.1-70b"],
}


# ---------------------------------------------------------------------------
# Pydantic response models
# ---------------------------------------------------------------------------

class ModelCostBreakdown(BaseModel):
    model: str
    occurrences: int = 0
    pricing_per_1m_input: Optional[float] = None
    pricing_per_1m_output: Optional[float] = None
    has_max_tokens: bool = True
    unbounded_calls: int = 0
    estimated_monthly_cost_low: Optional[float] = None
    estimated_monthly_cost_high: Optional[float] = None


class CostRecommendation(BaseModel):
    type: str  # "cheaper_alternative", "unbounded_cost", "self_hosted"
    severity: str  # "info", "warning", "critical"
    message: str
    current_model: Optional[str] = None
    suggested_model: Optional[str] = None
    potential_savings_pct: Optional[float] = None


class CostEstimateResponse(BaseModel):
    scan_id: str
    repo_url: str
    models_detected: List[ModelCostBreakdown]
    total_estimated_monthly_low: float = 0.0
    total_estimated_monthly_high: float = 0.0
    recommendations: List[CostRecommendation]
    unknown_models: List[str] = []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _estimate_monthly_cost(
    pricing: Dict[str, float],
    occurrences: int,
) -> tuple[float, float]:
    """
    Estimate monthly cost range for a model.

    Assumptions for estimation:
    - Low estimate: 100 calls/day, 500 input tokens, 200 output tokens per call
    - High estimate: 1000 calls/day, 2000 input tokens, 1000 output tokens per call
    - Scale by number of call sites (occurrences) as a rough proxy
    """
    input_price = pricing.get("input", 0)
    output_price = pricing.get("output", 0)

    # Low estimate: 100 calls/day * 30 days
    low_calls = 100 * 30 * max(1, occurrences)
    low_input_tokens = low_calls * 500 / 1_000_000
    low_output_tokens = low_calls * 200 / 1_000_000
    low_cost = (low_input_tokens * input_price) + (low_output_tokens * output_price)

    # High estimate: 1000 calls/day * 30 days
    high_calls = 1000 * 30 * max(1, occurrences)
    high_input_tokens = high_calls * 2000 / 1_000_000
    high_output_tokens = high_calls * 1000 / 1_000_000
    high_cost = (high_input_tokens * input_price) + (high_output_tokens * output_price)

    return round(low_cost, 2), round(high_cost, 2)


def _find_model_match(model_name: str) -> Optional[str]:
    """Try to match a model name to our pricing table (fuzzy)."""
    if not model_name:
        return None

    lower = model_name.lower().strip()

    # Exact match
    if lower in MODEL_PRICING:
        return lower

    # Try partial matching
    for key in MODEL_PRICING:
        if key in lower or lower in key:
            return key

    return None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/estimate", response_model=CostEstimateResponse)
async def estimate_costs(
    scan_id: str = Query(..., description="Scan ID to estimate costs for"),
    db: Session = Depends(get_db),
):
    """
    Estimate AI costs based on scan findings.

    Detects which models are used, looks up pricing, flags unbounded cost risks,
    and suggests cheaper alternatives.
    """
    scan_job = db.query(ScanJob).filter(ScanJob.id == scan_id).first()
    if not scan_job:
        raise HTTPException(status_code=404, detail="Scan not found")

    if scan_job.status != ScanStatus.SUCCESS:
        raise HTTPException(status_code=400, detail="Scan has not completed successfully")

    # Fetch findings with model information
    findings = db.query(Finding).filter(Finding.scan_id == scan_id).all()

    # Aggregate by model
    model_data: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"occurrences": 0, "unbounded": 0}
    )
    unknown_models: set = set()

    for f in findings:
        if not f.model_name:
            continue

        matched = _find_model_match(f.model_name)
        if matched:
            model_data[matched]["occurrences"] += 1
            if f.max_tokens is None:
                model_data[matched]["unbounded"] += 1
        else:
            unknown_models.add(f.model_name)

    # Build model cost breakdowns
    models_detected: List[ModelCostBreakdown] = []
    total_low = 0.0
    total_high = 0.0
    recommendations: List[CostRecommendation] = []

    for model, data in sorted(model_data.items()):
        pricing = MODEL_PRICING.get(model, {})
        has_max_tokens = data["unbounded"] == 0
        low, high = _estimate_monthly_cost(pricing, data["occurrences"])

        models_detected.append(
            ModelCostBreakdown(
                model=model,
                occurrences=data["occurrences"],
                pricing_per_1m_input=pricing.get("input"),
                pricing_per_1m_output=pricing.get("output"),
                has_max_tokens=has_max_tokens,
                unbounded_calls=data["unbounded"],
                estimated_monthly_cost_low=low,
                estimated_monthly_cost_high=high,
            )
        )

        total_low += low
        total_high += high

        # Recommendation: unbounded cost risk
        if data["unbounded"] > 0:
            recommendations.append(
                CostRecommendation(
                    type="unbounded_cost",
                    severity="warning",
                    message=(
                        f"{data['unbounded']} call(s) to {model} have no max_tokens set. "
                        f"This could lead to unexpectedly high costs. Add max_tokens to all LLM calls."
                    ),
                    current_model=model,
                )
            )

        # Recommendation: cheaper alternative
        if model in CHEAPER_ALTERNATIVES:
            for alt in CHEAPER_ALTERNATIVES[model]:
                alt_pricing = MODEL_PRICING.get(alt, {})
                if alt_pricing:
                    current_avg = (pricing.get("input", 0) + pricing.get("output", 0)) / 2
                    alt_avg = (alt_pricing.get("input", 0) + alt_pricing.get("output", 0)) / 2
                    if current_avg > 0:
                        savings = round((1 - alt_avg / current_avg) * 100, 0)
                    else:
                        savings = 0.0

                    recommendations.append(
                        CostRecommendation(
                            type="cheaper_alternative",
                            severity="info",
                            message=(
                                f"Consider using {alt} instead of {model} for non-critical tasks. "
                                f"Potential savings: ~{savings:.0f}%."
                            ),
                            current_model=model,
                            suggested_model=alt,
                            potential_savings_pct=savings,
                        )
                    )
                    break  # Only suggest the best alternative

    # Recommendation: self-hosted models
    if total_high > 500 and not any(
        m.model.startswith("llama") for m in models_detected
    ):
        recommendations.append(
            CostRecommendation(
                type="self_hosted",
                severity="info",
                message=(
                    "Your estimated monthly AI costs are significant. "
                    "Consider self-hosting open-source models (Llama 3.1, Mistral) "
                    "for non-sensitive workloads to reduce costs."
                ),
            )
        )

    return CostEstimateResponse(
        scan_id=scan_id,
        repo_url=scan_job.repo_url,
        models_detected=models_detected,
        total_estimated_monthly_low=round(total_low, 2),
        total_estimated_monthly_high=round(total_high, 2),
        recommendations=recommendations,
        unknown_models=sorted(unknown_models),
    )
