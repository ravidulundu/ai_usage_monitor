from __future__ import annotations

import configparser
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from core.ai_usage_monitor.local_usage import scan_vertex_local_usage
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
    id="vertexai",
    display_name="Vertex AI",
    short_name="Vertex",
    default_enabled=True,
    source_modes=("oauth",),
    config_fields=(
        ProviderConfigField("projectId", "Project ID", placeholder="my-gcp-project"),
    ),
    branding=ProviderBranding(
        icon_key="vertexai", asset_name="vertexai.svg", color="#4285F4", badge_text="VA"
    ),
    status_page_url="https://status.cloud.google.com/",
    usage_dashboard_default_url="https://console.cloud.google.com/vertex-ai",
    usage_dashboard_by_source=(
        ("oauth", "https://console.cloud.google.com/vertex-ai"),
    ),
    preferred_source_policy="local_first",
)


def _adc_path() -> Path:
    return Path.home() / ".config" / "gcloud" / "application_default_credentials.json"


def _config_default_path() -> Path:
    return Path.home() / ".config" / "gcloud" / "configurations" / "config_default"


def _load_adc() -> dict[str, Any] | None:
    path = _adc_path()
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text())
        return payload if isinstance(payload, dict) else None
    except Exception:
        return None


def _project_id_from_sources(settings: dict[str, Any] | None = None) -> str | None:
    project_id = (settings or {}).get("projectId")
    if isinstance(project_id, str) and project_id.strip():
        return project_id.strip()
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
    quota_project = adc.get("quota_project_id")
    if isinstance(quota_project, str) and quota_project.strip():
        return quota_project.strip()
    return None


def _access_token_from_adc(adc: dict[str, Any]) -> str | None:
    token = adc.get("access_token")
    if isinstance(token, str) and token.strip():
        return token.strip()
    refresh_token = adc.get("refresh_token")
    client_id = adc.get("client_id")
    client_secret = adc.get("client_secret")
    token_uri = adc.get("token_uri") or "https://oauth2.googleapis.com/token"
    if not all(
        isinstance(value, str) and value
        for value in (refresh_token, client_id, client_secret)
    ):
        return None
    data = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
    ).encode()
    req = urllib.request.Request(
        token_uri,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        payload = json.loads(resp.read())
    token = payload.get("access_token")
    if isinstance(token, str) and token.strip():
        return token.strip()
    return None


def _fetch_timeseries(
    access_token: str, project_id: str, metric: str
) -> dict[str, Any]:
    url = (
        f"https://monitoring.googleapis.com/v3/projects/{project_id}/timeSeries"
        f"?filter={urllib.parse.quote(metric)}&view=FULL&pageSize=200"
    )
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        payload = json.loads(resp.read())
    return payload if isinstance(payload, dict) else {}


def _series_key(series: dict[str, Any]) -> tuple[str, str, str]:
    metric_raw = series.get("metric")
    metric = metric_raw if isinstance(metric_raw, dict) else {}
    metric_labels_raw = metric.get("labels")
    metric_labels = metric_labels_raw if isinstance(metric_labels_raw, dict) else {}
    resource_raw = series.get("resource")
    resource = resource_raw if isinstance(resource_raw, dict) else {}
    resource_labels_raw = resource.get("labels")
    resource_labels = (
        resource_labels_raw if isinstance(resource_labels_raw, dict) else {}
    )
    return (
        str(metric_labels.get("quota_metric") or ""),
        str(metric_labels.get("limit_name") or ""),
        str(resource_labels.get("location") or ""),
    )


def _series_value(series: dict[str, Any]) -> float | None:
    points_raw = series.get("points")
    points = points_raw if isinstance(points_raw, list) else []
    if not points:
        return None
    first = points[0]
    if not isinstance(first, dict):
        return None
    value_raw = first.get("value")
    value = value_raw if isinstance(value_raw, dict) else {}
    for key in ("doubleValue", "int64Value"):
        raw = value.get(key)
        if raw is None:
            continue
        try:
            return float(raw)
        except Exception:
            return None
    return None


def _compute_highest_usage_percent(
    usage_payload: dict[str, Any], limit_payload: dict[str, Any]
) -> float | None:
    usage_raw = usage_payload.get("timeSeries")
    usage_series = (
        [item for item in usage_raw if isinstance(item, dict)]
        if isinstance(usage_raw, list)
        else []
    )
    limit_raw = limit_payload.get("timeSeries")
    limit_series = (
        [item for item in limit_raw if isinstance(item, dict)]
        if isinstance(limit_raw, list)
        else []
    )
    limits: dict[tuple[str, str, str], float | None] = {}
    for series in limit_series:
        limits[_series_key(series)] = _series_value(series)
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


def collect_vertexai(
    settings: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], ProviderState]:
    adc = _load_adc()
    if not adc:
        return {"installed": False}, ProviderState(
            id=DESCRIPTOR.id,
            display_name=DESCRIPTOR.display_name,
            installed=False,
            source="oauth",
        )

    project_id = _project_id_from_sources(settings)
    if not project_id:
        legacy = {
            "installed": True,
            "error": "No Google Cloud project configured.",
            "fail_reason": "invalid_credentials",
        }
        state = ProviderState(
            id=DESCRIPTOR.id,
            display_name=DESCRIPTOR.display_name,
            installed=True,
            authenticated=False,
            status="error",
            source="oauth",
            local_usage=scan_vertex_local_usage(),
            error=str(legacy["error"]),
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
            "account_id": project_id,
            "used_pct": round(highest) if highest is not None else None,
        }
        state = ProviderState(
            id=DESCRIPTOR.id,
            display_name=DESCRIPTOR.display_name,
            installed=True,
            authenticated=True,
            source="oauth",
            primary_metric=MetricWindow("Quota", highest or 0, None)
            if highest is not None
            else None,
            local_usage=scan_vertex_local_usage(),
            extras={
                "plan": project_id,
                "projectId": project_id,
                "accountId": project_id,
            },
        )
        return legacy, state
    except urllib.error.HTTPError as err:
        legacy = {
            "installed": True,
            **classify_http_failure("vertexai", err.code, read_http_error_body(err)),
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
        source="oauth",
        local_usage=scan_vertex_local_usage(),
        error=str(error_text) if error_text is not None else None,
        extras={"plan": project_id, "projectId": project_id, "accountId": project_id}
        if project_id
        else {},
    )
    return legacy, state
