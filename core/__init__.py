"""ScanLLM Core — shared scanning engine, graph builder, risk scorer, and policy engine."""

from __future__ import annotations

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("scanllm")
except PackageNotFoundError:
    __version__ = "0.0.0-dev"
