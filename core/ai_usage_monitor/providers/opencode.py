from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.ai_usage_monitor.browser_cookies import import_cookie_header
from core.ai_usage_monitor.cli_detect import resolve_cli_binary
from core.ai_usage_monitor.cookies import (
    cookie_header_from_settings,
    cookie_source_from_settings,
)
from core.ai_usage_monitor.local_usage import scan_opencode_local_usage
from core.ai_usage_monitor.models import LocalUsageSnapshot, MetricWindow, ProviderState
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
    id="opencode",
    display_name="OpenCode",
    short_name="OpenCode",
    default_enabled=True,
    source_modes=("auto", "cli", "web"),
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
            placeholder="auth=...",
        ),
        ProviderConfigField("workspaceID", "Workspace ID", placeholder="wrk_..."),
    ),
    branding=ProviderBranding(
        icon_key="opencode", asset_name="opencode.svg", color="#3B82F6", badge_text="OC"
    ),
    status_page_url="https://status.opencode.ai/",
    usage_dashboard_default_url="https://opencode.ai/",
    usage_dashboard_by_source=(
        ("cli", "https://opencode.ai/"),
        ("web", "https://opencode.ai/"),
    ),
    preferred_source_policy="local_first",
)


WORKSPACES_SERVER_ID = (
    "def39973159c7f0483d8793a822b8dbb10d067e12c65455fcb4608459ba0234f"
)
SUBSCRIPTION_SERVER_ID = (
    "7abeebee372f304e050aaaf92be863f4a86490e382f8c79db68fd94040d691b4"
)


def _opencode_data_roots() -> tuple[Path, ...]:
    home = Path.home()
    return (
        home / ".local" / "share" / "opencode",
        home / ".config" / "opencode",
    )


def _opencode_auth_paths() -> tuple[Path, ...]:
    return tuple(root / "auth.json" for root in _opencode_data_roots())


def _has_local_opencode_install() -> bool:
    if resolve_cli_binary("opencode", env_var="AI_USAGE_MONITOR_OPENCODE_BIN"):
        return True
    if any(path.exists() for path in _opencode_auth_paths()):
        return True
    for root in _opencode_data_roots():
        if (root / "storage" / "message").exists():
            return True
    return False


def _local_auth_type() -> str | None:
    for path in _opencode_auth_paths():
        if not path.exists():
            continue
        try:
            payload_raw = json.loads(path.read_text())
        except Exception:
            continue

        if not isinstance(payload_raw, dict):
            continue
        payload: dict[str, Any] = payload_raw
        opencode_raw = payload.get("opencode")
        opencode: dict[str, Any] = (
            opencode_raw if isinstance(opencode_raw, dict) else {}
        )
        auth_type_raw = opencode.get("type") or payload.get("type")
        if isinstance(auth_type_raw, str) and auth_type_raw.strip():
            return auth_type_raw.strip()
    return None


def _local_cli_state(
    local_usage: LocalUsageSnapshot | None = None,
) -> tuple[dict[str, Any], ProviderState] | None:
    if not _has_local_opencode_install():
        return None

    local_usage = (
        local_usage if local_usage is not None else scan_opencode_local_usage()
    )
    local_auth_type = _local_auth_type()
    legacy = {
        "installed": True,
        "auth_type": local_auth_type,
        "session_tokens": local_usage.session_tokens if local_usage else None,
        "last_30_days_tokens": local_usage.last_30_days_tokens if local_usage else None,
    }
    state = ProviderState(
        id=DESCRIPTOR.id,
        display_name=DESCRIPTOR.display_name,
        installed=True,
        authenticated=True,
        status="ok",
        source="cli",
        local_usage=local_usage,
        extras={"plan": local_auth_type or "", "model": "local-cli"},
    )
    return legacy, state


def _uninstalled_state(source: str) -> tuple[dict[str, Any], ProviderState]:
    return {"installed": False}, ProviderState(
        id=DESCRIPTOR.id,
        display_name=DESCRIPTOR.display_name,
        installed=False,
        source=source,
    )


def _auto_local_cli_fallback(
    configured_source: str,
    local_usage: LocalUsageSnapshot | None = None,
) -> tuple[dict[str, Any], ProviderState] | None:
    if configured_source != "auto":
        return None
    return _local_cli_state(local_usage=local_usage)


def _configured_source(settings: dict[str, Any] | None) -> str:
    return str((settings or {}).get("source") or "auto")


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


def _cookie_header(settings: dict[str, Any] | None) -> tuple[str | None, str | None]:
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


def _workspace_id_from_settings(settings: dict[str, Any] | None) -> str | None:
    return normalize_workspace_id(
        (settings or {}).get("workspaceID")
        or os.environ.get("CODEXBAR_OPENCODE_WORKSPACE_ID")
    )


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


def _collect_workspace_ids_json(obj: Any, out: list[str]) -> None:
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


def _extract_number(text: str, pattern: str) -> float | None:
    match = re.search(pattern, text, re.IGNORECASE)
    return float(match.group(1)) if match else None


