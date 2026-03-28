"""SARIF 2.1.0 output for GitHub Code Scanning and IDE integration."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def print_sarif(findings: list[dict[str, Any]], scan_path: Path) -> None:
    """Convert findings to SARIF 2.1.0 format and write to stdout."""
    sarif = to_sarif(findings, scan_path)
    sys.stdout.write(json.dumps(sarif, indent=2, default=str) + "\n")


def to_sarif(findings: list[dict[str, Any]], scan_path: Path) -> dict[str, Any]:
    """Convert findings to SARIF 2.1.0 format."""
    rules: dict[str, dict[str, Any]] = {}
    results: list[dict[str, Any]] = []

    severity_to_level = {"critical": "error", "high": "error", "medium": "warning", "low": "note", "info": "note"}

    for finding in findings:
        rule_id = finding.get("pattern_name", "unknown")
        sev = (finding.get("severity") or finding.get("pattern_severity") or "info").lower()
        level = severity_to_level.get(sev, "note")
        file_path = finding.get("file_path", "")
        line_number = finding.get("line_number", 1) or 1
        message = finding.get("message", "") or finding.get("pattern_description", "") or rule_id
        owasp_id = finding.get("owasp_id", "")

        if rule_id not in rules:
            rules[rule_id] = {
                "id": rule_id,
                "shortDescription": {"text": rule_id},
                "helpUri": "https://scanllm.ai",
                "properties": {"tags": ["security", "ai", "llm"] + ([owasp_id] if owasp_id else [])},
            }

        results.append({
            "ruleId": rule_id,
            "level": level,
            "message": {"text": message},
            "locations": [{
                "physicalLocation": {
                    "artifactLocation": {"uri": file_path, "uriBaseId": "%SRCROOT%"},
                    "region": {"startLine": max(1, int(line_number))},
                }
            }],
        })

    return {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/main/sarif-2.1/schema/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {
                "driver": {
                    "name": "ScanLLM",
                    "version": "2.0.0",
                    "informationUri": "https://scanllm.ai",
                    "rules": list(rules.values()),
                }
            },
            "results": results,
        }],
    }
