from __future__ import annotations

import json
import urllib.request
from datetime import datetime, timezone
from typing import Any

from core.ai_usage_monitor.runtime_cache import read_ttl_cache, write_ttl_cache


_STATUS_CACHE_FILE = "status_cache.json"
_STATUS_TTL_SECONDS = 300
_STATUS_FAILURE_TTL_SECONDS = 60


def _failure_cache_key(url: str) -> str:
    return f"failure:{url}"


def _read_json_uncached(url: str, timeout: int = 5) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": "ai-usage-monitor"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def _read_json(
    url: str, timeout: int = 5, ttl_seconds: int = _STATUS_TTL_SECONDS
) -> Any:
    cached = read_ttl_cache(_STATUS_CACHE_FILE, url, ttl_seconds)
    if cached is not None:
        return cached
    failed = read_ttl_cache(
        _STATUS_CACHE_FILE,
        _failure_cache_key(url),
        _STATUS_FAILURE_TTL_SECONDS,
    )
    if failed is True:
        raise RuntimeError("status fetch temporarily suppressed after recent failure")
    try:
        payload = _read_json_uncached(url, timeout=timeout)
    except Exception:
        write_ttl_cache(_STATUS_CACHE_FILE, _failure_cache_key(url), True)
        raise
    write_ttl_cache(_STATUS_CACHE_FILE, url, payload)
    return payload


def fetch_statuspage(base_url: str, public_url: str | None = None) -> dict | None:
    try:
        payload = _read_json(base_url.rstrip("/") + "/api/v2/status.json")
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None

    status = payload.get("status") or {}
    page = payload.get("page") or {}
    if not isinstance(status, dict):
        status = {}
    if not isinstance(page, dict):
        page = {}
    return {
        "indicator": status.get("indicator") or "unknown",
        "description": status.get("description"),
        "updatedAt": page.get("updated_at"),
        "url": public_url or base_url,
    }


def _workspace_indicator(status: str | None, severity: str | None) -> str:
    status = (status or "").upper()
    severity = (severity or "").lower()
    if status == "AVAILABLE":
        return "none"
    if status == "SERVICE_INFORMATION":
        return "minor"
    if status == "SERVICE_DISRUPTION":
        return "major"
    if status == "SERVICE_OUTAGE":
        return "critical"
    if status in {"SERVICE_MAINTENANCE", "SCHEDULED_MAINTENANCE"}:
        return "maintenance"
    if severity == "low":
        return "minor"
    if severity == "medium":
        return "major"
    if severity == "high":
        return "critical"
    return "minor"


def _workspace_summary(text: str | None) -> str | None:
    if not text:
        return None
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    for raw_line in normalized.split("\n"):
        line = raw_line.strip().replace("**", "")
        if not line:
            continue
        lower = line.lower()
        if lower.startswith("summary") or lower.startswith("description"):
            continue
        if line.startswith("- "):
            line = line[2:].strip()
        if line:
            return line
    return None


def fetch_google_workspace_status(
    product_id: str, public_url: str | None = None
) -> dict | None:
    try:
        incidents = _read_json(
            "https://www.google.com/appsstatus/dashboard/incidents.json"
        )
    except Exception:
        return None
    if not isinstance(incidents, list):
        return None

    active = []
    for incident in incidents:
        if not isinstance(incident, dict):
            continue
        current_products = (
            incident.get("currently_affected_products")
            or incident.get("currentlyAffectedProducts")
            or []
        )
        if not isinstance(current_products, list):
            current_products = []
        all_products = (
            incident.get("affected_products") or incident.get("affectedProducts") or []
        )
        if not isinstance(all_products, list):
            all_products = []
        products = current_products or all_products
        if not any(
            isinstance(product, dict) and (product.get("id") == product_id)
            for product in products
        ):
            continue
        if incident.get("end"):
            continue
        active.append(incident)

    if not active:
        return {
            "indicator": "none",
            "description": None,
            "updatedAt": None,
            "url": public_url,
        }

    def sort_key(incident: dict[str, Any]) -> datetime:
        update = (
            incident.get("most_recent_update") or incident.get("mostRecentUpdate") or {}
        )
        updated_at = (
            update.get("when")
            or incident.get("modified")
            or incident.get("begin")
            or ""
        )
        try:
            dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return datetime.min.replace(tzinfo=timezone.utc)

    best = sorted(active, key=sort_key, reverse=True)[0]
    update = best.get("most_recent_update") or best.get("mostRecentUpdate") or {}
    return {
        "indicator": _workspace_indicator(
            update.get("status")
            or best.get("status_impact")
            or best.get("statusImpact"),
            best.get("severity"),
        ),
        "description": _workspace_summary(
            update.get("text") or best.get("external_desc") or best.get("externalDesc")
        ),
        "updatedAt": update.get("when") or best.get("modified") or best.get("begin"),
        "url": public_url,
    }
