from __future__ import annotations

from typing import Any

from core.ai_usage_monitor.models import ProviderState
from core.ai_usage_monitor.presentation.identity_vm import (
    provider_identity_refreshing,
)


_LOCAL_SOURCE_IDS = {"cli", "local", "oauth", "local_cli"}
_REMOTE_SOURCE_IDS = {"api", "web"}
_API_SOURCE_IDS = {"api"}
_WEB_SOURCE_IDS = {"web"}


def _normalize_source_id(source_id: str) -> str:
    normalized = str(source_id or "").strip().lower()
    if normalized == "remote":
        return "web"
    return normalized


def _is_local_source(source_id: str) -> bool:
    return _normalize_source_id(source_id) in _LOCAL_SOURCE_IDS


def _is_remote_source(source_id: str) -> bool:
    return _normalize_source_id(source_id) in _REMOTE_SOURCE_IDS


def _is_api_source(source_id: str) -> bool:
    return _normalize_source_id(source_id) in _API_SOURCE_IDS


def _is_web_source(source_id: str) -> bool:
    return _normalize_source_id(source_id) in _WEB_SOURCE_IDS


def _active_source_label(
    canonical_mode: str,
    resolved_source: str,
    fallback_active: bool,
    unavailable: bool,
) -> str:
    if unavailable:
        return "Unavailable"
    if fallback_active:
        return "Fallback"
    if canonical_mode == "hybrid":
        return "Hybrid"
    if _is_local_source(resolved_source):
        return "Local CLI"
    if _is_web_source(resolved_source):
        return "Web"
    if _is_api_source(resolved_source):
        return "API"
    if canonical_mode == "local_cli":
        return "Local CLI"
    if canonical_mode == "api":
        return "API"
    return "Unavailable"


def source_reason_text(source_model: dict[str, Any]) -> str | None:
    strategy = source_model.get("sourceStrategy")
    strategy = strategy if isinstance(strategy, dict) else {}
    fallback_reason = (
        str(strategy.get("fallbackReason") or source_model.get("fallbackReason") or "")
        .strip()
        .lower()
    )
    resolution_reason = (
        str(
            strategy.get("resolutionReason")
            or source_model.get("resolutionReason")
            or ""
        )
        .strip()
        .lower()
    )
    fallback_active = bool(
        strategy.get("fallbackActive")
        or (source_model.get("fallbackState") or {}).get("active")
    )

    if fallback_active:
        if fallback_reason == "local_unavailable":
            return "Fallback: Local CLI unavailable"
        if fallback_reason == "unavailable":
            return "Preferred source unavailable"
        if fallback_reason == "source_error":
            return "Fallback after source error"
        if fallback_reason == "auto_selected":
            return "Auto source selected"
        return "Fallback active"

    if resolution_reason == "preferred_source_applied":
        return "Using preferred source"
    if resolution_reason == "auto_selected_best_source":
        return "Auto source selection applied"
    if resolution_reason == "provider_reported_active_source":
        return "Using provider active source"
    return None


