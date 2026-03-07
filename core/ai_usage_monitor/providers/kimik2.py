from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from core.ai_usage_monitor.models import MetricWindow, ProviderState
from core.ai_usage_monitor.providers.base import ProviderBranding, ProviderConfigField, ProviderDescriptor
from core.ai_usage_monitor.util import classify_exception_failure, classify_http_failure, read_http_error_body


DESCRIPTOR = ProviderDescriptor(
    id="kimik2",
    display_name="Kimi K2 API",
    short_name="Kimi K2",
    default_enabled=True,
    source_modes=("api",),
    config_fields=(
        ProviderConfigField("apiKey", "API Key", secret=True),
    ),
    branding=ProviderBranding(icon_key="kimik2", color="#1783FF", badge_text="K2"),
)


def _api_key(settings: dict | None) -> str | None:
    if settings and isinstance(settings.get("apiKey"), str) and settings.get("apiKey").strip():
        return settings.get("apiKey").strip()
    return os.environ.get("KIMI_K2_API_KEY") or os.environ.get("KIMI_API_KEY") or os.environ.get("KIMI_KEY")


def collect_kimik2(settings: dict | None = None) -> tuple[dict, ProviderState]:
    api_key = _api_key(settings)
    if not api_key:
        return {"installed": False}, ProviderState(id=DESCRIPTOR.id, display_name=DESCRIPTOR.display_name, installed=False, source="api")

    try:
        req = urllib.request.Request(
            "https://kimi-k2.ai/api/user/credits",
            headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            payload = json.loads(resp.read())
            remaining_header = resp.headers.get("X-Credits-Remaining")

        data = payload.get("data") or payload
        consumed = None
        remaining = None
        for key in ("consumed", "creditsConsumed", "used", "usage"):
            if data.get(key) is not None:
                consumed = float(data.get(key))
                break
        for key in ("remaining", "creditsRemaining", "balance"):
            if data.get(key) is not None:
                remaining = float(data.get(key))
                break
        if remaining is None and remaining_header:
            try:
                remaining = float(remaining_header)
            except Exception:
                remaining = None
        total = (consumed or 0) + (remaining or 0)
        used_pct = 0.0 if total <= 0 else min(100.0, max(0.0, ((consumed or 0) / total) * 100.0))

        legacy = {
            "installed": True,
            "consumed": consumed,
            "remaining": remaining,
            "used_pct": round(used_pct),
        }
        state = ProviderState(
            id=DESCRIPTOR.id,
            display_name=DESCRIPTOR.display_name,
            installed=True,
            authenticated=True,
            source="api",
            primary_metric=MetricWindow("Credits", used_pct, None),
            extras={"plan": f"Remaining {remaining}" if remaining is not None else ""},
        )
        return legacy, state
    except urllib.error.HTTPError as err:
        legacy = {"installed": True, **classify_http_failure("kimik2", err.code, read_http_error_body(err))}
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
