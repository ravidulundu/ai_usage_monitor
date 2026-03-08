from __future__ import annotations

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


# Backward-compatible alias used by tests that patch collector mappings.
COLLECTORS = fetcher_map()


def collect_all() -> tuple[dict[str, dict], AppState]:
    config = load_config()
    settings_map = provider_settings_map(config)
    identity_store = load_identity_store()
    provider_records = build_provider_records(
        registry=ProviderRegistry(),
        settings_map=settings_map,
        identity_store=identity_store,
        collectors=COLLECTORS,
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
    legacy, _ = collect_all()
    return legacy


def collect_state_payload() -> dict:
    _, app_state = collect_all()
    return app_state.to_dict()


def collect_popup_vm_payload(preferred_provider_id: str | None = None) -> dict:
    config = load_config()
    _, app_state = collect_all()
    refresh_interval = int(config.get("refreshInterval") or 60)
    return build_popup_view_model(
        app_state,
        refresh_interval_seconds=refresh_interval,
        preferred_provider_id=preferred_provider_id,
    )
