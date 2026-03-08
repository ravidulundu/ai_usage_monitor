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
from core.ai_usage_monitor.status import fetch_statuspage


DESCRIPTOR = ProviderDescriptor(
    id="copilot",
    display_name="GitHub Copilot",
    short_name="Copilot",
    default_enabled=True,
    source_modes=("api",),
    config_fields=(
        ProviderConfigField("apiKey", "API Token", secret=True, placeholder="gho_..."),
    ),
    branding=ProviderBranding(
        icon_key="copilot", asset_name="copilot.svg", color="#A855F7", badge_text="CP"
    ),
    status_page_url="https://www.githubstatus.com/",
    usage_dashboard_default_url="https://github.com/settings/copilot",
    usage_dashboard_by_source=(("api", "https://github.com/settings/copilot"),),
    preferred_source_policy="api_first",
)


def _copilot_identity(payload: Any) -> dict[str, str]:
    account_id = ""
    email = ""

    if not isinstance(payload, dict):
        return {"account_id": "", "email": ""}

    user = payload.get("user") if isinstance(payload.get("user"), dict) else {}
    candidates = (
        payload,
        user,
    )
    for mapping in candidates:
        if not isinstance(mapping, dict):
            continue
        if not account_id:
            account_id = str(
                mapping.get("userLogin")
                or mapping.get("user_login")
                or mapping.get("login")
                or mapping.get("username")
                or mapping.get("accountId")
                or mapping.get("account_id")
                or ""
            ).strip()
        if not email:
            email = str(mapping.get("email") or "").strip()
    return {"account_id": account_id, "email": email}


def _token_from_settings(settings: dict[str, Any] | None) -> str | None:
    api_key = (settings or {}).get("apiKey")
    if isinstance(api_key, str) and api_key.strip():
        return api_key.strip()
    token = os.environ.get("COPILOT_API_TOKEN")
    if token and token.strip():
        return token.strip()
    return None


def _make_metric(snapshot: dict[str, Any] | None, label: str) -> MetricWindow | None:
    if not isinstance(snapshot, dict):
        return None
    remaining = snapshot.get("percentRemaining")
    if remaining is None:
        remaining = snapshot.get("percent_remaining")
    if remaining is None:
        return None
    used = max(0.0, 100.0 - float(remaining))
    return MetricWindow(label, used, None)


def collect_copilot(
    settings: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], ProviderState]:
    token = _token_from_settings(settings)
    if not token:
        return {"installed": False}, ProviderState(
            id=DESCRIPTOR.id,
            display_name=DESCRIPTOR.display_name,
            installed=False,
            source="api",
        )

    try:
        req = urllib.request.Request(
            "https://api.github.com/copilot_internal/user",
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/json",
                "Editor-Version": "vscode/1.96.2",
                "Editor-Plugin-Version": "copilot-chat/0.26.7",
                "User-Agent": "GitHubCopilotChat/0.26.7",
                "X-Github-Api-Version": "2025-04-01",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            payload_raw = json.loads(resp.read())
        payload: dict[str, Any] = payload_raw if isinstance(payload_raw, dict) else {}

        quota_raw = payload.get("quotaSnapshots")
        quota: dict[str, Any] = quota_raw if isinstance(quota_raw, dict) else {}
        identity = _copilot_identity(payload)
        primary = _make_metric(quota.get("premiumInteractions"), "Premium")
        secondary = _make_metric(quota.get("chat"), "Chat")
        plan = payload.get("copilotPlan") or payload.get("plan") or ""

        legacy = {
            "installed": True,
            "plan": plan,
            "account_id": identity["account_id"],
            "premium_used_pct": primary.used_pct if primary else None,
            "chat_used_pct": secondary.used_pct if secondary else None,
        }
        state = ProviderState(
            id=DESCRIPTOR.id,
            display_name=DESCRIPTOR.display_name,
            installed=True,
            authenticated=True,
            source="api",
            primary_metric=primary,
            secondary_metric=secondary,
            extras={
                "plan": str(plan).capitalize() if plan else "",
                **(
                    {"accountId": identity["account_id"]}
                    if identity["account_id"]
                    else {}
                ),
                **({"email": identity["email"]} if identity["email"] else {}),
            },
            incident=fetch_statuspage(
                "https://www.githubstatus.com", "https://www.githubstatus.com/"
            ),
        )
        return legacy, state
    except urllib.error.HTTPError as err:
        legacy = {
            "installed": True,
            **classify_http_failure("copilot", err.code, read_http_error_body(err)),
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
        incident=fetch_statuspage(
            "https://www.githubstatus.com", "https://www.githubstatus.com/"
        ),
    )
    return legacy, state
