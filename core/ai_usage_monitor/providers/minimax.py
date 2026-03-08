from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, TypedDict
from urllib.parse import urlparse, urlunparse

from core.ai_usage_monitor.browser_cookies import import_cookie_header
from core.ai_usage_monitor.cookies import (
    cookie_source_from_settings,
    normalize_cookie_header,
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
    id="minimax",
    display_name="MiniMax",
    short_name="MiniMax",
    default_enabled=True,
    source_modes=("auto", "web", "api"),
    config_fields=(
        ProviderConfigField(
            "source", "Source", kind="choice", options=("auto", "web", "api")
        ),
        ProviderConfigField(
            "apiKey", "API Token", secret=True, placeholder="sk-cp-..."
        ),
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
            placeholder="Cookie: ...",
        ),
        ProviderConfigField(
            "region", "Region", kind="choice", options=("global", "cn")
        ),
    ),
    branding=ProviderBranding(
        icon_key="minimax", asset_name="minimax.svg", color="#FE603C", badge_text="MM"
    ),
    status_page_url="https://status.minimax.io/",
    usage_dashboard_default_url="https://platform.minimax.io/user-center/payment/coding-plan",
    usage_dashboard_by_source=(
        ("api", "https://platform.minimax.io/"),
        ("web", "https://platform.minimax.io/user-center/payment/coding-plan"),
    ),
    preferred_source_policy="auto",
)


class MiniMaxHosts(TypedDict):
    base: str
    api: str


class CookieOverride(TypedDict):
    cookieHeader: str
    authorizationToken: str | None
    groupId: str | None


class MiniMaxPayload(TypedDict):
    plan: str | None
    total: int | None
    used: int | None
    remaining: int | None
    used_pct: float | None
    window_minutes: int | None
    reset_at: str | None


def _normalize_payload_data(payload: dict[str, Any]) -> dict[str, Any]:
    data_raw = payload.get("data")
    if isinstance(data_raw, dict):
        return data_raw
    return payload


