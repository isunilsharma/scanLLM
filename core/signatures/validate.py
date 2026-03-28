"""Validate ai_signatures.yaml for correctness and completeness.

Run as: python -m core.signatures.validate
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


VALID_OWASP_IDS = {f"LLM{i:02d}" for i in range(1, 11)}
VALID_SEVERITIES = {"critical", "high", "medium", "low"}
VALID_CATEGORIES = {
    "llm_provider",
    "vector_db",
    "orchestration_framework",
    "agent_tool",
    "inference_server",
    "mcp_server",
    "embedding_service",
}

# Top-level sections that contain provider/tool entries
ENTRY_SECTIONS = {"providers", "vector_databases", "frameworks", "inference", "mcp"}


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load and parse the YAML file."""
    try:
        import yaml
    except ImportError:
        print("ERROR: PyYAML is required. Install with: pip install pyyaml")
        sys.exit(1)

    try:
        with open(path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        print(f"YAML SYNTAX ERROR: {exc}")
        sys.exit(1)

    if not isinstance(data, dict):
        print("ERROR: Top-level YAML structure must be a mapping")
        sys.exit(1)

    return data


def validate(path: Path | None = None) -> bool:
    """Validate the signatures file. Returns True if valid."""
    if path is None:
        path = Path(__file__).parent / "ai_signatures.yaml"

    if not path.exists():
        print(f"ERROR: Signatures file not found: {path}")
        return False

    data = _load_yaml(path)

    errors: list[str] = []
    warnings: list[str] = []

    # Track all entry names across sections for duplicate detection
    all_names: dict[str, str] = {}  # name -> section
    total_patterns = 0
    owasp_mapped = 0
    provider_count = 0

    for section_name in ENTRY_SECTIONS:
        section = data.get(section_name)
        if section is None:
            continue
        if not isinstance(section, dict):
            errors.append(f"Section '{section_name}' must be a mapping, got {type(section).__name__}")
            continue

        for entry_name, entry in section.items():
            provider_count += 1

            # Check for duplicate names across sections
            if entry_name in all_names:
                errors.append(
                    f"Duplicate entry '{entry_name}' in '{section_name}' "
                    f"(already defined in '{all_names[entry_name]}')"
                )
            all_names[entry_name] = section_name

            if not isinstance(entry, dict):
                errors.append(f"{section_name}.{entry_name}: entry must be a mapping")
                continue

            # Required: display_name
            if "display_name" not in entry:
                errors.append(f"{section_name}.{entry_name}: missing required field 'display_name'")

            # Required: category
            category = entry.get("category")
            if not category:
                errors.append(f"{section_name}.{entry_name}: missing required field 'category'")
            elif category not in VALID_CATEGORIES:
                warnings.append(
                    f"{section_name}.{entry_name}: category '{category}' is not in "
                    f"the standard set {sorted(VALID_CATEGORIES)}"
                )

            # Required: risk_weight
            rw = entry.get("risk_weight")
            if rw is None:
                errors.append(f"{section_name}.{entry_name}: missing required field 'risk_weight'")
            elif not isinstance(rw, (int, float)):
                errors.append(f"{section_name}.{entry_name}: risk_weight must be a number, got {type(rw).__name__}")

            # Check that at least one detection method exists
            has_detection = False
            for key in ("python", "javascript", "env_vars", "endpoint_urls", "config_files", "docker_images"):
                if key in entry:
                    has_detection = True
                    break
            if not has_detection:
                warnings.append(
                    f"{section_name}.{entry_name}: no detection methods defined "
                    f"(needs python, javascript, env_vars, endpoint_urls, config_files, or docker_images)"
                )

            # Count patterns
            for lang in ("python", "javascript"):
                lang_section = entry.get(lang)
                if isinstance(lang_section, dict):
                    for key in ("imports", "calls", "models"):
                        items = lang_section.get(key)
                        if isinstance(items, list):
                            total_patterns += len(items)

            if isinstance(entry.get("env_vars"), list):
                total_patterns += len(entry["env_vars"])
            if isinstance(entry.get("endpoint_urls"), list):
                total_patterns += len(entry["endpoint_urls"])
            if isinstance(entry.get("docker_images"), list):
                total_patterns += len(entry["docker_images"])
            if isinstance(entry.get("config_files"), list):
                total_patterns += len(entry["config_files"])

            # Validate risk_patterns
            risk_patterns = entry.get("risk_patterns")
            if isinstance(risk_patterns, list):
                for i, rp in enumerate(risk_patterns):
                    if not isinstance(rp, dict):
                        errors.append(f"{section_name}.{entry_name}.risk_patterns[{i}]: must be a mapping")
                        continue
                    if "pattern" not in rp:
                        errors.append(f"{section_name}.{entry_name}.risk_patterns[{i}]: missing 'pattern'")
                    owasp_id = rp.get("owasp")
                    if owasp_id:
                        owasp_mapped += 1
                        if owasp_id not in VALID_OWASP_IDS:
                            errors.append(
                                f"{section_name}.{entry_name}.risk_patterns[{i}]: "
                                f"invalid OWASP ID '{owasp_id}' (valid: {sorted(VALID_OWASP_IDS)})"
                            )
                    severity = rp.get("severity")
                    if severity and severity not in VALID_SEVERITIES:
                        errors.append(
                            f"{section_name}.{entry_name}.risk_patterns[{i}]: "
                            f"invalid severity '{severity}' (valid: {sorted(VALID_SEVERITIES)})"
                        )
                    total_patterns += 1

    # Validate top-level risk_patterns section
    top_risk = data.get("risk_patterns")
    if isinstance(top_risk, dict):
        for rp_name, rp in top_risk.items():
            if not isinstance(rp, dict):
                errors.append(f"risk_patterns.{rp_name}: must be a mapping")
                continue
            owasp_id = rp.get("owasp")
            if owasp_id:
                owasp_mapped += 1
                if owasp_id not in VALID_OWASP_IDS:
                    errors.append(
                        f"risk_patterns.{rp_name}: invalid OWASP ID '{owasp_id}' "
                        f"(valid: {sorted(VALID_OWASP_IDS)})"
                    )
            severity = rp.get("severity")
            if severity and severity not in VALID_SEVERITIES:
                errors.append(
                    f"risk_patterns.{rp_name}: invalid severity '{severity}' "
                    f"(valid: {sorted(VALID_SEVERITIES)})"
                )
            total_patterns += 1

    # Print results
    print(f"Signatures file: {path}")
    print(f"  Providers/tools: {provider_count}")
    print(f"  Total patterns:  {total_patterns}")
    print(f"  OWASP-mapped:    {owasp_mapped}")
    print()

    if warnings:
        print(f"WARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  - {w}")
        print()

    if errors:
        print(f"ERRORS ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
        print()
        print("VALIDATION FAILED")
        return False

    print("VALIDATION PASSED")
    return True


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    success = validate(path)
    sys.exit(0 if success else 1)
