from __future__ import annotations

from typing import Any

from core.ai_usage_monitor.presentation.popup_vm_common import clamp_pct


def panel_percent(tab: dict[str, Any] | None) -> float | None:
    metric = (tab or {}).get("miniMetric")
    if not isinstance(metric, dict) or str(metric.get("mode") or "") != "percent":
        return None
    value = metric.get("percent")
    try:
        parsed = float(value) if value is not None else None
    except Exception:
        return None
    return clamp_pct(parsed) if parsed is not None else None


def panel_tone(percent: float | None, provider: dict[str, Any] | None) -> str:
    error_state = provider.get("errorState") if isinstance(provider, dict) else {}
    error_state = error_state if isinstance(error_state, dict) else {}
    if error_state.get("hasError"):
        return "error"

    status_state = provider.get("statusState") if isinstance(provider, dict) else {}
    status_state = status_state if isinstance(status_state, dict) else {}
    if status_state.get("incidentActive") is True:
        return "error" if status_state.get("tone") == "error" else "warn"

    if percent is None:
        return "ok"
    if percent >= 90:
        return "error"
    if percent >= 70:
        return "warn"
    if percent >= 40:
        return "accent"
    return "ok"


def first_visible_metric(provider: dict[str, Any]) -> dict[str, Any] | None:
    metrics = provider.get("metrics")
    if not isinstance(metrics, list):
        return None
    for metric in metrics:
        if isinstance(metric, dict) and metric.get("visible", True):
            return metric
    for metric in metrics:
        if isinstance(metric, dict):
            return metric
    return None


def panel_tooltip_lines(provider: dict[str, Any] | None) -> list[str]:
    if not isinstance(provider, dict):
        return []

    lines: list[str] = []
    provider_name = str(provider.get("displayName") or "").strip()
    if provider_name:
        lines.append(provider_name)

    metric = first_visible_metric(provider)
    right_text = str((metric or {}).get("rightText") or "").strip()
    if right_text:
        lines.append(right_text)

    status_state = provider.get("statusState") or {}
    if isinstance(status_state, dict) and status_state.get("incidentActive"):
        summary = str(status_state.get("summary") or "").strip()
        if summary:
            lines.append(summary)

    error_state = provider.get("errorState") or {}
    if isinstance(error_state, dict) and error_state.get("hasError"):
        message = str(error_state.get("message") or "").strip()
        if message:
            lines.append(message)

    return lines


def panel_vm(
    switcher_tabs: list[dict[str, Any]],
    providers_vm: list[dict[str, Any]],
    selected_provider_id: str,
) -> dict[str, Any]:
    provider_tabs = [
        tab for tab in switcher_tabs if str(tab.get("kind") or "").lower() == "provider"
    ]
    fallback_tab = provider_tabs[0] if provider_tabs else None
    active_tab = next(
        (
            tab
            for tab in provider_tabs
            if str(tab.get("id") or "") == str(selected_provider_id or "")
        ),
        fallback_tab,
    )
    active_provider_id = str(active_tab.get("id") or "") if active_tab else ""
    active_provider = next(
        (
            provider
            for provider in providers_vm
            if str(provider.get("id") or "") == active_provider_id
        ),
        None,
    )
    percent = panel_percent(active_tab)
    return {
        "providerId": active_provider_id,
        "title": str(
            (active_provider or {}).get("displayName")
            or (active_tab or {}).get("title")
            or ""
        ),
        "badgeText": str((active_tab or {}).get("badgeText") or ""),
        "iconKey": (active_tab or {}).get("iconKey"),
        "displayText": str(
            ((active_tab or {}).get("miniMetric") or {}).get("displayText") or "-"
        ),
        "percent": percent,
        "tone": panel_tone(percent, active_provider),
        "tooltipLines": panel_tooltip_lines(active_provider),
    }