def _base_response(payload: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
    base_resp_raw = (
        data.get("base_resp")
        or data.get("baseResp")
        or payload.get("base_resp")
        or payload.get("baseResp")
        or {}
    )
    return base_resp_raw if isinstance(base_resp_raw, dict) else {}


def _model_remains(
    payload: dict[str, Any], data: dict[str, Any]
) -> list[dict[str, Any]]:
    model_remains_raw = data.get("model_remains") or data.get("modelRemains") or []
    if isinstance(model_remains_raw, list):
        normalized = [item for item in model_remains_raw if isinstance(item, dict)]
        if normalized:
            return normalized
    payload_model_remains = payload.get("model_remains")
    if isinstance(payload_model_remains, list):
        return [item for item in payload_model_remains if isinstance(item, dict)]
    return []


def _usage_values(first: dict[str, Any]) -> tuple[int | None, int | None, float | None]:
    total_raw = first.get("current_interval_total_count") or first.get(
        "currentIntervalTotalCount"
    )
    remaining_raw = first.get("current_interval_usage_count") or first.get(
        "currentIntervalUsageCount"
    )
    total = int(total_raw) if total_raw is not None else None
    remaining = int(remaining_raw) if remaining_raw is not None else None
    used = None if total is None or remaining is None else max(0, total - remaining)
    used_pct = (
        None
        if total is None or total <= 0 or used is None
        else min(100.0, (used / total) * 100.0)
    )
    return total, remaining, used_pct


def _resets_at_iso(first: dict[str, Any], now: datetime) -> str | None:
    end = _date_from_epoch(first.get("end_time") or first.get("endTime"))
    remains = first.get("remains_time") or first.get("remainsTime")
    resets_at = end if end and end > now else None
    if resets_at is None and remains:
        try:
            seconds = int(remains)
            if seconds > 1_000_000:
                seconds = int(seconds / 1000)
            reset_epoch = now.timestamp() + seconds
            resets_at = datetime.fromtimestamp(reset_epoch, tz=timezone.utc)
        except Exception:
            resets_at = None
    return resets_at.isoformat() if resets_at else None


def _window_minutes(first: dict[str, Any]) -> int | None:
    start = _date_from_epoch(first.get("start_time") or first.get("startTime"))
    end = _date_from_epoch(first.get("end_time") or first.get("endTime"))
    if not (start and end):
        return None
    delta = int((end - start).total_seconds() / 60)
    return delta if delta > 0 else None


def _plan_name(data: dict[str, Any]) -> str | None:
    for key in (
        "current_subscribe_title",
        "plan_name",
        "combo_title",
        "current_plan_title",
    ):
        value = data.get(key)
        if value:
            return str(value).strip()
    return None


def _region(settings: dict[str, Any] | None) -> str:
    region = (settings or {}).get("region")
    if region in {"global", "cn"}:
        return str(region)
    return "global"


def _hosts(region: str) -> MiniMaxHosts:
    if region == "cn":
        return {
            "base": "https://platform.minimaxi.com",
            "api": "https://api.minimaxi.com",
        }
    return {
        "base": "https://platform.minimax.io",
        "api": "https://api.minimax.io",
    }


def _api_token(settings: dict[str, Any] | None) -> str | None:
    api_key = (settings or {}).get("apiKey")
    if isinstance(api_key, str) and api_key.strip():
        return api_key.strip()
    token = os.environ.get("MINIMAX_API_KEY")
    return token.strip() if token and token.strip() else None


def _extract_first(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else None


def parse_cookie_override(raw: str | None) -> CookieOverride | None:
    if not isinstance(raw, str):
        return None
    cookie_line = _extract_first(r"(?:^|\n)\s*cookie:\s*([^\r\n]+)", raw)
    if cookie_line is None:
        cookie_line = _extract_first(r"(?:^|\n)\s*([A-Za-z0-9_\-]+=.+)", raw)
    normalized = normalize_cookie_header(cookie_line or raw)
    if not normalized:
        return None
    authorization_token = _extract_first(
        r"authorization:\s*bearer\s+([A-Za-z0-9._\-+=/]+)", raw or ""
    )
    group_id = _extract_first(r"group[_]?id=([0-9]{4,})", raw or "")
    return {
        "cookieHeader": normalized,
        "authorizationToken": authorization_token,
        "groupId": group_id,
    }


def _cookie_override(
    settings: dict[str, Any] | None,
) -> tuple[CookieOverride | None, str | None]:
    if settings and isinstance(settings.get("manualCookieHeader"), str):
        parsed = parse_cookie_override(settings.get("manualCookieHeader"))
        if parsed:
            return parsed, "manual"
    for env_key in ("MINIMAX_COOKIE", "MINIMAX_COOKIE_HEADER"):
        parsed = parse_cookie_override(os.environ.get(env_key))
        if parsed:
            return parsed, env_key
    return None, None


def _auto_cookie(
    settings: dict[str, Any] | None, region: str
) -> tuple[CookieOverride | None, str | None]:
    if cookie_source_from_settings(settings, default="off") != "auto":
        return None, None
    domains = (
        ["platform.minimax.io", "minimax.io"]
        if region == "global"
        else ["platform.minimaxi.com", "minimaxi.com"]
    )
    result = import_cookie_header(domains=domains, cookie_names=None)
    if not result:
        return None, None
    parsed = parse_cookie_override(result.header)
    if not parsed:
        parsed = {
            "cookieHeader": result.header,
            "authorizationToken": None,
            "groupId": None,
        }
    return parsed, result.source


def _date_from_epoch(value: Any) -> datetime | None:
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


def parse_minimax_payload(
    payload: dict[str, Any], now: datetime | None = None
) -> MiniMaxPayload:
    now = now or datetime.now(timezone.utc)
    data = _normalize_payload_data(payload)
    base_resp = _base_response(payload, data)
    status_code = base_resp.get("status_code") or base_resp.get("statusCode")
    status_msg = base_resp.get("status_msg") or base_resp.get("statusMessage") or ""
    if status_code not in (None, 0, "0"):
        raise PermissionError(status_msg or f"status_code {status_code}")

    remains = _model_remains(payload, data)
    if not remains:
        raise ValueError("Missing coding plan data.")
    first = remains[0]
    total, remaining, used_pct = _usage_values(first)
    used = None if total is None or remaining is None else max(0, total - remaining)

    return {
        "plan": _plan_name(data),
        "total": total,
        "used": used,
        "remaining": remaining,
        "used_pct": used_pct,
        "window_minutes": _window_minutes(first),
        "reset_at": _resets_at_iso(first, now),
    }


def _api_remains_url(region: str) -> str:
    return _hosts(region)["api"] + "/v1/coding_plan/remains"


def _web_remains_url(region: str) -> str:
    return _hosts(region)["base"] + "/v1/api/openplatform/coding_plan/remains"


def _coding_plan_referer(region: str) -> str:
    return _hosts(region)["base"] + "/user-center/payment/coding-plan"


def _append_group_id(url: str, group_id: str | None) -> str:
    if not group_id:
        return url
    parsed = urlparse(url)
    query = parsed.query
    new_query = f"{query}&GroupId={group_id}" if query else f"GroupId={group_id}"
    return urlunparse(parsed._replace(query=new_query))


def _minimax_metric(parsed: MiniMaxPayload) -> MetricWindow | None:
    if parsed["used_pct"] is None:
        return None
    return MetricWindow("Usage", parsed["used_pct"] or 0, parsed["reset_at"])


def _minimax_error_state(
    *, source: str, legacy: dict[str, Any], authenticated: bool
) -> ProviderState:
    return ProviderState(
        id=DESCRIPTOR.id,
        display_name=DESCRIPTOR.display_name,
        installed=True,
        authenticated=authenticated,
        status="error",
        source=source,
        error=str(legacy.get("error")) if legacy.get("error") is not None else None,
    )


def _collect_minimax_api(
    *,
    source: str,
    region: str,
    api_token: str,
    allow_web_fallback: bool,
) -> tuple[dict[str, Any], ProviderState] | None:
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
            payload_raw = json.loads(resp.read())
        payload = payload_raw if isinstance(payload_raw, dict) else {}
        parsed = parse_minimax_payload(payload)
        return {
            "installed": True,
            "used_pct": round(parsed["used_pct"])
            if parsed["used_pct"] is not None
            else None,
            "plan": parsed["plan"],
        }, ProviderState(
            id=DESCRIPTOR.id,
            display_name=DESCRIPTOR.display_name,
            installed=True,
            authenticated=True,
            source="api",
            primary_metric=_minimax_metric(parsed),
            extras={"plan": parsed["plan"] or ""},
        )
    except urllib.error.HTTPError as err:
        if allow_web_fallback:
            return None
        legacy = {
            "installed": True,
            **classify_http_failure("minimax", err.code, read_http_error_body(err)),
        }
        return legacy, _minimax_error_state(
            source="api",
            legacy=legacy,
            authenticated=str(legacy.get("fail_reason") or "") != "auth_required",
        )
    except Exception as err:
        if allow_web_fallback:
            return None
        legacy = {"installed": True, **classify_exception_failure(err)}
        return legacy, _minimax_error_state(
            source="api",
            legacy=legacy,
            authenticated=True,
        )


def _collect_minimax_web(
    *, region: str, cookie_override: CookieOverride, cookie_source: str | None
) -> tuple[dict[str, Any], ProviderState]:
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
                **(
                    {"Authorization": f"Bearer {cookie_override['authorizationToken']}"}
                    if cookie_override.get("authorizationToken")
                    else {}
                ),
            },
        )
        with urllib.request.urlopen(request, timeout=15) as resp:
            text = resp.read().decode("utf-8", errors="replace")
        payload_raw = json.loads(text)
        payload = payload_raw if isinstance(payload_raw, dict) else {}
        parsed = parse_minimax_payload(payload)
        return {
            "installed": True,
            "used_pct": round(parsed["used_pct"])
            if parsed["used_pct"] is not None
            else None,
            "plan": parsed["plan"],
            "cookie_source": cookie_source,
        }, ProviderState(
            id=DESCRIPTOR.id,
            display_name=DESCRIPTOR.display_name,
            installed=True,
            authenticated=True,
            source="web",
            primary_metric=_minimax_metric(parsed),
            extras={"plan": parsed["plan"] or "", "model": cookie_source or ""},
        )
    except PermissionError as err:
        legacy = {
            "installed": True,
            "error": str(err),
            "fail_reason": "auth_required",
        }
    except urllib.error.HTTPError as err:
        legacy = {
            "installed": True,
            **classify_http_failure("minimax", err.code, read_http_error_body(err)),
        }
    except Exception as err:
        legacy = {"installed": True, **classify_exception_failure(err)}
    return legacy, _minimax_error_state(
        source="web",
        legacy=legacy,
        authenticated=str(legacy.get("fail_reason") or "") != "auth_required",
    )


