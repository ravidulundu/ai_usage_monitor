from __future__ import annotations

from typing import Any

ABOUT_PAGE_URL = "https://github.com/KodyMike/ai_usage_monitor"

_CANONICAL_ACTION_SPECS: tuple[dict[str, str], ...] = (
    {"id": "usage_dashboard", "label": "Usage Dashboard", "intent": "open_url"},
    {"id": "status_page", "label": "Status Page", "intent": "open_url"},
    {"id": "settings", "label": "Settings", "intent": "open_settings"},
    {"id": "about", "label": "About", "intent": "about"},
    {"id": "quit", "label": "Quit", "intent": "quit"},
)


def actions_vm(
    dashboard_url: str | None, status_url: str | None
) -> list[dict[str, Any]]:
    target_by_id: dict[str, str | None] = {
        "usage_dashboard": dashboard_url,
        "status_page": status_url,
        "settings": None,
        "about": ABOUT_PAGE_URL,
        "quit": None,
    }
    enabled_by_id: dict[str, bool] = {
        "usage_dashboard": bool(dashboard_url),
        "status_page": bool(status_url),
        "settings": True,
        "about": True,
        "quit": True,
    }
    actions: list[dict[str, Any]] = []
    for spec in _CANONICAL_ACTION_SPECS:
        action_id = spec["id"]
        actions.append(
            {
                "id": action_id,
                "label": spec["label"],
                "visible": True,
                "enabled": enabled_by_id[action_id],
                "intent": spec["intent"],
                "target": target_by_id[action_id],
            }
        )
    return actions
