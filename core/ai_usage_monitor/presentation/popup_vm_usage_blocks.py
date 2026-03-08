from __future__ import annotations

from typing import Any

from core.ai_usage_monitor.models import ProviderState
from core.ai_usage_monitor.presentation.popup_vm_common import format_tokens, format_usd


def extra_usage_vm(provider: ProviderState) -> dict[str, Any]:
    local = provider.local_usage
    if not local:
        return {"visible": False, "title": "Extra usage", "rows": []}

    rows: list[dict[str, Any]] = []
    if local.last_30_days_cost_usd is not None:
        rows.append(
            {
                "label": "This month",
                "value": format_usd(local.last_30_days_cost_usd),
                "meta": format_tokens(local.last_30_days_tokens),
            }
        )
    elif local.last_30_days_tokens is not None:
        rows.append(
            {
                "label": "Last 30 days",
                "value": format_tokens(local.last_30_days_tokens),
                "meta": None,
            }
        )

    return {"visible": len(rows) > 0, "title": "Extra usage", "rows": rows}


def cost_vm(provider: ProviderState) -> dict[str, Any]:
    local = provider.local_usage
    if not local:
        return {"visible": False, "title": "Cost", "rows": []}

    rows = [
        {
            "label": "Today",
            "value": _compose_cost_row(local.session_cost_usd, local.session_tokens),
            "meta": None,
        },
        {
            "label": "Last 30 days",
            "value": _compose_cost_row(
                local.last_30_days_cost_usd, local.last_30_days_tokens
            ),
            "meta": None,
        },
    ]
    return {"visible": True, "title": "Cost", "rows": rows}


def _compose_cost_row(cost: float | None, tokens: int | None) -> str:
    if cost is not None and tokens is not None:
        return f"{format_usd(cost)} · {format_tokens(tokens)}"
    if cost is not None:
        return format_usd(cost)
    if tokens is not None:
        return format_tokens(tokens)
    return "—"
