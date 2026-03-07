from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path

from core.ai_usage_monitor.local_usage import scan_claude_local_usage
from core.ai_usage_monitor.models import MetricWindow, ProviderState
from core.ai_usage_monitor.providers.base import ProviderBranding, ProviderDescriptor
from core.ai_usage_monitor.status import fetch_statuspage
from core.ai_usage_monitor.util import classify_exception_failure, classify_http_failure, read_http_error_body


DESCRIPTOR = ProviderDescriptor(
    id="claude",
    display_name="Claude Code",
    short_name="Claude",
    branding=ProviderBranding(icon_key="claude", asset_name="claude.svg", color="#CC7C5E", badge_text="CC"),
)


def collect_claude(settings: dict | None = None) -> tuple[dict, ProviderState]:
    creds_path = Path.home() / ".claude" / ".credentials.json"
    legacy = {"installed": False}
    state = ProviderState(id=DESCRIPTOR.id, display_name=DESCRIPTOR.display_name, installed=False, source="oauth")

    if not creds_path.exists():
        return legacy, state

    try:
        creds = json.loads(creds_path.read_text())
        token = creds["claudeAiOauth"]["accessToken"]
        req = urllib.request.Request(
            "https://api.anthropic.com/api/oauth/usage",
            headers={
                "Authorization": f"Bearer {token}",
                "anthropic-beta": "oauth-2025-04-20",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())

        five_hour = data.get("five_hour") or {}
        seven_day = data.get("seven_day") or {}
        legacy = {
            "installed": True,
            "five_hour_pct": round(five_hour.get("utilization") or 0),
            "five_hour_reset": five_hour.get("resets_at"),
            "seven_day_pct": round(seven_day.get("utilization") or 0) if seven_day else None,
            "seven_day_reset": seven_day.get("resets_at") if seven_day else None,
        }
        state = ProviderState(
            id=DESCRIPTOR.id,
            display_name=DESCRIPTOR.display_name,
            installed=True,
            authenticated=True,
            source="oauth",
            local_usage=scan_claude_local_usage(),
            primary_metric=MetricWindow("5h", legacy["five_hour_pct"], legacy["five_hour_reset"]),
            secondary_metric=MetricWindow("7d", legacy["seven_day_pct"], legacy["seven_day_reset"])
            if legacy["seven_day_pct"] is not None
            else None,
            incident=fetch_statuspage("https://status.claude.com", "https://status.claude.com/"),
        )
        return legacy, state
    except urllib.error.HTTPError as err:
        legacy = {"installed": True, **classify_http_failure("claude", err.code, read_http_error_body(err))}
    except Exception as err:
        legacy = {"installed": True, **classify_exception_failure(err)}

    state = ProviderState(
        id=DESCRIPTOR.id,
        display_name=DESCRIPTOR.display_name,
        installed=True,
        authenticated=legacy.get("fail_reason") != "auth_required",
        status="error",
        source="oauth",
        local_usage=scan_claude_local_usage(),
        error=legacy.get("error"),
        incident=fetch_statuspage("https://status.claude.com", "https://status.claude.com/"),
    )
    return legacy, state
