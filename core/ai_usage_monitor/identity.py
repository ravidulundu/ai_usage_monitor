from __future__ import annotations

from typing import Any

from core.ai_usage_monitor.identity_apply import (
    apply_identity_to_provider as _apply_identity_to_provider,
)
from core.ai_usage_monitor.identity_snapshot import (
    load_identity_store as _load_identity_store,
    save_identity_store as _save_identity_store,
)
from core.ai_usage_monitor.models import ProviderState


def load_identity_store() -> dict[str, Any]:
    return _load_identity_store()


def save_identity_store(store: dict[str, Any]) -> None:
    _save_identity_store(store)


def apply_identity_to_provider(
    provider: ProviderState,
    provider_legacy: Any,
    configured_source: str,
    store: dict[str, Any],
) -> bool:
    return _apply_identity_to_provider(
        provider,
        provider_legacy,
        configured_source,
        store,
    )


__all__ = [
    "apply_identity_to_provider",
    "load_identity_store",
    "save_identity_store",
]
