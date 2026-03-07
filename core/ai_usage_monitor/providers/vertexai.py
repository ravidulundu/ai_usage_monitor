from __future__ import annotations

import configparser
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from core.ai_usage_monitor.local_usage import scan_vertex_local_usage
from core.ai_usage_monitor.models import MetricWindow, ProviderState
from core.ai_usage_monitor.providers.base import ProviderBranding, ProviderConfigField, ProviderDescriptor
from core.ai_usage_monitor.util import classify_exception_failure, classify_http_failure, read_http_error_body


DESCRIPTOR = ProviderDescriptor(
    id="vertexai",
    display_name="Vertex AI",
    short_name="Vertex",
    default_enabled=True,
    source_modes=("oauth",),
    config_fields=(
        ProviderConfigField("projectId", "Project ID", placeholder="my-gcp-project"),
    ),
    branding=ProviderBranding(icon_key="vertexai", asset_name="vertexai.svg", color="#4285F4", badge_text="VA"),
)


def _adc_path() -> Path:
    return Path.home() / ".config" / "gcloud" / "application_default_credentials.json"


def _config_default_path() -> Path:
    return Path.home() / ".config" / "gcloud" / "configurations" / "config_default"


def _load_adc() -> dict | None:
    path = _adc_path()
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def _project_id_from_sources(settings: dict | None = None) -> str | None:
    if settings and isinstance(settings.get("projectId"), str) and settings.get("projectId").strip():
        return settings.get("projectId").strip()
    for env_key in ("GOOGLE_CLOUD_PROJECT", "GCLOUD_PROJECT", "CLOUDSDK_CORE_PROJECT"):
        value = os.environ.get(env_key)
        if value and value.strip():
            return value.strip()
    cfg_path = _config_default_path()
    if cfg_path.exists():
        parser = configparser.ConfigParser()
        try:
            parser.read(cfg_path)
            if parser.has_option("core", "project"):
                value = parser.get("core", "project").strip()
                if value:
                    return value
        except Exception:
            pass
    adc = _load_adc() or {}
    if isinstance(adc.get("quota_project_id"), str) and adc.get("quota_project_id").strip():
        return adc.get("quota_project_id").strip()
    return None


def _access_token_from_adc(adc: dict) -> str | None:
    token = adc.get("access_token")
    if isinstance(token, str) and token.strip():
        return token.strip()
    refresh_token = adc.get("refresh_token")
    client_id = adc.get("client_id")
    client_secret = adc.get("client_secret")
    token_uri = adc.get("token_uri") or "https://oauth2.googleapis.com/token"
    if not all(isinstance(value, str) and value for value in (refresh_token, client_id, client_secret)):
        return None
    data = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
    ).encode()
    req = urllib.request.Request(token_uri, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        payload = json.loads(resp.read())
    token = payload.get("access_token")
    if isinstance(token, str) and token.strip():
        return token.strip()
    return None


def _fetch_timeseries(access_token: str, project_id: str, metric: str) -> dict:
    url = (
        f"https://monitoring.googleapis.com/v3/projects/{project_id}/timeSeries"
        f"?filter={urllib.parse.quote(metric)}&view=FULL&pageSize=200"
    )
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read())


def _series_key(series: dict) -> tuple[str, str, str]:
    metric_labels = (series.get("metric") or {}).get("labels") or {}
    resource_labels = (series.get("resource") or {}).get("labels") or {}
    return (
        metric_labels.get("quota_metric", ""),
        metric_labels.get("limit_name", ""),
        resource_labels.get("location", ""),
    )


def _series_value(series: dict) -> float | None:
    points = series.get("points") or []
    if not points:
        return None
    value = (points[0].get("value") or {})
    for key in ("doubleValue", "int64Value"):
        raw = value.get(key)
        if raw is None:
            continue
        try:
            return float(raw)
        except Exception:
            return None
    return None


def _compute_highest_usage_percent(usage_payload: dict, limit_payload: dict) -> float | None:
    usage_series = usage_payload.get("timeSeries") or []
    limit_series = limit_payload.get("timeSeries") or []
    limits = {_series_key(series): _series_value(series) for series in limit_series}
    best = None
    for series in usage_series:
        key = _series_key(series)
        usage_value = _series_value(series)
        limit_value = limits.get(key)
        if usage_value is None or not limit_value or limit_value <= 0:
            continue
        percent = (usage_value / limit_value) * 100.0
        best = percent if best is None else max(best, percent)
    return best


def collect_vertexai(settings: dict | None = None) -> tuple[dict, ProviderState]:
    adc = _load_adc()
    if not adc:
        return {"installed": False}, ProviderState(id=DESCRIPTOR.id, display_name=DESCRIPTOR.display_name, installed=False, source="oauth")

    project_id = _project_id_from_sources(settings)
    if not project_id:
        legacy = {"installed": True, "error": "No Google Cloud project configured.", "fail_reason": "invalid_credentials"}
        state = ProviderState(
            id=DESCRIPTOR.id,
            display_name=DESCRIPTOR.display_name,
            installed=True,
            authenticated=False,
            status="error",
            source="oauth",
            local_usage=scan_vertex_local_usage(),
            error=legacy["error"],
        )
        return legacy, state

    try:
        access_token = _access_token_from_adc(adc)
        if not access_token:
            raise KeyError("access_token")

        usage_filter = 'metric.type="serviceruntime.googleapis.com/quota/allocation/usage" AND resource.type="consumer_quota" AND resource.labels.service="aiplatform.googleapis.com"'
        limit_filter = 'metric.type="serviceruntime.googleapis.com/quota/limit" AND resource.type="consumer_quota" AND resource.labels.service="aiplatform.googleapis.com"'
        usage_payload = _fetch_timeseries(access_token, project_id, usage_filter)
        limit_payload = _fetch_timeseries(access_token, project_id, limit_filter)
        highest = _compute_highest_usage_percent(usage_payload, limit_payload)

        legacy = {
            "installed": True,
            "project_id": project_id,
            "used_pct": round(highest) if highest is not None else None,
        }
        state = ProviderState(
            id=DESCRIPTOR.id,
            display_name=DESCRIPTOR.display_name,
            installed=True,
            authenticated=True,
            source="oauth",
            primary_metric=MetricWindow("Quota", highest or 0, None) if highest is not None else None,
            local_usage=scan_vertex_local_usage(),
            extras={"plan": project_id},
        )
        return legacy, state
    except urllib.error.HTTPError as err:
        legacy = {"installed": True, **classify_http_failure("vertexai", err.code, read_http_error_body(err))}
    except Exception as err:
        legacy = {"installed": True, **classify_exception_failure(err)}

    state = ProviderState(
        id=DESCRIPTOR.id,
        display_name=DESCRIPTOR.display_name,
        installed=True,
        authenticated=legacy.get("fail_reason") != "auth_required",
        status="error",
        source="oauth",
        local_usage=scan_vertex_local_usage(),
        error=legacy.get("error"),
        extras={"plan": project_id} if project_id else {},
    )
    return legacy, state
