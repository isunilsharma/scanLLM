"""JSON output formatter for ScanLLM CLI."""

from __future__ import annotations

import json
import sys
from typing import Any

from rich.console import Console

console = Console()


def print_json(
    scan_result: dict[str, Any],
    risk_result: dict[str, Any] | None = None,
    owasp_result: dict[str, Any] | None = None,
    policy_result: dict[str, Any] | None = None,
    graph_data: dict[str, Any] | None = None,
    pretty: bool = True,
) -> None:
    """Print scan results as JSON to stdout.

    Combines all result sections into a single JSON document.
    Output goes to stdout so it can be piped to other tools.
    """
    output: dict[str, Any] = {
        "version": "2.0.0",
        "findings": scan_result.get("findings", []),
        "summary": scan_result.get("summary", {}),
    }

    if risk_result:
        output["risk"] = risk_result
    if owasp_result:
        output["owasp"] = owasp_result
    if policy_result:
        output["policy"] = policy_result
    if graph_data:
        output["graph"] = graph_data

    indent = 2 if pretty else None
    # Write directly to stdout to avoid Rich markup interpretation
    sys.stdout.write(json.dumps(output, indent=indent, default=str) + "\n")


def format_json(data: dict[str, Any], pretty: bool = True) -> str:
    """Return a JSON string representation of *data*."""
    indent = 2 if pretty else None
    return json.dumps(data, indent=indent, default=str)
