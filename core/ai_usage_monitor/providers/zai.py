from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from core.ai_usage_monitor.models import MetricWindow, ProviderState
from core.ai_usage_monitor.providers.base import (
    ProviderBranding,
    ProviderConfigField,
    ProviderDescriptor,
)
from core.ai_usage_monitor.shared.http_failures import (
    classify_exception_failure,
    classify_http_failure,
    read_http_error_body,
)
from core.ai_usage_monitor.shared.time_utils import unix_to_iso


DESCRIPTOR = ProviderDescriptor(
    id="zai",
    display_name="z.ai",
    short_name="z.ai",
    default_enabled=True,
    source_modes=("api",),
    config_fields=(
        ProviderConfigField("apiKey", "API Key", secret=True),
        ProviderConfigField(
            "apiUrl",
            "Quota URL",
            placeholder="https://api.z.ai/api/monitor/usage/quota/limit",
        ),
    ),
    branding=ProviderBranding(
        icon_key="zai", asset_name="zai.svg", color="#E85A6A", badge_text="ZA"
    ),
    status_page_url="https://status.z.ai/",
    usage_dashboard_default_url="https://chat.z.ai/",
    usage_dashboard_by_source=(("api", "https://chat.z.ai/"),),
    preferred_source_policy="api_first",
)


def _api_key(settings: dict[str, Any] | None) -> str | None:
    api_key = (settings or {}).get("apiKey")
    if isinstance(api_key, str) and api_key.strip():
        return api_key.strip()
    return os.environ.get("Z_AI_API_KEY")


def _api_url(settings: dict[str, Any] | None) -> str:
    api_url = (settings or {}).get("apiUrl")
    if isinstance(api_url, str) and api_url.strip():
        return api_url.strip()
    return (
        os.environ.get("Z_AI_QUOTA_URL")
        or "https://api.z.ai/api/monitor/usage/quota/limit"
    )


def _window_minutes(limit: dict[str, Any]) -> int | None:
    unit = str(limit.get("timeUnit") or limit.get("unit") or "").lower()
    number = limit.get("window") or limit.get("duration") or limit.get("time")
    if not isinstance(number, (str, int, float)):
        return None
    try:
        value = int(number)
    except Exception:
        return None
    if unit.startswith("day"):
        return value * 24 * 60
    if unit.startswith("hour"):
        return value * 60
    if unit.startswith("minute"):
        return value
    return None


def collect_zai(
    settings: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], ProviderState]:
    api_key = _api_key(settings)
    if not api_key:
        return {"installed": False}, ProviderState(
            id=DESCRIPTOR.id,
            display_name=DESCRIPTOR.display_name,
            installed=False,
            source="api",
        )

    try:
        req = urllib.request.Request(
            _api_url(settings),
            headers={
                "authorization": f"Bearer {api_key}",
                "accept": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            payload_raw = json.loads(resp.read())
        payload: dict[str, Any] = payload_raw if isinstance(payload_raw, dict) else {}

        data_raw = payload.get("data")
        data: dict[str, Any] = data_raw if isinstance(data_raw, dict) else payload
        limits_raw = data.get("limits")
        limits = (
            [item for item in limits_raw if isinstance(item, dict)]
            if isinstance(limits_raw, list)
            else []
        )
        primary_limit = next(
            (
                item
                for item in limits
                if str(item.get("type")).upper() == "TOKENS_LIMIT"
            ),
            None,
        )
        secondary_limit = next(
            (item for item in limits if str(item.get("type")).upper() == "TIME_LIMIT"),
            None,
        )

        def make_metric(
            limit: dict[str, Any] | None, label: str
        ) -> MetricWindow | None:
            if not isinstance(limit, dict):
                return None
            used = float(limit.get("usedPercent") or limit.get("used_percent") or 0)
            reset = (
                unix_to_iso((limit.get("nextResetTime") or 0) / 1000)
                if limit.get("nextResetTime")
                else None
            )
            return MetricWindow(label, used, reset)

        plan = (
            data.get("planName")
            or data.get("plan")
            or data.get("plan_type")
            or data.get("packageName")
            or ""
        )
        usage_details = data.get("usageDetails") or []
        legacy = {
            "installed": True,
            "plan": plan,
            "primary_used_pct": primary_limit.get("usedPercent")
            if isinstance(primary_limit, dict)
            else None,
            "secondary_used_pct": secondary_limit.get("usedPercent")
            if isinstance(secondary_limit, dict)
            else None,
        }
        state = ProviderState(
            id=DESCRIPTOR.id,
            display_name=DESCRIPTOR.display_name,
            installed=True,
            authenticated=True,
            source="api",
            primary_metric=make_metric(primary_limit, "Tokens"),
            secondary_metric=make_metric(secondary_limit, "Time"),
            extras={"plan": plan, "buckets": usage_details},
        )
        return legacy, state
    except urllib.error.HTTPError as err:
        legacy = {
            "installed": True,
            **classify_http_failure("zai", err.code, read_http_error_body(err)),
        }
    except Exception as err:
        legacy = {"installed": True, **classify_exception_failure(err)}

    error_text = legacy.get("error")
    state = ProviderState(
        id=DESCRIPTOR.id,
        display_name=DESCRIPTOR.display_name,
        installed=True,
        authenticated=str(legacy.get("fail_reason") or "") != "auth_required",
        status="error",
        source="api",
        error=str(error_text) if error_text is not None else None,
    )
    return legacy, state
