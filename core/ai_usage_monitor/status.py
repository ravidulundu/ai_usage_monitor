from __future__ import annotations

import json
import urllib.request
from datetime import datetime
from typing import Any


def _read_json(url: str, timeout: int = 5) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": "ai-usage-monitor"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def fetch_statuspage(base_url: str, public_url: str | None = None) -> dict | None:
    try:
        payload = _read_json(base_url.rstrip("/") + "/api/v2/status.json")
    except Exception:
        return None

    status = payload.get("status") or {}
    page = payload.get("page") or {}
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

    active = []
    for incident in incidents:
        current_products = (
            incident.get("currently_affected_products")
            or incident.get("currentlyAffectedProducts")
            or []
        )
        all_products = (
            incident.get("affected_products") or incident.get("affectedProducts") or []
        )
        products = current_products or all_products
        if not any((product.get("id") == product_id) for product in products):
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
            return datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        except Exception:
            return datetime.min

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
