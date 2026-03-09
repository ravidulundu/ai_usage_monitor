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


DESCRIPTOR = ProviderDescriptor(
    id="warp",
    display_name="Warp",
    default_enabled=True,
    source_modes=("api",),
    config_fields=(
        ProviderConfigField("apiKey", "API Key", secret=True, placeholder="wk-..."),
    ),
    branding=ProviderBranding(icon_key="warp", color="#938BB4", badge_text="WP"),
)


def _api_key(settings: dict[str, Any] | None) -> str | None:
    if settings:
        api_key_raw = settings.get("apiKey")
        if isinstance(api_key_raw, str):
            api_key = api_key_raw.strip()
            if api_key:
                return api_key
    return os.environ.get("WARP_API_KEY") or os.environ.get("WARP_TOKEN")


def collect_warp(
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

    query = {
        "operationName": "GetRequestLimitInfo",
        "query": "query GetRequestLimitInfo { requestLimitInfo { isUnlimited nextRefreshTime requestLimit requestsUsedSinceLastRefresh } }",
        "variables": {},
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    try:
        req = urllib.request.Request(
            "https://app.warp.dev/graphql/v2?op=GetRequestLimitInfo",
            data=json.dumps(query).encode(),
            headers=headers,
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            payload = json.loads(resp.read())

        info = (payload.get("data") or {}).get("requestLimitInfo") or {}
        is_unlimited = bool(info.get("isUnlimited"))
        request_limit = float(info.get("requestLimit") or 0)
        used = float(info.get("requestsUsedSinceLastRefresh") or 0)
        reset_time = info.get("nextRefreshTime")
        used_pct = (
            0.0
            if is_unlimited or request_limit <= 0
            else min(100.0, max(0.0, (used / request_limit) * 100.0))
        )

        legacy = {
            "installed": True,
            "used_pct": 0 if is_unlimited else round(used_pct),
            "reset_time": reset_time,
            "request_limit": request_limit,
            "used": used,
            "is_unlimited": is_unlimited,
        }
        state = ProviderState(
            id=DESCRIPTOR.id,
            display_name=DESCRIPTOR.display_name,
            installed=True,
            authenticated=True,
            source="api",
            primary_metric=MetricWindow(
                "Credits", 0 if is_unlimited else used_pct, reset_time
            ),
            extras={
                "plan": "Unlimited"
                if is_unlimited
                else f"{int(used)}/{int(request_limit)}"
            },
        )
        return legacy, state
    except urllib.error.HTTPError as err:
        legacy = {
            "installed": True,
            **classify_http_failure("warp", err.code, read_http_error_body(err)),
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
