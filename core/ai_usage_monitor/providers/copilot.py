from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from core.ai_usage_monitor.models import MetricWindow, ProviderState
from core.ai_usage_monitor.providers.base import ProviderBranding, ProviderConfigField, ProviderDescriptor
from core.ai_usage_monitor.status import fetch_statuspage
from core.ai_usage_monitor.util import classify_exception_failure, classify_http_failure, read_http_error_body


DESCRIPTOR = ProviderDescriptor(
    id="copilot",
    display_name="GitHub Copilot",
    short_name="Copilot",
    default_enabled=True,
    source_modes=("api",),
    config_fields=(
        ProviderConfigField("apiKey", "API Token", secret=True, placeholder="gho_..."),
    ),
    branding=ProviderBranding(icon_key="copilot", asset_name="copilot.svg", color="#A855F7", badge_text="CP"),
)


def _token_from_settings(settings: dict | None) -> str | None:
    if settings and isinstance(settings.get("apiKey"), str) and settings.get("apiKey").strip():
        return settings.get("apiKey").strip()
    token = os.environ.get("COPILOT_API_TOKEN")
    if token and token.strip():
        return token.strip()
    return None


def _make_metric(snapshot: dict | None, label: str) -> MetricWindow | None:
    if not isinstance(snapshot, dict):
        return None
    remaining = snapshot.get("percentRemaining")
    if remaining is None:
        remaining = snapshot.get("percent_remaining")
    if remaining is None:
        return None
    used = max(0.0, 100.0 - float(remaining))
    return MetricWindow(label, used, None)


def collect_copilot(settings: dict | None = None) -> tuple[dict, ProviderState]:
    token = _token_from_settings(settings)
    if not token:
        return {"installed": False}, ProviderState(id=DESCRIPTOR.id, display_name=DESCRIPTOR.display_name, installed=False, source="api")

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
            payload = json.loads(resp.read())

        quota = payload.get("quotaSnapshots") or {}
        primary = _make_metric(quota.get("premiumInteractions"), "Premium")
        secondary = _make_metric(quota.get("chat"), "Chat")
        plan = payload.get("copilotPlan") or payload.get("plan") or ""

        legacy = {
            "installed": True,
            "plan": plan,
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
            extras={"plan": str(plan).capitalize() if plan else ""},
            incident=fetch_statuspage("https://www.githubstatus.com", "https://www.githubstatus.com/"),
        )
        return legacy, state
    except urllib.error.HTTPError as err:
        legacy = {"installed": True, **classify_http_failure("copilot", err.code, read_http_error_body(err))}
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
        incident=fetch_statuspage("https://www.githubstatus.com", "https://www.githubstatus.com/"),
    )
    return legacy, state
