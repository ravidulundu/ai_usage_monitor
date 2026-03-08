from __future__ import annotations

import re
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any, TypedDict

from core.ai_usage_monitor.browser_cookies import import_cookie_header
from core.ai_usage_monitor.cookies import (
    cookie_header_from_settings,
    cookie_source_from_settings,
)
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
    id="amp",
    display_name="Amp",
    short_name="Amp",
    default_enabled=True,
    source_modes=("web",),
    config_fields=(
        ProviderConfigField(
            "cookieSource",
            "Cookie Source",
            kind="choice",
            options=("off", "manual", "auto"),
        ),
        ProviderConfigField(
            "manualCookieHeader",
            "Manual Cookie Header",
            secret=True,
            placeholder="session=...",
        ),
    ),
    branding=ProviderBranding(
        icon_key="amp", asset_name="amp.svg", color="#DC2626", badge_text="AM"
    ),
    status_page_url="https://status.ampcode.com/",
    usage_dashboard_default_url="https://ampcode.com/",
    usage_dashboard_by_source=(("web", "https://ampcode.com/"),),
    preferred_source_policy="web_first",
)


class AmpUsagePayload(TypedDict):
    quota: float
    used: float
    hourly_replenishment: float
    window_hours: float | None


def _first_capture(text: str, pattern: str, flags: int = 0) -> str | None:
    match = re.search(pattern, text, flags)
    return match.group(1).strip() if match else None


def parse_amp_html(html: str) -> AmpUsagePayload:
    lower = html.lower()
    if "sign in" in lower or "log in" in lower or "/login" in lower:
        raise PermissionError("Not logged in to Amp. Please log in via ampcode.com.")

    usage = None
    for token in ("freeTierUsage", "getFreeTierUsage"):
        token_index = html.find(token)
        if token_index == -1:
            continue
        brace_index = html.find("{", token_index)
        if brace_index == -1:
            continue
        depth = 0
        in_string = False
        escaped = False
        end_index = None
        for idx in range(brace_index, len(html)):
            char = html[idx]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
            else:
                if char == '"':
                    in_string = True
                elif char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        end_index = idx
                        break
        if end_index is None:
            continue
        usage = html[brace_index : end_index + 1]
        break

    if usage is None:
        raise ValueError("Missing Amp Free usage data.")

    def number(key: str) -> float | None:
        raw = _first_capture(
            usage, rf"['\"]?{re.escape(key)}['\"]?\s*:\s*([0-9]+(?:\.[0-9]+)?)"
        )
        return float(raw) if raw is not None else None

    quota = number("quota")
    used = number("used")
    hourly = number("hourlyReplenishment")
    window_hours = number("windowHours")
    if quota is None or used is None or hourly is None:
        raise ValueError("Missing Amp free-tier values.")

    return {
        "quota": quota,
        "used": used,
        "hourly_replenishment": hourly,
        "window_hours": window_hours,
    }


def collect_amp(
    settings: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], ProviderState]:
    source = cookie_source_from_settings(settings, default="off")
    if source == "off":
        return {"installed": False}, ProviderState(
            id=DESCRIPTOR.id,
            display_name=DESCRIPTOR.display_name,
            installed=False,
            source="web",
        )

    cookie_header = cookie_header_from_settings(
        settings, env_keys=("AMP_COOKIE_HEADER",)
    )
    source_label = "manual"
    if not cookie_header and source == "auto":
        result = import_cookie_header(
            domains=["ampcode.com", "www.ampcode.com"], cookie_names={"session"}
        )
        if result:
            cookie_header = result.header
            source_label = result.source
    if not cookie_header:
        return {"installed": False}, ProviderState(
            id=DESCRIPTOR.id,
            display_name=DESCRIPTOR.display_name,
            installed=False,
            source="web",
        )

    try:
        req = urllib.request.Request(
            "https://ampcode.com/settings",
            headers={
                "Cookie": cookie_header,
                "Accept": "text/html,application/xhtml+xml",
                "User-Agent": "AIUsageMonitor/1.0",
                "Referer": "https://ampcode.com/settings",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        parsed = parse_amp_html(html)
        quota = max(0.0, parsed["quota"])
        used = max(0.0, parsed["used"])
        percent = 0.0 if quota <= 0 else min(100.0, (used / quota) * 100.0)
        reset_at = None
        hourly = parsed["hourly_replenishment"]
        if hourly and used > 0:
            reset_at = (
                datetime.now(timezone.utc) + timedelta(hours=(used / hourly))
            ).isoformat()

        legacy = {
            "installed": True,
            "used_pct": round(percent),
            "quota": quota,
            "used": used,
            "window_hours": parsed["window_hours"],
            "reset_time": reset_at,
            "cookie_source": source_label,
        }
        state = ProviderState(
            id=DESCRIPTOR.id,
            display_name=DESCRIPTOR.display_name,
            installed=True,
            authenticated=True,
            source="web",
            primary_metric=MetricWindow("Amp Free", percent, reset_at),
            extras={"plan": "Amp Free", "model": source_label},
        )
        return legacy, state
    except PermissionError as err:
        legacy = {"installed": True, "error": str(err), "fail_reason": "auth_required"}
    except urllib.error.HTTPError as err:
        legacy = {
            "installed": True,
            **classify_http_failure("amp", err.code, read_http_error_body(err)),
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
        source="web",
        error=error_text,
    )
    return legacy, state
