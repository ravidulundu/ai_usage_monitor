from __future__ import annotations

import hashlib
import json
from typing import Any

from core.ai_usage_monitor.models import ProviderState
from core.ai_usage_monitor.runtime_cache import read_ttl_cache, write_ttl_cache


_PROVIDER_FRESHNESS_CACHE_FILE = "provider_freshness_cache.json"
_PROVIDER_FRESHNESS_TTLS: dict[str, int] = {
    # API-first providers: short TTL to reduce repeated remote fetch churn.
    "copilot": 30,
    "openrouter": 45,
    "zai": 45,
    "vertexai": 45,
    # Web/API providers with comparatively stable quota windows.
    "ollama": 30,
    "amp": 30,
    "minimax": 30,
}


def provider_cache_ttl(provider_id: str) -> int:
    return int(_PROVIDER_FRESHNESS_TTLS.get(provider_id, 0))


def _cache_key(provider_id: str, settings: dict[str, Any]) -> str:
    encoded = json.dumps(
        {"providerId": provider_id, "settings": settings},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_cached_provider_result(
    provider_id: str,
    settings: dict[str, Any],
) -> tuple[dict[str, Any], ProviderState] | None:
    ttl_seconds = provider_cache_ttl(provider_id)
    if ttl_seconds <= 0:
        return None
    cached = read_ttl_cache(
        _PROVIDER_FRESHNESS_CACHE_FILE,
        _cache_key(provider_id, settings),
        ttl_seconds,
    )
    if not isinstance(cached, dict):
        return None
    legacy = cached.get("legacy")
    state = cached.get("state")
    if not isinstance(legacy, dict) or not isinstance(state, dict):
        return None
    return dict(legacy), ProviderState.from_dict(state)


def store_cached_provider_result(
    provider_id: str,
    settings: dict[str, Any],
    legacy: dict[str, Any],
    state: ProviderState,
) -> None:
    ttl_seconds = provider_cache_ttl(provider_id)
    if ttl_seconds <= 0:
        return
    write_ttl_cache(
        _PROVIDER_FRESHNESS_CACHE_FILE,
        _cache_key(provider_id, settings),
        {"legacy": dict(legacy), "state": state.to_dict()},
    )
