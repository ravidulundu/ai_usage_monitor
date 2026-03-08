from __future__ import annotations

from typing import Any

from core.ai_usage_monitor.models import ProviderState


_LOCAL_SOURCE_IDS = {"cli", "local", "oauth", "local_cli"}


def provider_subtitle(
    provider: ProviderState, source_presentation: dict[str, Any] | None = None
) -> str:
    del source_presentation
    parts: list[str] = []
    model = provider.extras.get("model") if isinstance(provider.extras, dict) else None
    if model and model != "local-cli":
        parts.append(str(model))
    plan = provider.extras.get("plan") if isinstance(provider.extras, dict) else None
    if plan and not (provider.source == "cli" and str(plan) in {"api", "oauth"}):
        parts.append(str(plan))
    return " · ".join(parts)


def provider_source_model(provider: ProviderState) -> dict[str, Any]:
    if isinstance(provider.source_model, dict) and provider.source_model:
        return provider.source_model
    metadata = provider.metadata if isinstance(provider.metadata, dict) else {}
    source_model = metadata.get("sourceModel")
    if isinstance(source_model, dict):
        return source_model

    source_id = str(provider.source or "").lower()
    return {
        "canonicalMode": "unavailable" if provider.installed is False else "api",
        "providerCapabilities": {
            "supportsLocalCli": bool(source_id in _LOCAL_SOURCE_IDS),
            "supportsApi": bool(source_id == "api"),
            "supportsWeb": bool(source_id == "web"),
        },
        "sourceStrategy": {
            "preferredSource": source_id,
            "resolvedSource": source_id,
            "policy": "auto",
            "fallbackReason": None,
            "resolutionReason": "default_source",
            "fallbackActive": False,
            "supportsProbe": False,
            "fallbackChain": [],
            "candidates": [],
        },
        "availability": {
            "localToolInstalled": bool(provider.installed),
            "apiKeyPresent": False,
            "apiConfigured": False,
            "authValid": None
            if provider.installed is False
            else bool(provider.authenticated),
            "rateLimitState": "unavailable"
            if provider.installed is False
            else "unknown",
        },
        "preferredSource": source_id,
        "activeSource": source_id,
        "resolvedSource": source_id,
        "availableSources": [],
        "supportsProbe": False,
        "fallbackChain": [],
        "sourceCandidates": [],
        "fallbackState": {
            "active": False,
            "from": None,
            "to": None,
            "reason": None,
            "label": None,
        },
        "fallbackReason": None,
        "resolutionReason": "default_source",
        "sourceLabel": "Unavailable"
        if provider.installed is False
        else source_id.upper(),
        "sourceDetails": "",
        "authState": "auth_required"
        if provider.authenticated is False
        else ("unavailable" if provider.installed is False else "authenticated"),
        "localToolDetected": bool(provider.installed),
        "localToolInstalled": bool(provider.installed),
        "apiKeyPresent": False,
        "authValid": None
        if provider.installed is False
        else bool(provider.authenticated),
        "rateLimitState": "unavailable" if provider.installed is False else "unknown",
        "apiConfigured": False,
    }


def _dashboard_source_key(provider: ProviderState, source_model: dict[str, Any]) -> str:
    strategy = source_model.get("sourceStrategy")
    strategy = strategy if isinstance(strategy, dict) else {}
    resolved = (
        str(
            strategy.get("resolvedSource")
            or source_model.get("activeSource")
            or provider.source
            or ""
        )
        .strip()
        .lower()
    )
    plan = (
        str(provider.extras.get("plan") or "").strip().lower()
        if isinstance(provider.extras, dict)
        else ""
    )
    if resolved in {"", "auto"} and plan in {"api", "api_key", "apikey"}:
        return "api"
    return resolved


def usage_dashboard_url(
    provider: ProviderState, descriptor: Any, source_model: dict[str, Any]
) -> str | None:
    source_key = _dashboard_source_key(provider, source_model)
    plan = (
        str(provider.extras.get("plan") or "").strip().lower()
        if isinstance(provider.extras, dict)
        else ""
    )
    if provider.id == "opencode" and source_key == "web" and plan.startswith("wrk_"):
        return f"https://opencode.ai/workspace/{plan}/billing"

    if descriptor and hasattr(descriptor, "usage_dashboard_url_for_source"):
        resolved = descriptor.usage_dashboard_url_for_source(source_key)
        if resolved:
            return str(resolved)
    return None


def status_page_url(_provider_id: str, descriptor: Any | None) -> str | None:
    if descriptor and getattr(descriptor, "status_page_url", None):
        return str(descriptor.status_page_url)
    return None
