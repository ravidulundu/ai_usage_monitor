from __future__ import annotations

from typing import Any

from core.ai_usage_monitor.models import ProviderState
from core.ai_usage_monitor.presentation.popup_vm_common import (
    branding,
    metric_percent,
    mini_metric_display_text,
    plan_label,
    provider_badge_text,
    provider_short_name,
)


def visible_providers(providers: list[ProviderState]) -> list[ProviderState]:
    visible = [provider for provider in providers if provider.enabled]
    visible.sort(key=provider_rank)
    return visible


def normalized_overview_provider_ids(
    overview_provider_ids: list[str], known_provider_ids: list[str]
) -> list[str]:
    known = set(known_provider_ids)
    ordered: list[str] = []
    for provider_id in overview_provider_ids:
        normalized = str(provider_id or "").strip()
        if not normalized or normalized in ordered or normalized not in known:
            continue
        ordered.append(normalized)
        if len(ordered) >= 3:
            break
    return ordered


def resolve_selected_provider_id(
    provider_order: list[str], preferred_provider_id: str | None
) -> str:
    if preferred_provider_id and preferred_provider_id in provider_order:
        return preferred_provider_id
    return provider_order[0] if provider_order else ""


def provider_rank(provider: ProviderState) -> tuple[int, str]:
    install_rank = 0 if provider.installed else 2
    if (provider.primary_metric or provider.secondary_metric) and not provider.error:
        rank = 0
    elif not provider.error:
        rank = 1
    else:
        rank = 2
    return install_rank * 10 + rank, provider.display_name.lower()


def overview_cards(
    overview_provider_ids: list[str], providers: list[ProviderState]
) -> list[dict[str, Any]]:
    by_id = {provider.id: provider for provider in providers}
    cards: list[dict[str, Any]] = []
    for provider_id in overview_provider_ids:
        provider = by_id.get(provider_id)
        if not provider:
            continue
        session_percent = metric_percent(provider.primary_metric)
        weekly_percent = metric_percent(provider.secondary_metric)
        cards.append(
            {
                "providerId": provider.id,
                "title": provider_short_name(provider.id, provider.display_name),
                "planLabel": plan_label(provider),
                "metrics": [
                    {
                        "kind": "session",
                        "label": "Session",
                        "percent": session_percent,
                        "available": session_percent is not None,
                        "displayText": mini_metric_display_text(
                            "percent", session_percent
                        )
                        if session_percent is not None
                        else "—",
                    },
                    {
                        "kind": "weekly",
                        "label": "Weekly",
                        "percent": weekly_percent,
                        "available": weekly_percent is not None,
                        "displayText": mini_metric_display_text(
                            "percent", weekly_percent
                        )
                        if weekly_percent is not None
                        else "—",
                    },
                ],
            }
        )
        if len(cards) >= 3:
            break
    return cards


def provider_tab_vm(
    provider: ProviderState,
    descriptor_map: dict[str, Any],
    selected: bool,
    stale: bool,
) -> dict[str, Any]:
    descriptor = descriptor_map.get(provider.id)
    short_name = provider_short_name(
        provider.id,
        provider.display_name,
        descriptor.short_name if descriptor else None,
    )
    provider_branding = branding(provider)
    primary = provider.primary_metric
    rate_limits_missing = (
        provider.id == "codex" and provider.extras.get("hasRateLimits") is False
    )

    mode = "none"
    percent: float | None = None
    available = False
    if primary:
        mode, percent, available = "percent", metric_percent(primary), True
    elif provider.installed and not provider.error and not rate_limits_missing:
        mode, available = "tick", True

    return {
        "id": provider.id,
        "kind": "provider",
        "title": provider.display_name,
        "shortTitle": short_name,
        "selected": selected,
        "visible": True,
        "enabled": True,
        "iconKey": provider_branding.get("iconKey"),
        "badgeText": provider_badge_text(
            provider.id,
            provider.display_name,
            provider_branding.get("badgeText"),
        ),
        "accentColor": provider_branding.get("color"),
        "miniMetric": {
            "available": available,
            "stale": stale,
            "percent": percent,
            "mode": mode,
            "displayText": mini_metric_display_text(mode, percent),
        },
    }


def switcher_tabs_vm(tabs_vm: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        tab for tab in tabs_vm if tab.get("visible", True) and tab.get("enabled", True)
    ]
