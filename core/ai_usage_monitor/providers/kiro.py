"""Compatibility shim for archived provider implementation."""

from core.ai_usage_monitor.archived_providers.kiro import (
    ANSI_RE,
    DESCRIPTOR,
    collect_kiro,
    parse_kiro_output,
    strip_ansi,
)

__all__ = [
    "ANSI_RE",
    "DESCRIPTOR",
    "collect_kiro",
    "parse_kiro_output",
    "strip_ansi",
]
