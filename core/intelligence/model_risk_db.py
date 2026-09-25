"""
Model Risk Intelligence Database for ScanLLM.

Loads curated risk profiles from ``risk_profiles.yaml`` and provides
exact and fuzzy lookup by model name.  Each profile captures OWASP LLM
Top 10 risk ratings, a composite risk index (0-100), license
information, and recommended mitigations.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_PROFILES_PATH = Path(__file__).parent / "risk_profiles.yaml"

# ── Risk grade thresholds (same scale as RiskEngine) ────────────────────
_GRADE_RANGES: dict[str, tuple[int, int]] = {
    "A": (0, 20),
    "B": (21, 40),
    "C": (41, 60),
    "D": (61, 80),
    "F": (81, 100),
}


@dataclass
class OwaspRisk:
    """A single OWASP LLM Top 10 risk rating for a model."""

    owasp_id: str
    rating: str  # susceptible | moderate | low | not_applicable
    notes: str = ""


@dataclass
class ModelRiskProfile:
    """Complete risk profile for an AI model."""

    name: str
    provider: str
    type: str  # llm | embedding | image_generation
    license: str
    release_date: str
    last_assessed: str
    owasp_risks: list[OwaspRisk] = field(default_factory=list)
    risk_index: int = 0
    risk_grade: str = "C"
    mitigations: list[str] = field(default_factory=list)
    license_risk: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict for JSON output."""
        return {
            "name": self.name,
            "provider": self.provider,
            "type": self.type,
            "license": self.license,
            "release_date": self.release_date,
            "last_assessed": self.last_assessed,
            "owasp_risks": [
                {"owasp_id": r.owasp_id, "rating": r.rating, "notes": r.notes}
                for r in self.owasp_risks
            ],
            "risk_index": self.risk_index,
            "risk_grade": self.risk_grade,
            "mitigations": self.mitigations,
            "license_risk": self.license_risk,
        }


# ── Friendly OWASP ID labels ───────────────────────────────────────────
OWASP_LABELS: dict[str, str] = {
    "LLM01": "Prompt Injection",
    "LLM02": "Sensitive Data",
    "LLM03": "Supply Chain",
    "LLM05": "Output Handling",
    "LLM06": "Excessive Agency",
    "LLM07": "System Prompt",
    "LLM08": "Vector/Embedding",
    "LLM10": "Unbounded Consumption",
}


def _owasp_key_to_id(key: str) -> str:
    """Convert a YAML key like ``LLM01_prompt_injection`` to ``LLM01``."""
    return key.split("_")[0]


def _parse_profile(name: str, data: dict[str, Any]) -> ModelRiskProfile:
    """Parse a raw YAML model entry into a ``ModelRiskProfile``."""
    owasp_risks: list[OwaspRisk] = []
    for key, value in (data.get("owasp_risks") or {}).items():
        owasp_id = _owasp_key_to_id(key)
        if isinstance(value, dict):
            owasp_risks.append(
                OwaspRisk(
                    owasp_id=owasp_id,
                    rating=value.get("rating", "not_applicable"),
                    notes=value.get("notes", ""),
                )
            )
        else:
            owasp_risks.append(OwaspRisk(owasp_id=owasp_id, rating=str(value)))

    return ModelRiskProfile(
        name=name,
        provider=data.get("provider", "unknown"),
        type=data.get("type", "llm"),
        license=data.get("license", "unknown"),
        release_date=data.get("release_date", ""),
        last_assessed=data.get("last_assessed", ""),
        owasp_risks=owasp_risks,
        risk_index=int(data.get("risk_index", 50)),
        risk_grade=data.get("risk_grade", "C"),
        mitigations=data.get("mitigations", []),
        license_risk=data.get("license_risk", ""),
    )


# ── Date-suffix regex ───────────────────────────────────────────────────
# Matches trailing date patterns like -20240513, -2024-05-13, -20241022
_DATE_SUFFIX_RE = re.compile(r"-\d{4}-?\d{2}-?\d{2}$")
# Matches trailing version-like suffixes: -v2, -001, -002, -latest
_VERSION_SUFFIX_RE = re.compile(r"-(v\d+|latest|\d{3})$")


