from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from urllib.parse import urlencode, urlparse, urlunparse

from core.ai_usage_monitor.browser_cookies import import_cookie_header
from core.ai_usage_monitor.cookies import cookie_header_from_settings, cookie_source_from_settings, normalize_cookie_header
from core.ai_usage_monitor.models import MetricWindow, ProviderState
from core.ai_usage_monitor.providers.base import ProviderBranding, ProviderConfigField, ProviderDescriptor
from core.ai_usage_monitor.util import classify_exception_failure, classify_http_failure, read_http_error_body


DESCRIPTOR = ProviderDescriptor(
    id="minimax",
    display_name="MiniMax",
    default_enabled=True,
    source_modes=("auto", "web", "api"),
    config_fields=(
        ProviderConfigField("source", "Source", kind="choice", options=("auto", "web", "api")),
        ProviderConfigField("apiKey", "API Token", secret=True, placeholder="sk-cp-..."),
        ProviderConfigField("cookieSource", "Cookie Source", kind="choice", options=("off", "manual", "auto")),
        ProviderConfigField("manualCookieHeader", "Manual Cookie Header", secret=True, placeholder="Cookie: ..."),
        ProviderConfigField("region", "Region", kind="choice", options=("global", "cn")),
    ),
    branding=ProviderBranding(icon_key="minimax", asset_name="minimax.svg", color="#FE603C", badge_text="MM"),
)


def _region(settings: dict | None) -> str:
    region = (settings or {}).get("region")
    if region in {"global", "cn"}:
        return region
    return "global"


def _hosts(region: str):
    if region == "cn":
        return {
            "base": "https://platform.minimaxi.com",
            "api": "https://api.minimaxi.com",
        }
    return {
        "base": "https://platform.minimax.io",
        "api": "https://api.minimax.io",
    }


def _api_token(settings: dict | None) -> str | None:
    if settings and isinstance(settings.get("apiKey"), str) and settings.get("apiKey").strip():
        return settings.get("apiKey").strip()
    token = os.environ.get("MINIMAX_API_KEY")
    return token.strip() if token and token.strip() else None


