from __future__ import annotations

import hashlib
import json

from core.ai_usage_monitor.collector_helpers import (
    build_provider_records,
    changed_provider_ids,
    refresh_changed_provider_records,
)
from core.ai_usage_monitor.config import load_config, provider_settings_map
from core.ai_usage_monitor.identity import load_identity_store, save_identity_store
from core.ai_usage_monitor.models import AppState
from core.ai_usage_monitor.presentation import build_popup_view_model
from core.ai_usage_monitor.providers.fetch_strategies import fetcher_map
from core.ai_usage_monitor.providers.registry import ProviderRegistry
from core.ai_usage_monitor.runtime_cache import read_ttl_cache, write_ttl_cache


# Backward-compatible alias used by tests that patch collector mappings.
COLLECTORS = fetcher_map()
_POPUP_VM_CACHE_FILE = "popup_vm_cache.json"


def _popup_vm_cache_key(
    config: dict[str, object], preferred_provider_id: str | None
) -> str:
    payload = {
        "mode": "popup-vm",
        "preferredProviderId": preferred_provider_id or "",
        "config": config,
    }
    encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def collect_all() -> tuple[dict[str, dict], AppState]:
    return _collect_all(force_refresh=False)


def _collect_all(force_refresh: bool) -> tuple[dict[str, dict], AppState]:
    config = load_config()
    settings_map = provider_settings_map(config)
    identity_store = load_identity_store()
    provider_records = build_provider_records(
        registry=ProviderRegistry(),
        settings_map=settings_map,
        identity_store=identity_store,
        collectors=COLLECTORS,
        force_refresh=force_refresh,
    )

    changed_ids = changed_provider_ids(provider_records)
    refresh_changed_provider_records(provider_records, changed_ids, identity_store)

    legacy = {record["provider_id"]: record["legacy"] for record in provider_records}
    state = [record["state"] for record in provider_records]
    save_identity_store(identity_store)
    return legacy, AppState(
        providers=state,
        overview_provider_ids=list(config.get("overviewProviderIds") or []),
    )


def collect_legacy_usage() -> dict:
    legacy, _ = _collect_all(force_refresh=False)
    return legacy


def collect_state_payload() -> dict:
    _, app_state = _collect_all(force_refresh=False)
    return app_state.to_dict()


def collect_popup_vm_payload(
    preferred_provider_id: str | None = None, force: bool = False
) -> dict:
    config = load_config()
    polling_cache_seconds = int(config.get("pollingCacheSeconds") or 0)
    cache_key = _popup_vm_cache_key(config, preferred_provider_id)
    if not force and polling_cache_seconds > 0:
        cached = read_ttl_cache(_POPUP_VM_CACHE_FILE, cache_key, polling_cache_seconds)
        if isinstance(cached, dict):
            return cached
    _, app_state = _collect_all(force_refresh=force)
    refresh_interval = int(config.get("refreshInterval") or 60)
    payload = build_popup_view_model(
        app_state,
        refresh_interval_seconds=refresh_interval,
        preferred_provider_id=preferred_provider_id,
    )
    if polling_cache_seconds > 0:
        write_ttl_cache(_POPUP_VM_CACHE_FILE, cache_key, payload)
    return payload
