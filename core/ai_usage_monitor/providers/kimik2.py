"""Compatibility shim for archived provider implementation."""

from core.ai_usage_monitor.archived_providers.kimik2 import (
    DESCRIPTOR,
    _api_key,
    collect_kimik2,
)

__all__ = ["DESCRIPTOR", "_api_key", "collect_kimik2"]
