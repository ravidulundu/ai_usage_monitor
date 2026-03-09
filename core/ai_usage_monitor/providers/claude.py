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

CLAUDE_USAGE_URL = "https://api.anthropic.com/api/oauth/usage"
CLAUDE_STATUS_API_URL = "https://status.claude.com"
CLAUDE_STATUS_PAGE_URL = "https://status.claude.com/"


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


def _claude_extras(identity: dict[str, str]) -> dict[str, Any]:
    return {
        **({"accountId": identity["account_id"]} if identity.get("account_id") else {}),
        **({"email": identity["email"]} if identity.get("email") else {}),
    }


def _claude_incident() -> dict[str, Any] | None:
    return fetch_statuspage(CLAUDE_STATUS_API_URL, CLAUDE_STATUS_PAGE_URL)


def _load_claude_credentials() -> dict[str, Any] | None:
    creds_path = Path.home() / ".claude" / ".credentials.json"
    if not creds_path.exists():
        return None
    try:
        creds_raw = json.loads(creds_path.read_text())
    except Exception:
        return {}
    return creds_raw if isinstance(creds_raw, dict) else {}


def _fetch_claude_usage(token: str) -> dict[str, Any]:
    req = urllib.request.Request(
        CLAUDE_USAGE_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "anthropic-beta": "oauth-2025-04-20",
        },
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data_raw = json.loads(resp.read())
    return data_raw if isinstance(data_raw, dict) else {}


def _usage_window(data: dict[str, Any], key: str) -> dict[str, Any]:
    raw_window = data.get(key)
    return raw_window if isinstance(raw_window, dict) else {}


def _build_claude_legacy(data: dict[str, Any]) -> dict[str, Any]:
    five_hour = _usage_window(data, "five_hour")
    seven_day = _usage_window(data, "seven_day")
    return {
        "installed": True,
        "five_hour_pct": round(float(five_hour.get("utilization") or 0)),
        "five_hour_reset": (
            str(five_hour.get("resets_at")) if five_hour.get("resets_at") else None
        ),
        "seven_day_pct": (
            round(float(seven_day.get("utilization") or 0)) if seven_day else None
        ),
        "seven_day_reset": (
            str(seven_day.get("resets_at"))
            if seven_day and seven_day.get("resets_at")
            else None
        ),
    }


def _claude_success_state(
    *,
    legacy: dict[str, Any],
    identity: dict[str, str],
    local_usage: Any,
    incident: dict[str, Any] | None,
) -> tuple[dict[str, Any], ProviderState]:
    state = ProviderState(
        id=DESCRIPTOR.id,
        display_name=DESCRIPTOR.display_name,
        installed=True,
        authenticated=True,
        source="oauth",
        local_usage=local_usage,
        primary_metric=MetricWindow(
            "5h", legacy["five_hour_pct"], legacy["five_hour_reset"]
        ),
        secondary_metric=MetricWindow(
            "7d", legacy["seven_day_pct"], legacy["seven_day_reset"]
        )
        if legacy["seven_day_pct"] is not None
        else None,
        extras=_claude_extras(identity),
        incident=incident,
    )
    return legacy, state


def _claude_error_state(
    *,
    legacy: dict[str, Any],
    identity: dict[str, str],
    local_usage: Any,
    incident: dict[str, Any] | None,
) -> tuple[dict[str, Any], ProviderState]:
    error_text = legacy.get("error")
    state = ProviderState(
        id=DESCRIPTOR.id,
        display_name=DESCRIPTOR.display_name,
        installed=True,
        authenticated=str(legacy.get("fail_reason") or "") != "auth_required",
        status="error",
        source="oauth",
        local_usage=local_usage,
        error=str(error_text) if error_text is not None else None,
        extras=_claude_extras(identity),
        incident=incident,
    )
    return legacy, state


def collect_claude(
    settings: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], ProviderState]:
    _ = settings
    legacy: dict[str, Any] = {"installed": False}
    identity: dict[str, str] = {"account_id": "", "email": ""}
    incident = _claude_incident()
    local_usage = scan_claude_local_usage()
    creds = _load_claude_credentials()
    if creds is None:
        return legacy, ProviderState(
            id=DESCRIPTOR.id,
            display_name=DESCRIPTOR.display_name,
            installed=False,
            source="oauth",
        )

    try:
        identity = _claude_account_identity(creds)
        token = creds["claudeAiOauth"]["accessToken"]
        legacy = _build_claude_legacy(_fetch_claude_usage(token))
        return _claude_success_state(
            legacy=legacy,
            identity=identity,
            local_usage=local_usage,
            incident=incident,
        )
    except urllib.error.HTTPError as err:
        legacy = {
            "installed": True,
            **classify_http_failure("claude", err.code, read_http_error_body(err)),
        }
    except Exception as err:
        legacy = {"installed": True, **classify_exception_failure(err)}
    return _claude_error_state(
        legacy=legacy,
        identity=identity,
        local_usage=local_usage,
        incident=incident,
    )
