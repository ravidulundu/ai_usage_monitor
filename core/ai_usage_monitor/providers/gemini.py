from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from core.ai_usage_monitor.models import MetricWindow, ProviderState
from core.ai_usage_monitor.providers.base import ProviderBranding, ProviderDescriptor
from core.ai_usage_monitor.shared.http_failures import (
    classify_exception_failure,
    classify_http_failure,
    read_http_error_body,
)
from core.ai_usage_monitor.shared.oauth import refresh_gemini_token
from core.ai_usage_monitor.status import fetch_google_workspace_status


DESCRIPTOR = ProviderDescriptor(
    id="gemini",
    display_name="Gemini CLI",
    short_name="Gemini",
    source_modes=("auto", "oauth"),
    branding=ProviderBranding(
        icon_key="gemini", asset_name="gemini.svg", color="#AB87EA", badge_text="GM"
    ),
    status_page_url="https://status.cloud.google.com/",
    usage_dashboard_default_url="https://aistudio.google.com/",
    usage_dashboard_by_source=(
        ("oauth", "https://aistudio.google.com/"),
        ("api", "https://aistudio.google.com/"),
    ),
    preferred_source_policy="auto",
)

_GEMINI_STATUS_PRODUCT_ID = "npdyhgECDJ6tB66MxXyo"
_GEMINI_STATUS_HISTORY_URL = (
    "https://www.google.com/appsstatus/dashboard/products/npdyhgECDJ6tB66MxXyo/history"
)
_GEMINI_MAX_RETRIES = 3
_GEMINI_SOURCE_ID = "oauth"


def _gemini_account_identity(creds: dict[str, Any]) -> dict[str, str]:
    account_id = ""
    email = ""
    for mapping in (
        creds,
        creds.get("user") if isinstance(creds.get("user"), dict) else {},
    ):
        if not isinstance(mapping, dict):
            continue
        if not account_id:
            account_id = str(
                mapping.get("account_id")
                or mapping.get("accountId")
                or mapping.get("sub")
                or mapping.get("user_id")
                or mapping.get("userId")
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


def _gemini_settings_path() -> Path:
    return Path.home() / ".gemini" / "settings.json"


def _current_model_name() -> str:
    path = _gemini_settings_path()
    if not path.exists():
        return ""
    try:
        payload_raw = json.loads(path.read_text())
    except Exception:
        return ""
    payload: dict[str, Any] = payload_raw if isinstance(payload_raw, dict) else {}
    model = (
        ((payload.get("model") or {}).get("name"))
        if isinstance(payload.get("model"), dict)
        else ""
    ) or ""
    return str(model).strip()


def _bucket_used_pct(bucket: dict[str, Any]) -> int:
    remaining = bucket.get("remainingFraction", 1.0)
    try:
        remaining_fraction = float(remaining)
    except Exception:
        remaining_fraction = 1.0
    return round((1.0 - remaining_fraction) * 100)


def _group_bucket_kind(model_id: str) -> str:
    model = (model_id or "").lower()
    if "pro" in model:
        return "pro"
    if "flash" in model:
        return "flash"
    return "other"


def _pick_bucket(buckets: list[dict[str, Any]], kind: str) -> dict[str, Any] | None:
    candidates = [
        bucket
        for bucket in buckets
        if _group_bucket_kind(bucket.get("modelId", "")) == kind
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda bucket: bucket.get("remainingFraction", 1.0))


def _gemini_incident() -> dict[str, Any] | None:
    return fetch_google_workspace_status(
        _GEMINI_STATUS_PRODUCT_ID,
        _GEMINI_STATUS_HISTORY_URL,
    )


def _gemini_creds_path() -> Path:
    return Path.home() / ".gemini" / "oauth_creds.json"


def _load_gemini_creds(path: Path) -> dict[str, Any]:
    payload_raw = json.loads(path.read_text())
    return payload_raw if isinstance(payload_raw, dict) else {}


def _gemini_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def _request_json(
    url: str, *, headers: dict[str, str], payload: dict[str, Any]
) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers=headers,
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        body = json.loads(response.read())
    return body if isinstance(body, dict) else {}


def _fetch_gemini_buckets(token: str) -> tuple[list[dict[str, Any]], str]:
    base = "https://cloudcode-pa.googleapis.com/v1internal"
    headers = _gemini_headers(token)
    load_payload = {
        "cloudaicompanionProject": None,
        "metadata": {
            "ideType": "IDE_UNSPECIFIED",
            "platform": "PLATFORM_UNSPECIFIED",
            "pluginType": "GEMINI",
        },
    }
    load_response = _request_json(
        f"{base}:loadCodeAssist",
        headers=headers,
        payload=load_payload,
    )
    project_id = load_response.get("cloudaicompanionProject")
    if not project_id:
        raise ValueError("No cloudaicompanionProject in loadCodeAssist response")

    quota_response = _request_json(
        f"{base}:retrieveUserQuota",
        headers=headers,
        payload={"project": project_id},
    )
    buckets = [
        bucket
        for bucket in quota_response.get("buckets", [])
        if isinstance(bucket, dict)
        and not str(bucket.get("modelId", "")).endswith("_vertex")
    ]
    return buckets, _current_model_name()


def _bucket_view(
    buckets: list[dict[str, Any]],
) -> tuple[
    dict[str, Any] | None,
    dict[str, Any] | None,
    str,
    str | None,
    int,
    str | None,
    int | None,
    str | None,
]:
    pro_bucket = _pick_bucket(buckets, "pro")
    flash_bucket = _pick_bucket(buckets, "flash")
    if not pro_bucket and not flash_bucket and buckets:
        pro_bucket = min(
            buckets, key=lambda bucket: bucket.get("remainingFraction", 1.0)
        )
    primary_bucket = pro_bucket or flash_bucket
    secondary_bucket = flash_bucket if pro_bucket and flash_bucket else None
    primary_label = (
        "Pro"
        if pro_bucket
        else ((primary_bucket or {}).get("modelId", "") or "Gemini quota")
    )
    secondary_label = "Flash" if secondary_bucket else None
    used_pct = _bucket_used_pct(primary_bucket) if primary_bucket else 0
    reset_time = (
        str(primary_bucket.get("resetTime"))
        if primary_bucket and primary_bucket.get("resetTime")
        else None
    )
    secondary_used_pct = (
        _bucket_used_pct(secondary_bucket) if secondary_bucket else None
    )
    secondary_reset_time = (
        str(secondary_bucket.get("resetTime"))
        if secondary_bucket and secondary_bucket.get("resetTime")
        else None
    )
    return (
        primary_bucket,
        secondary_bucket,
        primary_label,
        secondary_label,
        used_pct,
        reset_time,
        secondary_used_pct,
        secondary_reset_time,
    )


def _bucket_payload(buckets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "model": bucket.get("modelId", ""),
            "used_pct": _bucket_used_pct(bucket),
            "reset_time": bucket.get("resetTime"),
        }
        for bucket in buckets
    ]


