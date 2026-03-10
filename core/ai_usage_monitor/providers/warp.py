"""Compatibility shim for archived provider implementation."""

from core.ai_usage_monitor.archived_providers.warp import (
    DESCRIPTOR,
    _api_key,
    collect_warp,
)

__all__ = ["DESCRIPTOR", "_api_key", "collect_warp"]
