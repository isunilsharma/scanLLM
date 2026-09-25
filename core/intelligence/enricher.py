"""
Scan Enricher — cross-references scan findings with the Model Risk
Intelligence Database to add risk profiles, OWASP ratings, and
mitigation recommendations to each finding.
"""

from __future__ import annotations

import logging
from typing import Any

from core.intelligence.model_risk_db import ModelRiskDB, ModelRiskProfile, OWASP_LABELS

logger = logging.getLogger(__name__)


class ScanEnricher:
    """Enriches scan findings with model risk intelligence data.

    For every finding that references a known model name, the enricher
    attaches the model's risk profile — OWASP risk ratings, composite
    risk index, license information, and recommended mitigations.

    Unknown models are flagged with ``"not_assessed": True`` so users
    know which models lack risk intelligence.

    Usage::

        enricher = ScanEnricher()
        enriched = enricher.enrich(findings)
    """

    def __init__(self, db: ModelRiskDB | None = None) -> None:
        self._db = db or ModelRiskDB()

    def enrich(self, findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Enrich a list of scan findings with model risk data.

        Each finding dict is mutated in place **and** returned.  A new
        key ``"model_risk"`` is added to findings that reference a model
        name.  The value is either the full risk profile dict or a
        ``not_assessed`` placeholder.

        Args:
            findings: List of finding dicts as produced by ``ScanEngine``.

        Returns:
            The same list (mutated) with ``model_risk`` added where applicable.
        """
        enriched_count = 0
        not_assessed_count = 0
        not_assessed_models: set[str] = set()

        for finding in findings:
            model_name = self._extract_model_name(finding)
            if not model_name:
                continue

            profile = self._db.lookup_fuzzy(model_name)

            if profile is not None:
                finding["model_risk"] = self._profile_to_enrichment(profile)
                enriched_count += 1
            else:
                finding["model_risk"] = {
                    "not_assessed": True,
                    "model_name": model_name,
                    "message": (
                        f"Model '{model_name}' is not in the ScanLLM risk database. "
                        "Risk profile unknown."
                    ),
                }
                not_assessed_models.add(model_name)
                not_assessed_count += 1

        logger.info(
            "Enriched %d findings with risk data; %d models not assessed (%s)",
            enriched_count,
            not_assessed_count,
            ", ".join(sorted(not_assessed_models)) if not_assessed_models else "none",
        )

        return findings

    def enrich_summary(self, findings: list[dict[str, Any]]) -> dict[str, Any]:
        """Return a summary of enrichment results.

        Call this after ``enrich()`` to get aggregate statistics.
        """
        enriched = 0
        not_assessed = 0
        models_found: dict[str, dict[str, Any]] = {}
        not_assessed_models: set[str] = set()

        for finding in findings:
            risk = finding.get("model_risk")
            if not risk:
                continue

            if risk.get("not_assessed"):
                not_assessed += 1
                not_assessed_models.add(risk.get("model_name", "unknown"))
            else:
                enriched += 1
                name = risk.get("name", "unknown")
                if name not in models_found:
                    models_found[name] = {
                        "provider": risk.get("provider", ""),
                        "risk_index": risk.get("risk_index", 0),
                        "risk_grade": risk.get("risk_grade", "?"),
                        "occurrence_count": 0,
                    }
                models_found[name]["occurrence_count"] += 1

        return {
            "enriched_findings": enriched,
            "not_assessed_findings": not_assessed,
            "models_found": models_found,
            "not_assessed_models": sorted(not_assessed_models),
            "total_models_in_db": self._db.model_count(),
        }

    # ── Internal helpers ────────────────────────────────────────────

    @staticmethod
    def _extract_model_name(finding: dict[str, Any]) -> str | None:
        """Extract the model name from a finding dict.

        Checks ``model_name``, ``model``, and falls back to inspecting
        ``matched_value`` for common model name patterns.
        """
        # Direct model_name field (set by Python/JS scanners)
        model_name = finding.get("model_name") or finding.get("model")
        if model_name and isinstance(model_name, str):
            return model_name.strip()

        # Check matched_value for model references (config scanner)
        matched = finding.get("matched_value", "")
        if matched and isinstance(matched, str):
            # Only treat as model name if the finding is a model reference
            category = finding.get("pattern_category", "")
            if category in ("model_reference", "model_usage", "model_config"):
                return matched.strip()

        return None

    @staticmethod
    def _profile_to_enrichment(profile: ModelRiskProfile) -> dict[str, Any]:
        """Convert a ``ModelRiskProfile`` to a finding enrichment dict."""
        owasp_summary: list[dict[str, str]] = []
        for risk in profile.owasp_risks:
            if risk.rating != "not_applicable":
                label = OWASP_LABELS.get(risk.owasp_id, risk.owasp_id)
                owasp_summary.append({
                    "id": risk.owasp_id,
                    "name": label,
                    "rating": risk.rating,
                    "notes": risk.notes,
                })

        return {
            "not_assessed": False,
            "name": profile.name,
            "provider": profile.provider,
            "type": profile.type,
            "license": profile.license,
            "release_date": profile.release_date,
            "last_assessed": profile.last_assessed,
            "risk_index": profile.risk_index,
            "risk_grade": profile.risk_grade,
            "owasp_risks": owasp_summary,
            "mitigations": profile.mitigations,
            "license_risk": profile.license_risk,
        }