def _identity_extras(
    identity: dict[str, str], retry_count: int | None = None
) -> dict[str, Any]:
    extras: dict[str, Any] = {}
    if retry_count is not None:
        extras["retryCount"] = retry_count
    if identity.get("account_id"):
        extras["accountId"] = identity["account_id"]
    if identity.get("email"):
        extras["email"] = identity["email"]
    return extras


def _gemini_success_response(
    identity: dict[str, str],
    buckets: list[dict[str, Any]],
    current_model: str,
) -> tuple[dict[str, Any], ProviderState]:
    (
        primary_bucket,
        secondary_bucket,
        primary_label,
        secondary_label,
        used_pct,
        reset_time,
        secondary_used_pct,
        secondary_reset_time,
    ) = _bucket_view(buckets)
    buckets_payload = _bucket_payload(buckets)
    legacy = {
        "installed": True,
        "authenticated": True,
        "used_pct": used_pct,
        "reset_time": reset_time,
        "model": current_model
        or (primary_bucket.get("modelId", "") if primary_bucket else ""),
        "primary_label": primary_label,
        "secondary_used_pct": secondary_used_pct,
        "secondary_reset_time": secondary_reset_time,
        "buckets": buckets_payload,
    }
    state = ProviderState(
        id=DESCRIPTOR.id,
        display_name=DESCRIPTOR.display_name,
        installed=True,
        authenticated=True,
        source=_GEMINI_SOURCE_ID,
        primary_metric=MetricWindow(primary_label, used_pct, reset_time)
        if primary_bucket
        else None,
        secondary_metric=MetricWindow(
            secondary_label,
            secondary_used_pct,
            secondary_reset_time,
        )
        if secondary_bucket and secondary_label and secondary_used_pct is not None
        else None,
        extras={
            "model": current_model or "",
            "buckets": buckets_payload,
            "primaryModel": primary_bucket.get("modelId", "") if primary_bucket else "",
            "secondaryModel": secondary_bucket.get("modelId", "")
            if secondary_bucket
            else "",
            **_identity_extras(identity),
        },
        incident=_gemini_incident(),
    )
    return legacy, state