def _extract_int(text: str, pattern: str) -> int | None:
    match = re.search(pattern, text, re.IGNORECASE)
    return int(match.group(1)) if match else None


def _parse_usage_dict(obj: Any) -> dict[str, dict[str, Any]] | None:
    if not isinstance(obj, dict):
        return None

    rolling = None
    weekly = None
    for key in (
        "rollingUsage",
        "rolling",
        "rolling_usage",
        "rollingWindow",
        "rolling_window",
    ):
        if isinstance(obj.get(key), dict):
            rolling = obj.get(key)
            break
    for key in (
        "weeklyUsage",
        "weekly",
        "weekly_usage",
        "weeklyWindow",
        "weekly_window",
    ):
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


def parse_subscription_text(text: str, now: datetime | None = None) -> dict[str, float]:
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
            rolling_pct = float(
                rolling.get("usagePercent")
                or rolling.get("usedPercent")
                or rolling.get("percentUsed")
                or 0
            )
            weekly_pct = float(
                weekly.get("usagePercent")
                or weekly.get("usedPercent")
                or weekly.get("percentUsed")
                or 0
            )
            rolling_reset = int(
                rolling.get("resetInSec") or rolling.get("resetInSeconds") or 0
            )
            weekly_reset = int(
                weekly.get("resetInSec") or weekly.get("resetInSeconds") or 0
            )
            return {
                "rolling_pct": rolling_pct,
                "weekly_pct": weekly_pct,
                "rolling_reset_at": (now.timestamp() + rolling_reset),
                "weekly_reset_at": (now.timestamp() + weekly_reset),
            }

    rolling_pct_raw = _extract_number(
        text, r"rollingUsage[^}]*?usagePercent\s*:\s*([0-9]+(?:\.[0-9]+)?)"
    )
    weekly_pct_raw = _extract_number(
        text, r"weeklyUsage[^}]*?usagePercent\s*:\s*([0-9]+(?:\.[0-9]+)?)"
    )
    rolling_reset_raw = _extract_int(
        text, r"rollingUsage[^}]*?resetInSec\s*:\s*([0-9]+)"
    )
    weekly_reset_raw = _extract_int(text, r"weeklyUsage[^}]*?resetInSec\s*:\s*([0-9]+)")
    if None in (rolling_pct_raw, weekly_pct_raw, rolling_reset_raw, weekly_reset_raw):
        raise ValueError("Missing usage fields.")
    assert rolling_pct_raw is not None
    assert weekly_pct_raw is not None
    assert rolling_reset_raw is not None
    assert weekly_reset_raw is not None
    rolling_pct = float(rolling_pct_raw)
    weekly_pct = float(weekly_pct_raw)
    rolling_reset = int(rolling_reset_raw)
    weekly_reset = int(weekly_reset_raw)
    return {
        "rolling_pct": rolling_pct,
        "weekly_pct": weekly_pct,
        "rolling_reset_at": (now.timestamp() + rolling_reset),
        "weekly_reset_at": (now.timestamp() + weekly_reset),
    }


def _server_url(server_id: str, args: list[Any] | None = None) -> str:
    if args:
        query = urllib.parse.urlencode({"id": server_id, "args": json.dumps(args)})
    else:
        query = urllib.parse.urlencode({"id": server_id})
    return f"https://opencode.ai/_server?{query}"


def _fetch_server_text(
    server_id: str,
    cookie_header: str,
    method: str = "GET",
    args: list[Any] | None = None,
    referer: str = "https://opencode.ai",
) -> str:
    url = (
        _server_url(server_id, args=args)
        if method.upper() == "GET"
        else "https://opencode.ai/_server"
    )
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
        body = resp.read()
    if isinstance(body, bytes):
        return body.decode("utf-8", errors="replace")
    return str(body)


def _resolve_workspace_id(
    *, cookie_header: str, initial_workspace_id: str | None
) -> str:
    if initial_workspace_id:
        return initial_workspace_id
    text = _fetch_server_text(
        WORKSPACES_SERVER_ID,
        cookie_header,
        method="GET",
        referer="https://opencode.ai",
    )
    if _looks_signed_out(text):
        raise PermissionError("OpenCode session cookie is invalid or expired.")
    workspace_ids = parse_workspace_ids(text)
    if not workspace_ids:
        text = _fetch_server_text(
            WORKSPACES_SERVER_ID,
            cookie_header,
            method="POST",
            args=[],
            referer="https://opencode.ai",
        )
        workspace_ids = parse_workspace_ids(text)
    if not workspace_ids:
        raise ValueError("Missing workspace id.")
    return workspace_ids[0]


