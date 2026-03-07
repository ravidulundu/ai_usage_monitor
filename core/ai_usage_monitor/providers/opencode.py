from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from core.ai_usage_monitor.browser_cookies import import_cookie_header
from core.ai_usage_monitor.cookies import cookie_header_from_settings, cookie_source_from_settings
from core.ai_usage_monitor.models import MetricWindow, ProviderState
from core.ai_usage_monitor.providers.base import ProviderBranding, ProviderConfigField, ProviderDescriptor
from core.ai_usage_monitor.util import classify_exception_failure, classify_http_failure, read_http_error_body


DESCRIPTOR = ProviderDescriptor(
    id="opencode",
    display_name="OpenCode",
    default_enabled=True,
    source_modes=("web",),
    config_fields=(
        ProviderConfigField("cookieSource", "Cookie Source", kind="choice", options=("off", "manual", "auto")),
        ProviderConfigField("manualCookieHeader", "Manual Cookie Header", secret=True, placeholder="auth=..."),
        ProviderConfigField("workspaceID", "Workspace ID", placeholder="wrk_..."),
    ),
    branding=ProviderBranding(icon_key="opencode", asset_name="opencode.svg", color="#3B82F6", badge_text="OC"),
)


WORKSPACES_SERVER_ID = "def39973159c7f0483d8793a822b8dbb10d067e12c65455fcb4608459ba0234f"
SUBSCRIPTION_SERVER_ID = "7abeebee372f304e050aaaf92be863f4a86490e382f8c79db68fd94040d691b4"


def normalize_workspace_id(raw: str | None) -> str | None:
    if not isinstance(raw, str):
        return None
    value = raw.strip()
    if not value:
        return None
    if value.startswith("wrk_"):
        return value
    match = re.search(r"wrk_[A-Za-z0-9]+", value)
    return match.group(0) if match else None


def _cookie_header(settings: dict | None) -> tuple[str | None, str | None]:
    header = cookie_header_from_settings(settings, env_keys=("OPENCODE_COOKIE_HEADER",))
    if header:
        return header, "manual"

    if cookie_source_from_settings(settings, default="off") == "auto":
        result = import_cookie_header(
            domains=["opencode.ai", "app.opencode.ai"],
            cookie_names={"auth", "__Host-auth"},
        )
        if result:
            return result.header, result.source
    return None, None


def _looks_signed_out(text: str) -> bool:
    lower = text.lower()
    return "login" in lower or "sign in" in lower or "auth/authorize" in lower


def _extract_workspace_ids(text: str) -> list[str]:
    regex = re.compile(r'id\s*:\s*"?(wrk_[A-Za-z0-9]+)"?')
    ids = []
    for match in regex.finditer(text):
        workspace = match.group(1)
        if workspace not in ids:
            ids.append(workspace)
    return ids


def _collect_workspace_ids_json(obj, out: list[str]):
    if isinstance(obj, dict):
        for value in obj.values():
            _collect_workspace_ids_json(value, out)
    elif isinstance(obj, list):
        for value in obj:
            _collect_workspace_ids_json(value, out)
    elif isinstance(obj, str) and obj.startswith("wrk_") and obj not in out:
        out.append(obj)


def parse_workspace_ids(text: str) -> list[str]:
    ids = _extract_workspace_ids(text)
    if ids:
        return ids
    try:
        obj = json.loads(text)
    except Exception:
        return []
    _collect_workspace_ids_json(obj, ids)
    return ids


def _extract_number(text: str, pattern: str):
    match = re.search(pattern, text, re.IGNORECASE)
    return float(match.group(1)) if match else None


def _extract_int(text: str, pattern: str):
    match = re.search(pattern, text, re.IGNORECASE)
    return int(match.group(1)) if match else None


def _parse_usage_dict(obj) -> dict | None:
    if not isinstance(obj, dict):
        return None

    rolling = None
    weekly = None
    for key in ("rollingUsage", "rolling", "rolling_usage", "rollingWindow", "rolling_window"):
        if isinstance(obj.get(key), dict):
            rolling = obj.get(key)
            break
    for key in ("weeklyUsage", "weekly", "weekly_usage", "weeklyWindow", "weekly_window"):
        if isinstance(obj.get(key), dict):
            weekly = obj.get(key)
            break
    if rolling and weekly:
        return {"rolling": rolling, "weekly": weekly}

    for value in obj.values():
        nested = _parse_usage_dict(value)
        if nested:
            return nested
    return None


