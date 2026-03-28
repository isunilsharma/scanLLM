"""AI model cost estimation engine."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

MODEL_PRICING: dict[str, dict[str, float]] = {
    # OpenAI
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "gpt-4": {"input": 30.00, "output": 60.00},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    "o1": {"input": 15.00, "output": 60.00},
    "o1-mini": {"input": 3.00, "output": 12.00},
    "o3": {"input": 10.00, "output": 40.00},
    "o3-mini": {"input": 1.10, "output": 4.40},
    "o4-mini": {"input": 1.10, "output": 4.40},
    # Anthropic
    "claude-opus-4-20250514": {"input": 15.00, "output": 75.00},
    "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
    "claude-haiku-4-5-20251001": {"input": 0.25, "output": 1.25},
    # Google
    "gemini-2.5-pro": {"input": 1.25, "output": 10.00},
    "gemini-2.5-flash": {"input": 0.15, "output": 0.60},
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    # Meta (self-hosted, $0)
    "llama-3.1-405b": {"input": 0.00, "output": 0.00},
    "llama-3.1-70b": {"input": 0.00, "output": 0.00},
    "llama-3.1-8b": {"input": 0.00, "output": 0.00},
    # Mistral
    "mistral-large": {"input": 2.00, "output": 6.00},
    "mistral-small": {"input": 0.20, "output": 0.60},
    "mistral-nemo": {"input": 0.15, "output": 0.15},
    # Cohere
    "command-r-plus": {"input": 2.50, "output": 10.00},
    "command-r": {"input": 0.15, "output": 0.60},
}

CHEAPER_ALTERNATIVES: dict[str, list[str]] = {
    "gpt-4o": ["gpt-4o-mini", "gemini-2.5-flash"],
    "gpt-4-turbo": ["gpt-4o", "gpt-4o-mini"],
    "gpt-4": ["gpt-4o", "gpt-4o-mini"],
    "claude-opus-4-20250514": ["claude-sonnet-4-20250514", "claude-haiku-4-5-20251001"],
    "claude-sonnet-4-20250514": ["claude-haiku-4-5-20251001", "gpt-4o-mini"],
    "gemini-1.5-pro": ["gemini-2.5-flash", "gemini-2.0-flash"],
    "o1": ["o3-mini", "gpt-4o"],
    "mistral-large": ["mistral-small", "mistral-nemo"],
    "command-r-plus": ["command-r"],
}

@dataclass
class ModelUsage:
    model_name: str
    provider: str
    files: list[str] = field(default_factory=list)
    call_count: int = 0
    has_max_tokens: bool = True
    input_price_per_1m: float = 0.0
    output_price_per_1m: float = 0.0
    cheaper_alternatives: list[str] = field(default_factory=list)
    cost_tier: str = "unknown"  # "free", "low", "medium", "high", "very_high"

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "provider": self.provider,
            "files": self.files,
            "call_count": self.call_count,
            "has_max_tokens": self.has_max_tokens,
            "input_price_per_1m": self.input_price_per_1m,
            "output_price_per_1m": self.output_price_per_1m,
            "cheaper_alternatives": self.cheaper_alternatives,
            "cost_tier": self.cost_tier,
        }

@dataclass
class CostEstimate:
    models: list[ModelUsage] = field(default_factory=list)
    total_models_detected: int = 0
    unbounded_cost_risks: int = 0  # calls without max_tokens
    provider_breakdown: dict[str, int] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    estimated_monthly_range: dict[str, float] = field(default_factory=dict)  # {"low": X, "high": Y}

    def to_dict(self) -> dict[str, Any]:
        return {
            "models": [m.to_dict() for m in self.models],
            "total_models_detected": self.total_models_detected,
            "unbounded_cost_risks": self.unbounded_cost_risks,
            "provider_breakdown": self.provider_breakdown,
            "recommendations": self.recommendations,
            "estimated_monthly_range": self.estimated_monthly_range,
        }

class CostEstimator:
    """Estimate AI costs from scan findings."""

    def estimate(self, findings: list[dict[str, Any]]) -> CostEstimate:
        """Analyze findings to produce cost estimates."""
        # Extract model usage from findings
        model_map: dict[str, ModelUsage] = {}
        unbounded = 0

        for finding in findings:
            model_name = self._extract_model_name(finding)
            if not model_name:
                continue

            provider = finding.get("provider", "unknown")
            file_path = finding.get("file_path", "")
            has_max_tokens = finding.get("has_max_tokens", True)

            if model_name not in model_map:
                pricing = MODEL_PRICING.get(model_name, {})
                alternatives = CHEAPER_ALTERNATIVES.get(model_name, [])
                input_price = pricing.get("input", 0.0)
                output_price = pricing.get("output", 0.0)
                avg_price = (input_price + output_price) / 2

                if avg_price == 0:
                    tier = "free"
                elif avg_price < 1.0:
                    tier = "low"
                elif avg_price < 5.0:
                    tier = "medium"
                elif avg_price < 20.0:
                    tier = "high"
                else:
                    tier = "very_high"

                model_map[model_name] = ModelUsage(
                    model_name=model_name,
                    provider=provider,
                    input_price_per_1m=input_price,
                    output_price_per_1m=output_price,
                    cheaper_alternatives=alternatives,
                    cost_tier=tier,
                )

            usage = model_map[model_name]
            if file_path and file_path not in usage.files:
                usage.files.append(file_path)
            usage.call_count += 1

            if not has_max_tokens:
                usage.has_max_tokens = False
                unbounded += 1

        models = sorted(model_map.values(), key=lambda m: m.output_price_per_1m, reverse=True)

        # Provider breakdown
        provider_counts: dict[str, int] = {}
        for m in models:
            provider_counts[m.provider] = provider_counts.get(m.provider, 0) + m.call_count

        # Recommendations
        recs: list[str] = []
        for m in models:
            if m.cheaper_alternatives:
                alt = m.cheaper_alternatives[0]
                alt_pricing = MODEL_PRICING.get(alt, {})
                if alt_pricing:
                    savings = ((m.output_price_per_1m - alt_pricing.get("output", 0)) / m.output_price_per_1m * 100) if m.output_price_per_1m > 0 else 0
                    if savings > 20:
                        recs.append(f"Consider {alt} instead of {m.model_name} — up to {savings:.0f}% cheaper")
            if not m.has_max_tokens:
                recs.append(f"Add max_tokens to {m.model_name} calls — unbounded token usage is a cost risk")

        # Estimated monthly range (very rough — assumes 1000-10000 calls/month per model)
        low_est = sum(m.input_price_per_1m * 0.001 * 1000 for m in models)  # 1K tokens * 1K calls
        high_est = sum(m.output_price_per_1m * 0.004 * 10000 for m in models)  # 4K tokens * 10K calls

        return CostEstimate(
            models=models,
            total_models_detected=len(models),
            unbounded_cost_risks=unbounded,
            provider_breakdown=provider_counts,
            recommendations=recs,
            estimated_monthly_range={"low": round(low_est, 2), "high": round(high_est, 2)},
        )

    def _extract_model_name(self, finding: dict[str, Any]) -> str | None:
        """Try to extract a model name from a finding."""
        # Check direct model_name field
        model = finding.get("model_name")
        if model and model in MODEL_PRICING:
            return model

        # Check matched_value for model names
        matched = finding.get("matched_value", "") or finding.get("matched_text", "")
        if matched:
            for known_model in MODEL_PRICING:
                if known_model in matched.lower():
                    return known_model

        # Check pattern metadata
        metadata = finding.get("metadata", {})
        if isinstance(metadata, dict):
            model = metadata.get("model")
            if model and model in MODEL_PRICING:
                return model

        return None