def _fetch_subscription_with_retry(
    *, cookie_header: str, workspace_id: str
) -> dict[str, float]:
    referer = f"https://opencode.ai/workspace/{workspace_id}/billing"
    text = _fetch_server_text(
        SUBSCRIPTION_SERVER_ID,
        cookie_header,
        method="GET",
        args=[workspace_id],
        referer=referer,
    )
    if _looks_signed_out(text):
        raise PermissionError("OpenCode session cookie is invalid or expired.")
    try:
        return parse_subscription_text(text)
    except Exception:
        text = _fetch_server_text(
            SUBSCRIPTION_SERVER_ID,
            cookie_header,
            method="POST",
            args=[workspace_id],
            referer=referer,
        )
        return parse_subscription_text(text)


def _opencode_success(
    *,
    workspace_id: str,
    cookie_source: str | None,
    parsed: dict[str, float],
    local_usage: LocalUsageSnapshot | None,
) -> tuple[dict[str, Any], ProviderState]:
    return {
        "installed": True,
        "rolling_used_pct": round(parsed["rolling_pct"]),
        "weekly_used_pct": round(parsed["weekly_pct"]),
        "workspace_id": workspace_id,
        "cookie_source": cookie_source,
    }, ProviderState(
        id=DESCRIPTOR.id,
        display_name=DESCRIPTOR.display_name,
        installed=True,
        authenticated=True,
        source="web",
        primary_metric=MetricWindow(
            "5h",
            parsed["rolling_pct"],
            datetime.fromtimestamp(
                parsed["rolling_reset_at"], tz=timezone.utc
            ).isoformat(),
        ),
        secondary_metric=MetricWindow(
            "7d",
            parsed["weekly_pct"],
            datetime.fromtimestamp(
                parsed["weekly_reset_at"], tz=timezone.utc
            ).isoformat(),
        ),
        local_usage=local_usage,
        extras={
            "plan": workspace_id,
            "model": cookie_source or "",
            "workspaceId": workspace_id,
            "accountId": workspace_id,
            "sessionId": workspace_id,
        },
    )


def _opencode_error_state(
    *,
    workspace_id: str | None,
    legacy: dict[str, Any],
    local_usage: LocalUsageSnapshot | None,
) -> ProviderState:
    return ProviderState(
        id=DESCRIPTOR.id,
        display_name=DESCRIPTOR.display_name,
        installed=True,
        authenticated=str(legacy.get("fail_reason") or "") != "auth_required",
        status="error",
        source="web",
        error=str(legacy.get("error")) if legacy.get("error") is not None else None,
        local_usage=local_usage,
        extras={
            **({"workspaceId": workspace_id} if workspace_id else {}),
            **({"accountId": workspace_id} if workspace_id else {}),
            **({"sessionId": workspace_id} if workspace_id else {}),
        },
    )


def _opencode_permission_error(err: PermissionError) -> dict[str, Any]:
    return {"installed": True, "error": str(err), "fail_reason": "auth_required"}


def _opencode_http_error(err: urllib.error.HTTPError) -> dict[str, Any]:
    return {
        "installed": True,
        **classify_http_failure("opencode", err.code, read_http_error_body(err)),
    }


def _opencode_exception_error(err: Exception) -> dict[str, Any]:
    return {"installed": True, **classify_exception_failure(err)}


def _collect_opencode_web(
    *,
    cookie_header: str,
    cookie_source: str | None,
    workspace_id: str | None,
) -> tuple[dict[str, Any], ProviderState]:
    resolved_workspace_id = _resolve_workspace_id(
        cookie_header=cookie_header,
        initial_workspace_id=workspace_id,
    )
    parsed = _fetch_subscription_with_retry(
        cookie_header=cookie_header,
        workspace_id=resolved_workspace_id,
    )
    local_usage = scan_opencode_local_usage()
    return _opencode_success(
        workspace_id=resolved_workspace_id,
        cookie_source=cookie_source,
        parsed=parsed,
        local_usage=local_usage,
    )


def collect_opencode(
    settings: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], ProviderState]:
    configured_source = _configured_source(settings)

    if configured_source == "cli":
        local_cli = _local_cli_state()
        return local_cli if local_cli else _uninstalled_state("cli")

    source = cookie_source_from_settings(settings, default="auto")
    if configured_source == "web" and source == "off":
        return _uninstalled_state("web")

    cookie_header, cookie_source = _cookie_header(settings)
    if not cookie_header:
        local_cli = _auto_local_cli_fallback(configured_source)
        return local_cli if local_cli else _uninstalled_state("web")

    workspace_id = _workspace_id_from_settings(settings)

    try:
        return _collect_opencode_web(
            cookie_header=cookie_header,
            cookie_source=cookie_source,
            workspace_id=workspace_id,
        )
    except PermissionError as err:
        legacy = _opencode_permission_error(err)
    except urllib.error.HTTPError as err:
        legacy = _opencode_http_error(err)
    except Exception as err:
        legacy = _opencode_exception_error(err)

    error_local_usage = scan_opencode_local_usage()
    local_cli = _auto_local_cli_fallback(
        configured_source, local_usage=error_local_usage
    )
    if local_cli:
        return local_cli

    return legacy, _opencode_error_state(
        workspace_id=workspace_id,
        legacy=legacy,
        local_usage=error_local_usage,
    )