class ModelRiskDB:
    """Model risk intelligence database.

    Loads ``risk_profiles.yaml`` and provides exact, alias-based, and
    fuzzy lookups for model risk profiles.

    Usage::

        db = ModelRiskDB()
        profile = db.lookup("gpt-4o")
        profile = db.lookup_fuzzy("gpt-4o-2024-05-13")
    """

    def __init__(self, profiles_path: Path | None = None) -> None:
        self._path = profiles_path or _PROFILES_PATH
        self._profiles: dict[str, ModelRiskProfile] = {}
        self._aliases: dict[str, str] = {}
        self._load()

    # ── Public API ──────────────────────────────────────────────────

    def lookup(self, model_name: str) -> ModelRiskProfile | None:
        """Exact lookup by canonical model name.

        Returns ``None`` if the model is not in the database.
        """
        key = model_name.strip().lower()
        return self._profiles.get(key)

    def lookup_fuzzy(self, model_name: str) -> ModelRiskProfile | None:
        """Fuzzy lookup that handles version variants and aliases.

        Resolution order:
        1. Exact match on canonical name
        2. Exact match on alias table
        3. Strip date suffix (``-20240513``, ``-2024-05-13``) and retry
        4. Strip version suffix (``-v2``, ``-001``, ``-latest``) and retry
        5. Normalise separators (``_`` → ``-``, ``.`` → ``-``) and retry
        6. Prefix match against all canonical names
        """
        if not model_name:
            return None

        key = model_name.strip().lower()

        # 1. Exact match on canonical name
        if key in self._profiles:
            return self._profiles[key]

        # 2. Alias table
        canonical = self._aliases.get(key)
        if canonical and canonical in self._profiles:
            return self._profiles[canonical]

        # 3. Strip date suffix
        stripped = _DATE_SUFFIX_RE.sub("", key)
        if stripped != key:
            result = self._profiles.get(stripped)
            if result:
                return result
            canonical = self._aliases.get(stripped)
            if canonical and canonical in self._profiles:
                return self._profiles[canonical]

        # 4. Strip version suffix
        stripped = _VERSION_SUFFIX_RE.sub("", key)
        if stripped != key:
            result = self._profiles.get(stripped)
            if result:
                return result

        # 5. Normalise separators
        normalised = key.replace("_", "-").replace(".", "-")
        if normalised != key:
            result = self._profiles.get(normalised)
            if result:
                return result
            canonical = self._aliases.get(normalised)
            if canonical and canonical in self._profiles:
                return self._profiles[canonical]

        # 6. Prefix match — pick the longest matching canonical name
        best: ModelRiskProfile | None = None
        best_len = 0
        for cname, profile in self._profiles.items():
            if key.startswith(cname) and len(cname) > best_len:
                best = profile
                best_len = len(cname)

        return best

    def list_models(self) -> list[str]:
        """Return a sorted list of all canonical model names."""
        return sorted(self._profiles.keys())

    def get_all_profiles(self) -> dict[str, ModelRiskProfile]:
        """Return all profiles keyed by canonical name."""
        return dict(self._profiles)

    def model_count(self) -> int:
        """Return the number of models in the database."""
        return len(self._profiles)

    # ── Internal ────────────────────────────────────────────────────

    def _load(self) -> None:
        """Load profiles and aliases from the YAML file."""
        if not self._path.exists():
            logger.warning("Risk profiles not found at %s", self._path)
            return

        try:
            with open(self._path, encoding="utf-8") as fh:
                data = yaml.safe_load(fh) or {}
        except Exception:
            logger.warning("Failed to load risk profiles from %s", self._path, exc_info=True)
            return

        # Parse model profiles
        models_data = data.get("models", {})
        for name, profile_data in models_data.items():
            if isinstance(profile_data, dict):
                key = name.strip().lower()
                self._profiles[key] = _parse_profile(name, profile_data)

        # Parse aliases
        aliases_data = data.get("aliases", {})
        for alias, canonical in aliases_data.items():
            if isinstance(alias, str) and isinstance(canonical, str):
                self._aliases[alias.strip().lower()] = canonical.strip().lower()

        logger.info(
            "Loaded %d model risk profiles and %d aliases from %s",
            len(self._profiles),
            len(self._aliases),
            self._path,
        )
