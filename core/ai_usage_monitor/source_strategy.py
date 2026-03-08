from __future__ import annotations

"""Compatibility shim; prefer `core.ai_usage_monitor.sources.strategy`."""

from typing import Any

from core.ai_usage_monitor.sources.strategy import (
    resolve_provider_source_plan as _resolve_provider_source_plan,
)


def resolve_provider_source_plan(
    descriptor: Any,
    settings: dict[str, Any] | None,
    configured_source: str | None = None,
) -> dict[str, Any]:
    return _resolve_provider_source_plan(
        descriptor=descriptor,
        settings=settings,
        configured_source=configured_source,
    )


__all__ = [
    "resolve_provider_source_plan",
]
