from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from core.ai_usage_monitor.models import MetricWindow, ProviderState
from core.ai_usage_monitor.providers.base import ProviderBranding, ProviderConfigField, ProviderDescriptor
from core.ai_usage_monitor.util import classify_exception_failure, classify_http_failure, read_http_error_body, unix_to_iso


DESCRIPTOR = ProviderDescriptor(
    id="zai",
    display_name="z.ai",
    default_enabled=True,
    source_modes=("api",),
    config_fields=(
        ProviderConfigField("apiKey", "API Key", secret=True),
        ProviderConfigField("apiUrl", "Quota URL", placeholder="https://api.z.ai/api/monitor/usage/quota/limit"),
    ),
    branding=ProviderBranding(icon_key="zai", asset_name="zai.svg", color="#E85A6A", badge_text="ZA"),
)


def _api_key(settings: dict | None) -> str | None:
    if settings and isinstance(settings.get("apiKey"), str) and settings.get("apiKey").strip():
        return settings.get("apiKey").strip()
    return os.environ.get("Z_AI_API_KEY")


def _api_url(settings: dict | None) -> str:
    if settings and isinstance(settings.get("apiUrl"), str) and settings.get("apiUrl").strip():
        return settings.get("apiUrl").strip()
    return os.environ.get("Z_AI_QUOTA_URL") or "https://api.z.ai/api/monitor/usage/quota/limit"


def _window_minutes(limit: dict) -> int | None:
    unit = str(limit.get("timeUnit") or limit.get("unit") or "").lower()
    number = limit.get("window") or limit.get("duration") or limit.get("time")
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


def collect_zai(settings: dict | None = None) -> tuple[dict, ProviderState]:
    api_key = _api_key(settings)
    if not api_key:
        return {"installed": False}, ProviderState(id=DESCRIPTOR.id, display_name=DESCRIPTOR.display_name, installed=False, source="api")

    try:
        req = urllib.request.Request(
            _api_url(settings),
            headers={"authorization": f"Bearer {api_key}", "accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            payload = json.loads(resp.read())

        data = payload.get("data") or payload
        limits = data.get("limits") or []
        primary_limit = next((item for item in limits if str(item.get("type")).upper() == "TOKENS_LIMIT"), None)
        secondary_limit = next((item for item in limits if str(item.get("type")).upper() == "TIME_LIMIT"), None)

        def make_metric(limit, label):
            if not isinstance(limit, dict):
                return None
            used = float(limit.get("usedPercent") or limit.get("used_percent") or 0)
            reset = unix_to_iso((limit.get("nextResetTime") or 0) / 1000) if limit.get("nextResetTime") else None
            return MetricWindow(label, used, reset)

        plan = data.get("planName") or data.get("plan") or data.get("plan_type") or data.get("packageName") or ""
        usage_details = data.get("usageDetails") or []
        legacy = {
            "installed": True,
            "plan": plan,
            "primary_used_pct": primary_limit.get("usedPercent") if isinstance(primary_limit, dict) else None,
            "secondary_used_pct": secondary_limit.get("usedPercent") if isinstance(secondary_limit, dict) else None,
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
        legacy = {"installed": True, **classify_http_failure("zai", err.code, read_http_error_body(err))}
    except Exception as err:
        legacy = {"installed": True, **classify_exception_failure(err)}

    state = ProviderState(
        id=DESCRIPTOR.id,
        display_name=DESCRIPTOR.display_name,
        installed=True,
        authenticated=legacy.get("fail_reason") != "auth_required",
        status="error",
        source="api",
        error=legacy.get("error"),
    )
    return legacy, state
