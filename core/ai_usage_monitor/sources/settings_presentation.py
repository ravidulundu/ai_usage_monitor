from __future__ import annotations

from typing import Any

from core.ai_usage_monitor.models import ProviderState
from core.ai_usage_monitor.sources.common import source_token
from core.ai_usage_monitor.sources.model_types import (
    SourceModelInputs,
    SourceModelRuntime,
)


def _settings_status_tags(
    *,
    has_local_capability: bool,
    has_api_capability: bool,
    has_web_capability: bool,
    local_tool_detected: bool,
    api_configured: bool,
    api_key_present: bool,
    fallback_active: bool,
    installed: bool,
    disabled: bool,
) -> list[str]:
    if disabled:
        return ["Disabled"]
    tags: list[str] = []
    if has_local_capability:
        tags.append("CLI detected" if local_tool_detected else "CLI missing")
    if has_api_capability or has_web_capability:
        tags.append(
            "API configured" if (api_configured or api_key_present) else "API missing"
        )
    if fallback_active:
        tags.append("Fallback active")
    if not installed:
        tags.append("Unavailable")
    return tags


def _settings_status_label(tags: list[str]) -> str:
    if "Disabled" in tags:
        return "Status: Disabled"
    if "Unavailable" in tags:
        return "Status: Unavailable"
    if "Fallback active" in tags:
        return "Status: Fallback"
    if "CLI missing" in tags or "API missing" in tags:
        return "Status: Config missing"
    return "Status: Ready"


def _settings_capabilities_label(
    *,
    has_local_capability: bool,
    has_api_capability: bool,
    has_web_capability: bool,
) -> str:
    labels: list[str] = []
    if has_local_capability:
        labels.append("Local CLI")
    if has_api_capability:
        labels.append("API")
    if has_web_capability:
        labels.append("Web")
    return " + ".join(labels) if labels else "Unavailable"


def _settings_availability_label(
    *,
    has_local_capability: bool,
    has_api_capability: bool,
    has_web_capability: bool,
    local_tool_detected: bool,
    api_configured: bool,
    api_key_present: bool,
    auth_valid: bool | None,
    rate_limit_state: str,
    disabled: bool,
) -> str:
    if disabled:
        return "Disabled"
    labels: list[str] = []
    if has_local_capability:
        labels.append("CLI installed" if local_tool_detected else "CLI missing")
    if has_api_capability or has_web_capability:
        if api_configured:
            labels.append("API configured")
        elif api_key_present:
            labels.append("API key set")
        else:
            labels.append("API key missing")
    if auth_valid is True:
        labels.append("Auth valid")
    elif auth_valid is False:
        labels.append("Auth required")
    if rate_limit_state and rate_limit_state != "unknown":
        labels.append(f"Rate limit: {rate_limit_state.replace('_', ' ')}")
    return " · ".join(labels) if labels else "Unknown"


def _settings_source_reason_label(
    *, fallback_reason: str, resolution_reason: str, disabled: bool
) -> str:
    if disabled:
        return "Provider disabled"
    if fallback_reason:
        return f"Using fallback: {fallback_reason.replace('_', ' ')}"
    if resolution_reason:
        return f"Source selection: {resolution_reason.replace('_', ' ')}"
    return ""


def _settings_strategy_label(
    *,
    preferred_source: str,
    active_source: str,
    available_sources: tuple[str, ...],
    fallback_reason: str,
    resolution_reason: str,
) -> str:
    preferred = preferred_source or "auto"
    active = active_source or preferred
    available = "/".join(source.upper() for source in available_sources if source)
    reason = (
        f"fallback: {fallback_reason.replace('_', ' ')}"
        if fallback_reason
        else resolution_reason.replace("_", " ")
    )
    parts = [f"Preferred {source_token(preferred)}", f"Active {source_token(active)}"]
    if available:
        parts.append(f"available {available}")
    if reason:
        parts.append(reason)
    return " · ".join(parts)


def _settings_subtitle(source_mode_label: str, provider: ProviderState) -> str:
    if (
        provider.enabled is False
        or str(provider.status or "").strip().lower() == "disabled"
    ):
        return f"{source_mode_label} · disabled"
    if provider.installed is False:
        return f"{source_mode_label} · unavailable"
    if provider.error:
        return f"{source_mode_label} · needs attention"
    return f"{source_mode_label} · ready"


def build_settings_presentation(
    *,
    provider: ProviderState,
    inputs: SourceModelInputs,
    runtime: SourceModelRuntime,
) -> dict[str, Any]:
    disabled = (
        provider.enabled is False
        or str(provider.status or "").strip().lower() == "disabled"
    )
    status_tags = _settings_status_tags(
        has_local_capability=runtime.has_local_capability,
        has_api_capability=runtime.has_api_capability,
        has_web_capability=runtime.has_web_capability,
        local_tool_detected=runtime.local_tool_detected,
        api_configured=runtime.api_configured,
        api_key_present=runtime.api_key_present,
        fallback_active=runtime.fallback_active,
        installed=bool(provider.installed),
        disabled=disabled,
    )
    active_source_label = f"Active {source_token(inputs.active_source or inputs.preferred_source or 'auto')}"
    preferred_source_label = (
        f"Preferred {source_token(inputs.preferred_source or 'auto')}"
    )
    fallback_presentation_label = (
        f"Fallback {runtime.fallback_reason.replace('_', ' ')}"
        if runtime.fallback_reason
        else ""
    )
    return {
        "sourceModeLabel": runtime.source_label,
        "activeSourceLabel": active_source_label,
        "sourceStatusLabel": _settings_status_label(status_tags),
        "fallbackLabel": fallback_presentation_label,
        "availabilityLabel": _settings_availability_label(
            has_local_capability=runtime.has_local_capability,
            has_api_capability=runtime.has_api_capability,
            has_web_capability=runtime.has_web_capability,
            local_tool_detected=runtime.local_tool_detected,
            api_configured=runtime.api_configured,
            api_key_present=runtime.api_key_present,
            auth_valid=runtime.auth_valid,
            rate_limit_state=runtime.rate_limit_state,
            disabled=disabled,
        ),
        "subtitle": _settings_subtitle(runtime.source_label, provider),
        "preferredSourceLabel": preferred_source_label,
        "statusTags": status_tags,
        "sourceReasonLabel": _settings_source_reason_label(
            fallback_reason=runtime.fallback_reason,
            resolution_reason=runtime.resolution_reason,
            disabled=disabled,
        ),
        "strategyLabel": _settings_strategy_label(
            preferred_source=inputs.preferred_source,
            active_source=inputs.active_source,
            available_sources=inputs.available_sources,
            fallback_reason=runtime.fallback_reason,
            resolution_reason=runtime.resolution_reason,
        ),
        "capabilitiesLabel": _settings_capabilities_label(
            has_local_capability=runtime.has_local_capability,
            has_api_capability=runtime.has_api_capability,
            has_web_capability=runtime.has_web_capability,
        ),
    }
