"""Compatibility shim for archived provider implementation."""

from core.ai_usage_monitor.archived_providers.jetbrains import (
    DESCRIPTOR,
    IDE_PATTERNS,
    collect_jetbrains,
    decode_html_entities,
    detect_installed_ides,
    parse_jetbrains_xml,
)

__all__ = [
    "DESCRIPTOR",
    "IDE_PATTERNS",
    "collect_jetbrains",
    "decode_html_entities",
    "detect_installed_ides",
    "parse_jetbrains_xml",
]