def _extract_first(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else None


def parse_cookie_override(raw: str | None):
    if not isinstance(raw, str):
        return None
    cookie_line = _extract_first(r"(?:^|\n)\s*cookie:\s*([^\r\n]+)", raw)
    if cookie_line is None:
        cookie_line = _extract_first(r"(?:^|\n)\s*([A-Za-z0-9_\-]+=.+)", raw)
    normalized = normalize_cookie_header(cookie_line or raw)
    if not normalized:
        return None
    authorization_token = _extract_first(r"authorization:\s*bearer\s+([A-Za-z0-9._\-+=/]+)", raw or "")
    group_id = _extract_first(r"group[_]?id=([0-9]{4,})", raw or "")
    return {
        "cookieHeader": normalized,
        "authorizationToken": authorization_token,
        "groupId": group_id,
    }


def _cookie_override(settings: dict | None):
    if settings and isinstance(settings.get("manualCookieHeader"), str):
        parsed = parse_cookie_override(settings.get("manualCookieHeader"))
        if parsed:
            return parsed, "manual"
    for env_key in ("MINIMAX_COOKIE", "MINIMAX_COOKIE_HEADER"):
        parsed = parse_cookie_override(os.environ.get(env_key))
        if parsed:
            return parsed, env_key
    return None, None


def _auto_cookie(settings: dict | None, region: str):
    if cookie_source_from_settings(settings, default="off") != "auto":
        return None, None
    domains = ["platform.minimax.io", "minimax.io"] if region == "global" else ["platform.minimaxi.com", "minimaxi.com"]
    result = import_cookie_header(domains=domains, cookie_names=None)
    if not result:
        return None, None
    parsed = parse_cookie_override(result.header)
    if not parsed:
        parsed = {"cookieHeader": result.header, "authorizationToken": None, "groupId": None}
    return parsed, result.source


def _date_from_epoch(value):
    if value is None:
        return None
    try:
        raw = int(value)
    except Exception:
        return None
    if raw > 1_000_000_000_000:
        return datetime.fromtimestamp(raw / 1000, tz=timezone.utc)
    if raw > 1_000_000_000:
        return datetime.fromtimestamp(raw, tz=timezone.utc)
    return None


def parse_minimax_payload(payload: dict, now: datetime | None = None):
    now = now or datetime.now(timezone.utc)
    data = payload.get("data") or payload
    if isinstance(data, dict):
        base_resp = data.get("base_resp") or data.get("baseResp") or payload.get("base_resp") or payload.get("baseResp") or {}
        status_code = base_resp.get("status_code") or base_resp.get("statusCode")
        status_msg = base_resp.get("status_msg") or base_resp.get("statusMessage") or ""
        if status_code not in (None, 0, "0"):
            raise PermissionError(status_msg or f"status_code {status_code}")

        model_remains = data.get("model_remains") or data.get("modelRemains") or []
        if not model_remains and isinstance(payload.get("model_remains"), list):
            model_remains = payload.get("model_remains")
        if not model_remains:
            raise ValueError("Missing coding plan data.")
        first = model_remains[0]
        total = first.get("current_interval_total_count") or first.get("currentIntervalTotalCount")
        remaining = first.get("current_interval_usage_count") or first.get("currentIntervalUsageCount")
        total = int(total) if total is not None else None
        remaining = int(remaining) if remaining is not None else None
        used = None if total is None or remaining is None else max(0, total - remaining)
        used_pct = None if total is None or total <= 0 or used is None else min(100.0, (used / total) * 100.0)

        start = _date_from_epoch(first.get("start_time") or first.get("startTime"))
        end = _date_from_epoch(first.get("end_time") or first.get("endTime"))
        remains = first.get("remains_time") or first.get("remainsTime")
        window_minutes = None
        if start and end:
            delta = int((end - start).total_seconds() / 60)
            window_minutes = delta if delta > 0 else None
        resets_at = end if end and end > now else None
        if resets_at is None and remains:
            try:
                seconds = int(remains)
                if seconds > 1_000_000:
                    seconds = int(seconds / 1000)
                resets_at = now.timestamp() + seconds
                resets_at = datetime.fromtimestamp(resets_at, tz=timezone.utc)
            except Exception:
                resets_at = None

        plan_name = None
        for key in ("current_subscribe_title", "plan_name", "combo_title", "current_plan_title"):
            if data.get(key):
                plan_name = str(data.get(key)).strip()
                break
        return {
            "plan": plan_name,
            "total": total,
            "used": used,
            "remaining": remaining,
            "used_pct": used_pct,
            "window_minutes": window_minutes,
            "reset_at": resets_at.isoformat() if resets_at else None,
        }
    raise ValueError("Invalid MiniMax payload.")


def _api_remains_url(region: str):
    return _hosts(region)["api"] + "/v1/coding_plan/remains"


def _web_remains_url(region: str):
    return _hosts(region)["base"] + "/v1/api/openplatform/coding_plan/remains"


def _coding_plan_referer(region: str):
    return _hosts(region)["base"] + "/user-center/payment/coding-plan"


def _append_group_id(url: str, group_id: str | None) -> str:
    if not group_id:
        return url
    parsed = urlparse(url)
    query = parsed.query
    new_query = f"{query}&GroupId={group_id}" if query else f"GroupId={group_id}"
    return urlunparse(parsed._replace(query=new_query))


def collect_minimax(settings: dict | None = None) -> tuple[dict, ProviderState]:
    source = (settings or {}).get("source") or "auto"
    region = _region(settings)
    api_token = _api_token(settings)
    cookie_override, cookie_source = _cookie_override(settings)
    if not cookie_override:
        cookie_override, cookie_source = _auto_cookie(settings, region)

    if source == "api" or (source == "auto" and api_token):
        if not api_token:
            error = "MiniMax API token not found. Set apiKey or MINIMAX_API_KEY."
            return (
                {"installed": True, "error": error, "fail_reason": "missing_credentials"},
                ProviderState(
                    id=DESCRIPTOR.id,
                    display_name=DESCRIPTOR.display_name,
                    installed=True,
                    authenticated=False,
                    status="error",
                    source="api",
                    error=error,
                ),
            )
        try:
            request = urllib.request.Request(
                _api_remains_url(region),
                headers={
                    "Authorization": f"Bearer {api_token}",
                    "accept": "application/json",
                    "Content-Type": "application/json",
                    "MM-API-Source": "AIUsageMonitor",
                },
            )
            with urllib.request.urlopen(request, timeout=15) as resp:
                payload = json.loads(resp.read())
            parsed = parse_minimax_payload(payload)
            legacy = {
                "installed": True,
                "used_pct": round(parsed["used_pct"]) if parsed["used_pct"] is not None else None,
                "plan": parsed["plan"],
            }
            state = ProviderState(
                id=DESCRIPTOR.id,
                display_name=DESCRIPTOR.display_name,
                installed=True,
                authenticated=True,
                source="api",
                primary_metric=MetricWindow("Usage", parsed["used_pct"] or 0, parsed["reset_at"]) if parsed["used_pct"] is not None else None,
                extras={"plan": parsed["plan"] or ""},
            )
            return legacy, state
        except urllib.error.HTTPError as err:
            if source == "auto" and cookie_override:
                pass
            else:
                legacy = {"installed": True, **classify_http_failure("minimax", err.code, read_http_error_body(err))}
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
        except Exception as err:
            if not (source == "auto" and cookie_override):
                legacy = {"installed": True, **classify_exception_failure(err)}
                state = ProviderState(
                    id=DESCRIPTOR.id,
                    display_name=DESCRIPTOR.display_name,
                    installed=True,
                    authenticated=True,
                    status="error",
                    source="api",
                    error=legacy.get("error"),
                )
                return legacy, state

    if source in {"web", "auto"}:
        if not cookie_override:
            if source == "web":
                return {"installed": False}, ProviderState(id=DESCRIPTOR.id, display_name=DESCRIPTOR.display_name, installed=False, source="web")
            return {"installed": False}, ProviderState(id=DESCRIPTOR.id, display_name=DESCRIPTOR.display_name, installed=False, source="web")

        try:
            url = _append_group_id(_web_remains_url(region), cookie_override.get("groupId"))
            request = urllib.request.Request(
                url,
                headers={
                    "Cookie": cookie_override["cookieHeader"],
                    "accept": "application/json, text/plain, */*",
                    "x-requested-with": "XMLHttpRequest",
                    "User-Agent": "AIUsageMonitor/1.0",
                    "Origin": _hosts(region)["base"],
                    "Referer": _coding_plan_referer(region),
                    **({"Authorization": f"Bearer {cookie_override['authorizationToken']}"} if cookie_override.get("authorizationToken") else {}),
                },
            )
            with urllib.request.urlopen(request, timeout=15) as resp:
                text = resp.read().decode("utf-8", errors="replace")
            try:
                payload = json.loads(text)
            except Exception:
                payload = json.loads(text)
            parsed = parse_minimax_payload(payload)
            legacy = {
                "installed": True,
                "used_pct": round(parsed["used_pct"]) if parsed["used_pct"] is not None else None,
                "plan": parsed["plan"],
                "cookie_source": cookie_source,
            }
            state = ProviderState(
                id=DESCRIPTOR.id,
                display_name=DESCRIPTOR.display_name,
                installed=True,
                authenticated=True,
                source="web",
                primary_metric=MetricWindow("Usage", parsed["used_pct"] or 0, parsed["reset_at"]) if parsed["used_pct"] is not None else None,
                extras={"plan": parsed["plan"] or "", "model": cookie_source or ""},
            )
            return legacy, state
        except PermissionError as err:
            legacy = {"installed": True, "error": str(err), "fail_reason": "auth_required"}
        except urllib.error.HTTPError as err:
            legacy = {"installed": True, **classify_http_failure("minimax", err.code, read_http_error_body(err))}
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

    return {"installed": False}, ProviderState(id=DESCRIPTOR.id, display_name=DESCRIPTOR.display_name, installed=False, source=source)
