from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from core.ai_usage_monitor.local_usage import scan_claude_local_usage
from core.ai_usage_monitor.models import MetricWindow, ProviderState
from core.ai_usage_monitor.providers.base import ProviderBranding, ProviderDescriptor
from core.ai_usage_monitor.shared.http_failures import (
    classify_exception_failure,
    classify_http_failure,
    read_http_error_body,
)
from core.ai_usage_monitor.status import fetch_statuspage


DESCRIPTOR = ProviderDescriptor(
    id="claude",
    display_name="Claude Code",
    short_name="Claude",
    branding=ProviderBranding(
        icon_key="claude", asset_name="claude.svg", color="#CC7C5E", badge_text="CC"
    ),
    status_page_url="https://status.claude.com/",
    usage_dashboard_default_url="https://claude.ai/",
    usage_dashboard_by_source=(
        ("api", "https://console.anthropic.com/"),
        ("oauth", "https://claude.ai/"),
        ("cli", "https://claude.ai/"),
    ),
    preferred_source_policy="local_first",
)


def _claude_account_identity(creds: dict[str, Any]) -> dict[str, str]:
    oauth = (
        creds.get("claudeAiOauth")
        if isinstance(creds.get("claudeAiOauth"), dict)
        else {}
    )
    if not isinstance(oauth, dict):
        oauth = {}
    user = oauth.get("user") if isinstance(oauth.get("user"), dict) else {}
    if not isinstance(user, dict):
        user = {}

    account_id = ""
    email = ""
    for mapping in (oauth, user, creds):
        if not account_id:
            account_id = str(
                mapping.get("accountId")
                or mapping.get("account_id")
                or mapping.get("userId")
                or mapping.get("user_id")
                or ""
            ).strip()
        if not email:
            email = str(
                mapping.get("email") or mapping.get("emailAddress") or ""
            ).strip()
    return {
        "account_id": account_id,
        "email": email,
    }


def collect_claude(
    settings: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], ProviderState]:
    _ = settings
    creds_path = Path.home() / ".claude" / ".credentials.json"
    legacy: dict[str, Any] = {"installed": False}
    identity: dict[str, str] = {"account_id": "", "email": ""}
    state = ProviderState(
        id=DESCRIPTOR.id,
        display_name=DESCRIPTOR.display_name,
        installed=False,
        source="oauth",
    )

    if not creds_path.exists():
        return legacy, state

    try:
        creds_raw = json.loads(creds_path.read_text())
        creds: dict[str, Any] = creds_raw if isinstance(creds_raw, dict) else {}
        identity = _claude_account_identity(creds)
        token = creds["claudeAiOauth"]["accessToken"]
        req = urllib.request.Request(
            "https://api.anthropic.com/api/oauth/usage",
            headers={
                "Authorization": f"Bearer {token}",
                "anthropic-beta": "oauth-2025-04-20",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data_raw = json.loads(resp.read())
        data: dict[str, Any] = data_raw if isinstance(data_raw, dict) else {}

        five_hour_raw = data.get("five_hour")
        five_hour: dict[str, Any] = (
            five_hour_raw if isinstance(five_hour_raw, dict) else {}
        )
        seven_day_raw = data.get("seven_day")
        seven_day: dict[str, Any] = (
            seven_day_raw if isinstance(seven_day_raw, dict) else {}
        )
        five_hour_pct = round(float(five_hour.get("utilization") or 0))
        five_hour_reset = (
            str(five_hour.get("resets_at")) if five_hour.get("resets_at") else None
        )
        seven_day_pct = (
            round(float(seven_day.get("utilization") or 0)) if seven_day else None
        )
        seven_day_reset = (
            str(seven_day.get("resets_at"))
            if seven_day and seven_day.get("resets_at")
            else None
        )
        legacy = {
            "installed": True,
            "five_hour_pct": five_hour_pct,
            "five_hour_reset": five_hour_reset,
            "seven_day_pct": seven_day_pct,
            "seven_day_reset": seven_day_reset,
        }
        state = ProviderState(
            id=DESCRIPTOR.id,
            display_name=DESCRIPTOR.display_name,
            installed=True,
            authenticated=True,
            source="oauth",
            local_usage=scan_claude_local_usage(),
            primary_metric=MetricWindow(
                "5h", legacy["five_hour_pct"], legacy["five_hour_reset"]
            ),
            secondary_metric=MetricWindow(
                "7d", legacy["seven_day_pct"], legacy["seven_day_reset"]
            )
            if legacy["seven_day_pct"] is not None
            else None,
            extras={
                **(
                    {"accountId": identity["account_id"]}
                    if identity["account_id"]
                    else {}
                ),
                **({"email": identity["email"]} if identity["email"] else {}),
            },
            incident=fetch_statuspage(
                "https://status.claude.com", "https://status.claude.com/"
            ),
        )
        return legacy, state
    except urllib.error.HTTPError as err:
        legacy = {
            "installed": True,
            **classify_http_failure("claude", err.code, read_http_error_body(err)),
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
        source="oauth",
        local_usage=scan_claude_local_usage(),
        error=str(error_text) if error_text is not None else None,
        extras={
            **(
                {"accountId": identity["account_id"]}
                if identity.get("account_id")
                else {}
            ),
            **({"email": identity["email"]} if identity.get("email") else {}),
        },
        incident=fetch_statuspage(
            "https://status.claude.com", "https://status.claude.com/"
        ),
    )
    return legacy, state
