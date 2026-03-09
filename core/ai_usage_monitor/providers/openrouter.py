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
from core.ai_usage_monitor.shared.url_safety import env_flag_enabled, resolve_safe_url


DESCRIPTOR = ProviderDescriptor(
    id="openrouter",
    display_name="OpenRouter",
    short_name="OpenRouter",
    default_enabled=False,
    source_modes=("api",),
    config_fields=(
        ProviderConfigField(
            "apiKey", "API Key", secret=True, placeholder="sk-or-v1-..."
        ),
        ProviderConfigField(
            "apiUrl", "API URL", placeholder="https://openrouter.ai/api/v1"
        ),
    ),
    branding=ProviderBranding(
        icon_key="openrouter",
        asset_name="openrouter.svg",
        color="#6467F2",
        badge_text="OR",
    ),
    status_page_url="https://status.openrouter.ai/",
    usage_dashboard_default_url="https://openrouter.ai/activity",
    usage_dashboard_by_source=(("api", "https://openrouter.ai/activity"),),
    preferred_source_policy="api_first",
)


def _get_setting(settings: dict[str, Any] | None, key: str) -> str | None:
    if not settings:
        return None
    value = settings.get(key)
    if isinstance(value, str):
        normalized = value.strip()
        if normalized:
            return normalized
    return None


def _api_key(settings: dict[str, Any] | None) -> str | None:
    return _get_setting(settings, "apiKey") or os.environ.get("OPENROUTER_API_KEY")


def _base_url(settings: dict[str, Any] | None) -> str:
    default_url = "https://openrouter.ai/api/v1"
    candidate = (
        _get_setting(settings, "apiUrl")
        or os.environ.get("OPENROUTER_API_URL")
        or default_url
    )
    return resolve_safe_url(
        candidate,
        default_url=default_url,
        allowed_hosts=("openrouter.ai",),
        allow_unsafe=env_flag_enabled(
            os.environ.get("OPENROUTER_ALLOW_UNSAFE_API_URL")
        ),
    )


def collect_openrouter(
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

    base_url = _base_url(settings)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "X-Title": os.environ.get("OPENROUTER_X_TITLE", "AI Usage Monitor"),
    }
    http_referer = os.environ.get("OPENROUTER_HTTP_REFERER")
    if http_referer:
        headers["HTTP-Referer"] = http_referer

    try:
        credits_req = urllib.request.Request(f"{base_url}/credits", headers=headers)
        with urllib.request.urlopen(credits_req, timeout=10) as resp:
            credits_payload = json.loads(resp.read())

        key_req = urllib.request.Request(f"{base_url}/key", headers=headers)
        with urllib.request.urlopen(key_req, timeout=10) as resp:
            key_payload = json.loads(resp.read())

        credits_data = credits_payload.get("data") or {}
        total_credits = float(credits_data.get("total_credits") or 0)
        total_usage = float(credits_data.get("total_usage") or 0)
        balance = max(0.0, total_credits - total_usage)
        used_pct = (
            0.0
            if total_credits <= 0
            else min(100.0, max(0.0, (total_usage / total_credits) * 100.0))
        )

        key_data = key_payload.get("data") or {}
        rate_limit = key_data.get("rate_limit") or {}

        legacy = {
            "installed": True,
            "used_pct": round(used_pct),
            "balance": balance,
            "total_credits": total_credits,
            "rate_limit": rate_limit,
        }
        state = ProviderState(
            id=DESCRIPTOR.id,
            display_name=DESCRIPTOR.display_name,
            installed=True,
            authenticated=True,
            source="api",
            primary_metric=MetricWindow("Credits", used_pct, None),
            extras={
                "plan": f"Balance ${balance:.2f}",
                "rateLimit": rate_limit,
            },
        )
        return legacy, state
    except urllib.error.HTTPError as err:
        legacy = {
            "installed": True,
            **classify_http_failure("openrouter", err.code, read_http_error_body(err)),
        }
    except Exception as err:
        legacy = {"installed": True, **classify_exception_failure(err)}

    error_text = str(legacy.get("error") or "").strip() or None
    state = ProviderState(
        id=DESCRIPTOR.id,
        display_name=DESCRIPTOR.display_name,
        installed=True,
        authenticated=legacy.get("fail_reason") != "auth_required",
        status="error",
        source="api",
        error=error_text,
    )
    return legacy, state