def collect_minimax(
    settings: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], ProviderState]:
    source = str((settings or {}).get("source") or "auto")
    region = _region(settings)
    api_token = _api_token(settings)
    cookie_override, cookie_source = _cookie_override(settings)
    if not cookie_override:
        cookie_override, cookie_source = _auto_cookie(settings, region)

    if source == "api":
        if not api_token:
            error = "MiniMax API token not found. Set apiKey or MINIMAX_API_KEY."
            return {
                "installed": True,
                "error": error,
                "fail_reason": "missing_credentials",
            }, _minimax_error_state(
                source="api",
                legacy={"error": error},
                authenticated=False,
            )
        api_result = _collect_minimax_api(
            source=source,
            region=region,
            api_token=api_token,
            allow_web_fallback=False,
        )
        if api_result is not None:
            return api_result

    if source == "auto" and api_token:
        api_result = _collect_minimax_api(
            source=source,
            region=region,
            api_token=api_token,
            allow_web_fallback=bool(cookie_override),
        )
        if api_result is not None:
            return api_result

    if source in {"web", "auto"}:
        if not cookie_override:
            return {"installed": False}, ProviderState(
                id=DESCRIPTOR.id,
                display_name=DESCRIPTOR.display_name,
                installed=False,
                source="web",
            )
        return _collect_minimax_web(
            region=region,
            cookie_override=cookie_override,
            cookie_source=cookie_source,
        )

    return {"installed": False}, ProviderState(
        id=DESCRIPTOR.id,
        display_name=DESCRIPTOR.display_name,
        installed=False,
        source=source,
    )