def parse_subscription_text(text: str, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    try:
        obj = json.loads(text)
    except Exception:
        obj = None

    if obj is not None:
        usage = _parse_usage_dict(obj)
        if usage:
            rolling = usage["rolling"]
            weekly = usage["weekly"]
            rolling_pct = float(rolling.get("usagePercent") or rolling.get("usedPercent") or rolling.get("percentUsed") or 0)
            weekly_pct = float(weekly.get("usagePercent") or weekly.get("usedPercent") or weekly.get("percentUsed") or 0)
            rolling_reset = int(rolling.get("resetInSec") or rolling.get("resetInSeconds") or 0)
            weekly_reset = int(weekly.get("resetInSec") or weekly.get("resetInSeconds") or 0)
            return {
                "rolling_pct": rolling_pct,
                "weekly_pct": weekly_pct,
                "rolling_reset_at": (now.timestamp() + rolling_reset),
                "weekly_reset_at": (now.timestamp() + weekly_reset),
            }

    rolling_pct = _extract_number(text, r"rollingUsage[^}]*?usagePercent\s*:\s*([0-9]+(?:\.[0-9]+)?)")
    weekly_pct = _extract_number(text, r"weeklyUsage[^}]*?usagePercent\s*:\s*([0-9]+(?:\.[0-9]+)?)")
    rolling_reset = _extract_int(text, r"rollingUsage[^}]*?resetInSec\s*:\s*([0-9]+)")
    weekly_reset = _extract_int(text, r"weeklyUsage[^}]*?resetInSec\s*:\s*([0-9]+)")
    if None in (rolling_pct, weekly_pct, rolling_reset, weekly_reset):
        raise ValueError("Missing usage fields.")
    return {
        "rolling_pct": rolling_pct,
        "weekly_pct": weekly_pct,
        "rolling_reset_at": (now.timestamp() + rolling_reset),
        "weekly_reset_at": (now.timestamp() + weekly_reset),
    }


def _server_url(server_id: str, args: list | None = None) -> str:
    if args:
        query = urllib.parse.urlencode({"id": server_id, "args": json.dumps(args)})
    else:
        query = urllib.parse.urlencode({"id": server_id})
    return f"https://opencode.ai/_server?{query}"


def _fetch_server_text(server_id: str, cookie_header: str, method: str = "GET", args: list | None = None, referer: str = "https://opencode.ai"):
    url = _server_url(server_id, args=args) if method.upper() == "GET" else "https://opencode.ai/_server"
    request = urllib.request.Request(url, method=method.upper())
    request.add_header("Cookie", cookie_header)
    request.add_header("X-Server-Id", server_id)
    request.add_header("X-Server-Instance", "server-fn:ai-usage-monitor")
    request.add_header("User-Agent", "AIUsageMonitor/1.0")
    request.add_header("Origin", "https://opencode.ai")
    request.add_header("Referer", referer)
    request.add_header("Accept", "text/javascript, application/json;q=0.9, */*;q=0.8")
    if method.upper() != "GET" and args is not None:
        body = json.dumps(args).encode()
        request.data = body
        request.add_header("Content-Type", "application/json")

    with urllib.request.urlopen(request, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")


def collect_opencode(settings: dict | None = None) -> tuple[dict, ProviderState]:
    source = cookie_source_from_settings(settings, default="off")
    if source == "off":
        return {"installed": False}, ProviderState(id=DESCRIPTOR.id, display_name=DESCRIPTOR.display_name, installed=False, source="web")

    cookie_header, cookie_source = _cookie_header(settings)
    if not cookie_header:
        return {"installed": False}, ProviderState(id=DESCRIPTOR.id, display_name=DESCRIPTOR.display_name, installed=False, source="web")

    workspace_id = normalize_workspace_id((settings or {}).get("workspaceID") or os.environ.get("CODEXBAR_OPENCODE_WORKSPACE_ID"))

    try:
        if not workspace_id:
            text = _fetch_server_text(WORKSPACES_SERVER_ID, cookie_header, method="GET", referer="https://opencode.ai")
            if _looks_signed_out(text):
                raise PermissionError("OpenCode session cookie is invalid or expired.")
            workspace_ids = parse_workspace_ids(text)
            if not workspace_ids:
                text = _fetch_server_text(WORKSPACES_SERVER_ID, cookie_header, method="POST", args=[], referer="https://opencode.ai")
                workspace_ids = parse_workspace_ids(text)
            if not workspace_ids:
                raise ValueError("Missing workspace id.")
            workspace_id = workspace_ids[0]

        referer = f"https://opencode.ai/workspace/{workspace_id}/billing"
        text = _fetch_server_text(SUBSCRIPTION_SERVER_ID, cookie_header, method="GET", args=[workspace_id], referer=referer)
        if _looks_signed_out(text):
            raise PermissionError("OpenCode session cookie is invalid or expired.")
        try:
            parsed = parse_subscription_text(text)
        except Exception:
            text = _fetch_server_text(SUBSCRIPTION_SERVER_ID, cookie_header, method="POST", args=[workspace_id], referer=referer)
            parsed = parse_subscription_text(text)

        legacy = {
            "installed": True,
            "rolling_used_pct": round(parsed["rolling_pct"]),
            "weekly_used_pct": round(parsed["weekly_pct"]),
            "workspace_id": workspace_id,
            "cookie_source": cookie_source,
        }
        state = ProviderState(
            id=DESCRIPTOR.id,
            display_name=DESCRIPTOR.display_name,
            installed=True,
            authenticated=True,
            source="web",
            primary_metric=MetricWindow("5h", parsed["rolling_pct"], datetime.fromtimestamp(parsed["rolling_reset_at"], tz=timezone.utc).isoformat()),
            secondary_metric=MetricWindow("7d", parsed["weekly_pct"], datetime.fromtimestamp(parsed["weekly_reset_at"], tz=timezone.utc).isoformat()),
            extras={"plan": workspace_id, "model": cookie_source or ""},
        )
        return legacy, state
    except PermissionError as err:
        legacy = {"installed": True, "error": str(err), "fail_reason": "auth_required"}
    except urllib.error.HTTPError as err:
        legacy = {"installed": True, **classify_http_failure("opencode", err.code, read_http_error_body(err))}
    except Exception as err:
        legacy = {"installed": True, **classify_exception_failure(err)}

    state = ProviderState(
        id=DESCRIPTOR.id,
        display_name=DESCRIPTOR.display_name,
        installed=True,
        authenticated=legacy.get("fail_reason") != "auth_required",
        status="error",
        source="web",
        error=legacy.get("error"),
    )
    return legacy, state