def source_unavailable_reason(
    provider: ProviderState,
    source_model: dict[str, Any],
    rate_limits_missing: bool,
) -> dict[str, Any] | None:
    strategy = source_model.get("sourceStrategy")
    strategy = strategy if isinstance(strategy, dict) else {}
    availability = source_model.get("availability")
    availability = availability if isinstance(availability, dict) else {}
    capabilities = source_model.get("providerCapabilities")
    capabilities = capabilities if isinstance(capabilities, dict) else {}

    resolved_source = (
        str(
            strategy.get("resolvedSource")
            or source_model.get("activeSource")
            or provider.source
            or ""
        )
        .strip()
        .lower()
    )
    resolved_source = _normalize_source_id(resolved_source)
    metadata = provider.metadata if isinstance(provider.metadata, dict) else {}
    raw_identity = metadata.get("identity")
    identity: dict[str, Any] = raw_identity if isinstance(raw_identity, dict) else {}
    source_switch_refreshing = provider_identity_refreshing(provider) and bool(
        identity.get("sourceChanged")
    )

    if (
        source_switch_refreshing
        and strategy.get("fallbackActive")
        and str(strategy.get("preferredSource") or "").strip().lower()
        != resolved_source
    ):
        return {"code": "source_switched", "text": "Source switched"}

    if provider.installed is False and capabilities.get("supportsLocalCli"):
        return {"code": "cli_not_installed", "text": "CLI not installed"}

    if availability.get("authValid") is False:
        return {"code": "auth_invalid", "text": "Auth invalid"}

    if (
        capabilities.get("supportsApi") or capabilities.get("supportsWeb")
    ) and resolved_source in _REMOTE_SOURCE_IDS:
        api_present = bool(
            availability.get("apiConfigured")
            or availability.get("apiKeyPresent")
            or source_model.get("apiConfigured")
        )
        if not api_present:
            return {"code": "api_not_configured", "text": "API not configured"}

    if rate_limits_missing:
        return {"code": "local_usage_unavailable", "text": "Local usage unavailable"}

    if (
        resolved_source in {"cli", "local", "oauth"}
        and provider.local_usage is None
        and provider.primary_metric is None
        and provider.secondary_metric is None
    ):
        return {"code": "local_usage_unavailable", "text": "Local usage unavailable"}

    if provider.installed is False:
        return {"code": "unavailable", "text": "Unavailable"}
    return None


def source_presentation_vm(
    provider: ProviderState,
    source_model: dict[str, Any],
    rate_limits_missing: bool,
) -> dict[str, Any]:
    strategy = source_model.get("sourceStrategy")
    strategy = strategy if isinstance(strategy, dict) else {}
    availability = source_model.get("availability")
    availability = availability if isinstance(availability, dict) else {}
    capabilities = source_model.get("providerCapabilities")
    capabilities = capabilities if isinstance(capabilities, dict) else {}

    mode_label = str(source_model.get("sourceLabel") or "").strip()
    canonical_mode = str(source_model.get("canonicalMode") or "").strip().lower()
    resolved_source = (
        str(
            strategy.get("resolvedSource")
            or source_model.get("activeSource")
            or provider.source
            or ""
        )
        .strip()
        .lower()
    )
    resolved_source = _normalize_source_id(resolved_source)
    fallback_active = bool(
        strategy.get("fallbackActive")
        or (source_model.get("fallbackState") or {}).get("active")
    )
    unavailable = bool(provider.installed is False or canonical_mode == "unavailable")

    status_tags: list[str] = []
    if capabilities.get("supportsLocalCli"):
        status_tags.append(
            "CLI detected"
            if bool(availability.get("localToolInstalled"))
            else "CLI not installed"
        )
    if capabilities.get("supportsApi") or capabilities.get("supportsWeb"):
        api_present = bool(
            availability.get("apiConfigured")
            or availability.get("apiKeyPresent")
            or source_model.get("apiConfigured")
        )
        status_tags.append("API configured" if api_present else "API not configured")
    if fallback_active:
        status_tags.append("Fallback active")
    if unavailable:
        status_tags.append("Unavailable")

    unavailable_reason = source_unavailable_reason(
        provider=provider,
        source_model=source_model,
        rate_limits_missing=rate_limits_missing,
    )
    reason_text = source_reason_text(source_model)
    if unavailable_reason and unavailable_reason.get("code") == "source_switched":
        reason_text = "Source changed, refreshing data"

    return {
        "modeLabel": mode_label,
        "activeSourceLabel": _active_source_label(
            canonical_mode=canonical_mode,
            resolved_source=resolved_source,
            fallback_active=fallback_active,
            unavailable=unavailable,
        ),
        "statusTags": status_tags,
        "reasonText": reason_text,
        "unavailableReason": unavailable_reason,
    }
