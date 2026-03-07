from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path

from core.ai_usage_monitor.models import MetricWindow, ProviderState
from core.ai_usage_monitor.providers.base import ProviderBranding, ProviderDescriptor
from core.ai_usage_monitor.status import fetch_google_workspace_status
from core.ai_usage_monitor.util import (
    classify_exception_failure,
    classify_http_failure,
    read_http_error_body,
    refresh_gemini_token,
)


DESCRIPTOR = ProviderDescriptor(
    id="gemini",
    display_name="Gemini CLI",
    short_name="Gemini",
    branding=ProviderBranding(icon_key="gemini", asset_name="gemini.svg", color="#AB87EA", badge_text="GM"),
)


def _gemini_settings_path() -> Path:
    return Path.home() / ".gemini" / "settings.json"


def _current_model_name() -> str:
    path = _gemini_settings_path()
    if not path.exists():
        return ""
    try:
        payload = json.loads(path.read_text())
    except Exception:
        return ""
    model = (((payload.get("model") or {}).get("name")) if isinstance(payload.get("model"), dict) else "") or ""
    return str(model).strip()


def _bucket_used_pct(bucket: dict) -> int:
    return round((1.0 - bucket.get("remainingFraction", 1.0)) * 100)


def _group_bucket_kind(model_id: str) -> str:
    model = (model_id or "").lower()
    if "pro" in model:
        return "pro"
    if "flash" in model:
        return "flash"
    return "other"


def _pick_bucket(buckets: list[dict], kind: str) -> dict | None:
    candidates = [bucket for bucket in buckets if _group_bucket_kind(bucket.get("modelId", "")) == kind]
    if not candidates:
        return None
    return min(candidates, key=lambda bucket: bucket.get("remainingFraction", 1.0))


def collect_gemini(settings: dict | None = None) -> tuple[dict, ProviderState]:
    creds_path = Path.home() / ".gemini" / "oauth_creds.json"
    legacy = {"installed": False}
    state = ProviderState(id=DESCRIPTOR.id, display_name=DESCRIPTOR.display_name, installed=False, source="api")

    if not creds_path.exists():
        return legacy, state

    creds = {}
    max_retries = 3
    retry_count = 0
    last_error = None

    while retry_count < max_retries:
        try:
            creds = json.loads(creds_path.read_text())
            token = creds["access_token"]

            base = "https://cloudcode-pa.googleapis.com/v1internal"
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

            load_body = json.dumps(
                {
                    "cloudaicompanionProject": None,
                    "metadata": {
                        "ideType": "IDE_UNSPECIFIED",
                        "platform": "PLATFORM_UNSPECIFIED",
                        "pluginType": "GEMINI",
                    },
                }
            ).encode()
            req = urllib.request.Request(f"{base}:loadCodeAssist", data=load_body, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                load_res = json.loads(resp.read())

            project_id = load_res.get("cloudaicompanionProject")
            if not project_id:
                raise ValueError("No cloudaicompanionProject in loadCodeAssist response")

            quota_body = json.dumps({"project": project_id}).encode()
            req = urllib.request.Request(f"{base}:retrieveUserQuota", data=quota_body, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                quota_res = json.loads(resp.read())

            buckets = [bucket for bucket in quota_res.get("buckets", []) if not bucket.get("modelId", "").endswith("_vertex")]
            current_model = _current_model_name()
            pro_bucket = _pick_bucket(buckets, "pro")
            flash_bucket = _pick_bucket(buckets, "flash")

            if not pro_bucket and not flash_bucket and buckets:
                pro_bucket = min(buckets, key=lambda bucket: bucket.get("remainingFraction", 1.0))

            primary_bucket = pro_bucket or flash_bucket
            secondary_bucket = flash_bucket if pro_bucket and flash_bucket else None
            primary_label = "Pro" if pro_bucket else ((primary_bucket or {}).get("modelId", "") or "Gemini quota")
            secondary_label = "Flash" if secondary_bucket else None
            used_pct = _bucket_used_pct(primary_bucket) if primary_bucket else 0
            reset_time = primary_bucket.get("resetTime") if primary_bucket else None

            legacy = {
                "installed": True,
                "authenticated": True,
                "used_pct": used_pct,
                "reset_time": reset_time,
                "model": current_model or (primary_bucket.get("modelId", "") if primary_bucket else ""),
                "primary_label": primary_label,
                "secondary_used_pct": _bucket_used_pct(secondary_bucket) if secondary_bucket else None,
                "secondary_reset_time": secondary_bucket.get("resetTime") if secondary_bucket else None,
                "buckets": [
                    {
                        "model": bucket.get("modelId", ""),
                        "used_pct": _bucket_used_pct(bucket),
                        "reset_time": bucket.get("resetTime"),
                    }
                    for bucket in buckets
                ],
            }
            state = ProviderState(
                id=DESCRIPTOR.id,
                display_name=DESCRIPTOR.display_name,
                installed=True,
                authenticated=True,
                source="api",
                primary_metric=MetricWindow(primary_label, used_pct, reset_time) if primary_bucket else None,
                secondary_metric=MetricWindow(
                    secondary_label,
                    legacy["secondary_used_pct"],
                    legacy["secondary_reset_time"],
                ) if secondary_bucket and secondary_label else None,
                extras={
                    "model": current_model or "",
                    "buckets": legacy["buckets"],
                    "primaryModel": primary_bucket.get("modelId", "") if primary_bucket else "",
                    "secondaryModel": secondary_bucket.get("modelId", "") if secondary_bucket else "",
                },
                incident=fetch_google_workspace_status(
                    "npdyhgECDJ6tB66MxXyo",
                    "https://www.google.com/appsstatus/dashboard/products/npdyhgECDJ6tB66MxXyo/history",
                ),
            )
            return legacy, state

        except urllib.error.HTTPError as err:
            retry_count += 1
            body = read_http_error_body(err)
            if err.code == 401 and retry_count < max_retries and creds.get("refresh_token"):
                success, new_creds, refresh_error = refresh_gemini_token(creds_path, creds)
                if success:
                    creds = new_creds
                    continue
                last_error = {"fail_reason": "auth_failed", "error": refresh_error, "http_code": 401}
                if retry_count >= max_retries:
                    break
                continue
            last_error = classify_http_failure("gemini", err.code, body, context={"creds": creds})
            break
        except Exception as err:
            retry_count += 1
            last_error = classify_exception_failure(err)
            if retry_count >= max_retries:
                break

    if last_error:
        legacy = {
            "installed": True,
            "authenticated": last_error.get("fail_reason") not in ("auth_required", "auth_failed"),
            "retry_count": retry_count,
            **last_error,
        }
        state = ProviderState(
            id=DESCRIPTOR.id,
            display_name=DESCRIPTOR.display_name,
            installed=True,
            authenticated=legacy["authenticated"],
            status="error",
            source="api",
            error=legacy.get("error"),
            extras={"retryCount": retry_count},
            incident=fetch_google_workspace_status(
                "npdyhgECDJ6tB66MxXyo",
                "https://www.google.com/appsstatus/dashboard/products/npdyhgECDJ6tB66MxXyo/history",
            ),
        )
        return legacy, state

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
        source="api",
        error=legacy["error"],
        incident=fetch_google_workspace_status(
            "npdyhgECDJ6tB66MxXyo",
            "https://www.google.com/appsstatus/dashboard/products/npdyhgECDJ6tB66MxXyo/history",
        ),
    )
    return legacy, state
