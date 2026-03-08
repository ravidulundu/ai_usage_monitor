from __future__ import annotations

from typing import Any

from core.ai_usage_monitor.models import ProviderState


def provider_status_state(
    provider: ProviderState,
    status_url: str | None,
    stale: bool,
    source_presentation: dict[str, Any] | None,
) -> dict[str, Any]:
    incident = provider.incident if isinstance(provider.incident, dict) else {}
    indicator = incident_indicator(provider) or ("unknown" if incident else "none")
    incident_active = incident_is_active(indicator)
    incident_url = str(incident.get("url") or "").strip()
    effective_status_url = incident_url or (status_url or "")
    source_unavailable_reason = (
        source_presentation.get("unavailableReason")
        if isinstance(source_presentation, dict)
        else None
    )
    return {
        "hasStatusPage": bool(effective_status_url),
        "statusPageUrl": effective_status_url or None,
        "incidentActive": incident_active,
        "indicator": indicator,
        "summary": incident_summary(indicator),
        "details": incident_description(provider),
        "updatedAt": incident.get("updatedAt"),
        "stale": stale,
        "refreshFailed": bool(provider.error),
        "sourceIssue": bool(source_unavailable_reason),
        "tone": incident_tone(indicator),
    }


def status_presentation_vm(status_state: dict[str, Any]) -> dict[str, Any]:
    incident_active = bool(status_state.get("incidentActive"))
    details = str(status_state.get("details") or "").strip()
    if not incident_active:
        return {
            "visible": False,
            "badgeLabel": "",
            "details": "",
            "tone": str(status_state.get("tone") or "ok"),
        }
    return {
        "visible": True,
        "badgeLabel": str(status_state.get("summary") or "Service incident"),
        "details": details,
        "tone": str(status_state.get("tone") or "warn"),
    }


def incident_indicator(provider: ProviderState) -> str:
    incident = provider.incident if isinstance(provider.incident, dict) else {}
    return str(incident.get("indicator") or "").strip().lower()


def incident_is_active(indicator: str) -> bool:
    normalized = str(indicator or "").strip().lower()
    if not normalized:
        return False
    return normalized not in {"none", "operational", "ok"}


def incident_tone(indicator: str) -> str:
    normalized = str(indicator or "").strip().lower()
    if normalized in {"critical", "major_outage", "service_outage"}:
        return "error"
    if normalized in {
        "major",
        "minor",
        "maintenance",
        "degraded",
        "partial_outage",
        "service_disruption",
    }:
        return "warn"
    if normalized in {"none", "operational"}:
        return "ok"
    return "warn"


def incident_summary(indicator: str) -> str:
    normalized = str(indicator or "").strip().lower()
    if normalized in {"critical", "major_outage", "service_outage"}:
        return "Service outage"
    if normalized in {
        "major",
        "minor",
        "degraded",
        "partial_outage",
        "service_disruption",
    }:
        return "Service disruption"
    if normalized in {"maintenance", "service_maintenance", "scheduled_maintenance"}:
        return "Maintenance"
    if normalized in {"none", "operational"}:
        return "Operational"
    return "Service incident"


def incident_description(provider: ProviderState) -> str | None:
    incident = provider.incident if isinstance(provider.incident, dict) else {}
    description = str(incident.get("description") or "").strip()
    if not description:
        return None
    first_sentence = description.split(".")[0].strip()
    if len(first_sentence) > 100:
        return first_sentence[:97].rstrip() + "..."
    return first_sentence or description