def _gemini_error_response(
    *, last_error: dict[str, Any], retry_count: int, identity: dict[str, str]
) -> tuple[dict[str, Any], ProviderState]:
    authenticated = last_error.get("fail_reason") not in (
        "auth_required",
        "auth_failed",
    )
    legacy = {
        "installed": True,
        "authenticated": authenticated,
        "retry_count": retry_count,
        **last_error,
    }
    state = ProviderState(
        id=DESCRIPTOR.id,
        display_name=DESCRIPTOR.display_name,
        installed=True,
        authenticated=authenticated,
        status="error",
        source=_GEMINI_SOURCE_ID,
        error=str(legacy.get("error")) if legacy.get("error") is not None else None,
        extras=_identity_extras(identity, retry_count=retry_count),
        incident=_gemini_incident(),
    )
    return legacy, state


def _gemini_not_installed() -> tuple[dict[str, Any], ProviderState]:
    return (
        {"installed": False},
        ProviderState(
            id=DESCRIPTOR.id,
            display_name=DESCRIPTOR.display_name,
            installed=False,
            source=_GEMINI_SOURCE_ID,
        ),
    )


def _load_gemini_context(
    creds_path: Path,
) -> tuple[dict[str, Any], dict[str, str]]:
    creds = _load_gemini_creds(creds_path)
    return creds, _gemini_account_identity(creds)


def _collect_gemini_once(
    creds: dict[str, Any],
    identity: dict[str, str],
) -> tuple[dict[str, Any], dict[str, str], list[dict[str, Any]], str]:
    token = str(creds["access_token"])
    buckets, current_model = _fetch_gemini_buckets(token)
    return creds, identity, buckets, current_model


def _refresh_gemini_credentials(
    creds_path: Path,
    creds: dict[str, Any],
) -> tuple[bool, dict[str, Any]]:
    success, new_creds, refresh_error = refresh_gemini_token(creds_path, creds)
    if success and new_creds is not None:
        return True, new_creds
    return False, {
        "fail_reason": "auth_failed",
        "error": refresh_error,
        "http_code": 401,
    }


def _classify_gemini_http_error(
    *,
    err: urllib.error.HTTPError,
    creds_path: Path,
    creds: dict[str, Any],
    retry_count: int,
) -> tuple[bool, dict[str, Any]]:
    body = read_http_error_body(err)
    if (
        err.code == 401
        and retry_count < _GEMINI_MAX_RETRIES
        and creds.get("refresh_token")
    ):
        return _refresh_gemini_credentials(creds_path, creds)
    return False, classify_http_failure(
        "gemini", err.code, body, context={"creds": creds}
    )


def _gemini_unknown_error_response(
    retry_count: int,
) -> tuple[dict[str, Any], ProviderState]:
    legacy = {
        "installed": True,
        "authenticated": False,
        "error": f"Failed after {retry_count} attempts",
        "fail_reason": "unknown_error",
    }
    state = ProviderState(
        id=DESCRIPTOR.id,
        display_name=DESCRIPTOR.display_name,
        installed=True,
        authenticated=False,
        status="error",
        source=_GEMINI_SOURCE_ID,
        error=str(legacy["error"]),
        incident=_gemini_incident(),
    )
    return legacy, state


def collect_gemini(
    settings: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], ProviderState]:
    _ = settings
    creds_path = _gemini_creds_path()
    if not creds_path.exists():
        return _gemini_not_installed()

    identity: dict[str, str] = {"account_id": "", "email": ""}
    creds: dict[str, Any] = {}
    retry_count = 0
    last_error: dict[str, Any] | None = None

    while retry_count < _GEMINI_MAX_RETRIES:
        try:
            creds, identity = _load_gemini_context(creds_path)
            creds, identity, buckets, current_model = _collect_gemini_once(
                creds,
                identity,
            )
            return _gemini_success_response(identity, buckets, current_model)
        except urllib.error.HTTPError as err:
            retry_count += 1
            refreshed, error_payload = _classify_gemini_http_error(
                err=err,
                creds_path=creds_path,
                creds=creds,
                retry_count=retry_count,
            )
            if refreshed:
                continue
            last_error = error_payload
            break
        except Exception as err:
            retry_count += 1
            last_error = classify_exception_failure(err)
            if retry_count >= _GEMINI_MAX_RETRIES:
                break

    if last_error:
        return _gemini_error_response(
            last_error=last_error,
            retry_count=retry_count,
            identity=identity,
        )
    return _gemini_unknown_error_response(retry_count)
