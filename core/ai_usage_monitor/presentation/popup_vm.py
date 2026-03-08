from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from core.ai_usage_monitor.models import AppState
from core.ai_usage_monitor.presentation.identity_vm import (
    provider_identity_fingerprint as _provider_identity_fingerprint,
    provider_identity_refreshing as _provider_identity_refreshing,
    provider_identity_vm as _provider_identity_vm,
)
from core.ai_usage_monitor.presentation.popup_vm_common import (
    is_stale,
    mini_metric_display_text,
    updated_text,
)
from core.ai_usage_monitor.presentation.popup_vm_panel import panel_vm
from core.ai_usage_monitor.presentation.popup_vm_provider import provider_vm
from core.ai_usage_monitor.presentation.popup_vm_tabs import (
    normalized_overview_provider_ids,
    overview_cards,
    provider_tab_vm,
    resolve_selected_provider_id,
    switcher_tabs_vm,
    visible_providers,
)
from core.ai_usage_monitor.providers.registry import ProviderRegistry


def build_popup_view_model(
    app_state: AppState,
    refresh_interval_seconds: int = 60,
    preferred_provider_id: str | None = None,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    stale = is_stale(app_state.updated_at, now, refresh_interval_seconds)
    descriptor_map = {item.id: item for item in ProviderRegistry().list_descriptors()}

    providers = visible_providers(app_state.providers)
    provider_order = [provider.id for provider in providers]
    all_provider_ids = [provider.id for provider in app_state.providers]
    overview_provider_ids = normalized_overview_provider_ids(
        app_state.overview_provider_ids, all_provider_ids
    )
    cards_vm = overview_cards(overview_provider_ids, app_state.providers)
    has_overview = len(overview_provider_ids) > 0

    selected_provider_id = resolve_selected_provider_id(
        provider_order, preferred_provider_id
    )
    selected_provider = next(
        (p for p in providers if p.id == selected_provider_id), None
    )
    updated = updated_text(app_state.updated_at, now)

    providers_vm = [
        provider_vm(
            provider,
            descriptor_map,
            selected=(provider.id == selected_provider_id),
            stale=stale,
            updated_text=updated,
        )
        for provider in providers
    ]

    tabs_vm = _build_tabs_vm(
        providers=providers,
        descriptor_map=descriptor_map,
        stale=stale,
        has_overview=has_overview,
        selected_provider_id=selected_provider_id,
    )
    switcher_tabs = switcher_tabs_vm(tabs_vm)

    return {
        "version": 1,
        "generatedAt": now.isoformat(),
        "popup": {
            "selectedProviderId": selected_provider_id,
            "providerOrder": provider_order,
            "enabledProviderIds": provider_order,
            "overviewProviderIds": overview_provider_ids,
            "overviewCardProviderIds": [
                str(card.get("providerId") or "")
                for card in cards_vm
                if card.get("providerId")
            ],
            "overviewSelectionIndependent": True,
            "hasOverview": has_overview,
            "identityRefreshPending": any(
                _provider_identity_refreshing(provider) for provider in providers
            ),
            "activeIdentity": _provider_identity_vm(selected_provider),
            "activeIdentityFingerprint": _provider_identity_fingerprint(
                selected_provider
            ),
            "tabs": tabs_vm,
            "switcherTabs": switcher_tabs,
            "selectableProviderIds": provider_order,
            "providers": providers_vm,
            "overviewCards": cards_vm,
            "panel": panel_vm(
                switcher_tabs=switcher_tabs,
                providers_vm=providers_vm,
                selected_provider_id=selected_provider_id,
            ),
        },
    }


def _build_tabs_vm(
    *,
    providers: list,
    descriptor_map: dict[str, Any],
    stale: bool,
    has_overview: bool,
    selected_provider_id: str,
) -> list[dict[str, Any]]:
    tabs_vm: list[dict[str, Any]] = []
    if has_overview:
        tabs_vm.append(
            {
                "id": "overview",
                "kind": "overview",
                "title": "Overview",
                "shortTitle": "Overview",
                "selected": False,
                "visible": True,
                "enabled": True,
                "iconKey": None,
                "badgeText": None,
                "accentColor": None,
                "miniMetric": {
                    "available": True,
                    "stale": stale,
                    "percent": None,
                    "mode": "none",
                    "displayText": mini_metric_display_text("none", None),
                },
            }
        )

    for provider in providers:
        tabs_vm.append(
            provider_tab_vm(
                provider,
                descriptor_map,
                selected=(provider.id == selected_provider_id),
                stale=stale,
            )
        )
    return tabs_vm
