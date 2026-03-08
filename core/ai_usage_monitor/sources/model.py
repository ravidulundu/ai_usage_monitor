from __future__ import annotations

from typing import Any

from core.ai_usage_monitor.models import ProviderState

_LOCAL_SOURCE_IDS = {"cli", "local", "oauth", "local_cli"}
_API_SOURCE_IDS = {"api"}
_WEB_SOURCE_IDS = {"web", "remote"}


def _norm_source(value: Any) -> str:
    text = str(value or "").strip().lower()
    return text or ""


def _source_family(source_id: str) -> str:
    source = _norm_source(source_id)
    if source in _LOCAL_SOURCE_IDS:
        return "local_cli"
    if source in _API_SOURCE_IDS:
        return "api"
    if source in _WEB_SOURCE_IDS:
        return "web"
    return source


def _source_token(source_id: str) -> str:
    source = _norm_source(source_id)
    if source == "local_cli":
        return "LOCAL CLI"
    return source.upper()


def _unique_strings(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item in seen or not item:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def _has_local_capability(available_sources: list[str], active_source: str) -> bool:
    if active_source in _LOCAL_SOURCE_IDS:
        return True
    return any(source in _LOCAL_SOURCE_IDS for source in available_sources)


def _has_api_capability(available_sources: list[str], active_source: str) -> bool:
    if active_source in _API_SOURCE_IDS:
        return True
    return any(source in _API_SOURCE_IDS for source in available_sources)


def _has_web_capability(available_sources: list[str], active_source: str) -> bool:
    if active_source in _WEB_SOURCE_IDS:
        return True
    return any(source in _WEB_SOURCE_IDS for source in available_sources)


def _api_configured(
    settings: dict[str, Any] | None, active_source: str, installed: bool
) -> bool:
    if active_source in (_API_SOURCE_IDS | _WEB_SOURCE_IDS) and installed:
        return True
    if not isinstance(settings, dict):
        return False
    for key, value in settings.items():
        if value is None:
            continue
        if isinstance(value, str) and value.strip() == "":
            continue
        lowered = str(key).lower()
        if "api" in lowered and ("key" in lowered or "token" in lowered):
            return True
        if "cookie" in lowered or "header" in lowered:
            return True
        if lowered in {"workspaceid", "projectid", "organization", "orgid"}:
            return True
    return False


def _api_key_present(settings: dict[str, Any] | None) -> bool:
    if not isinstance(settings, dict):
        return False
    for key, value in settings.items():
        if value is None:
            continue
        if isinstance(value, str) and value.strip() == "":
            continue
        lowered = str(key).lower()
        if "api" in lowered and ("key" in lowered or "token" in lowered):
            return True
        if lowered.endswith("apikey") or lowered.endswith("apitoken"):
            return True
    return False


def _auth_state(provider: ProviderState) -> str:
    if provider.installed is False:
        return "unavailable"
    auth_value: object = provider.authenticated
    if auth_value is False:
        return "auth_required"
    if provider.error:
        return "error"
    if bool(auth_value):
        return "authenticated"
    return "unknown"


def _canonical_mode(
    provider: ProviderState,
    active_source: str,
    has_local_capability: bool,
    has_api_capability: bool,
    has_web_capability: bool,
) -> str:
    if provider.installed is False:
        return "unavailable"
    if has_local_capability and (has_api_capability or has_web_capability):
        return "hybrid"
    if active_source in _LOCAL_SOURCE_IDS or has_local_capability:
        return "local_cli"
    if (
        active_source in (_API_SOURCE_IDS | _WEB_SOURCE_IDS)
        or has_api_capability
        or has_web_capability
    ):
        return "api"
    return "unavailable"


def _source_label(canonical_mode: str, local_first: bool, active_source: str) -> str:
    if active_source in _WEB_SOURCE_IDS:
        return "Web"
    if canonical_mode == "local_cli":
        return "Local CLI"
    if canonical_mode == "api":
        return "API"
    if canonical_mode == "hybrid":
        return "Hybrid (local-first)" if local_first else "Hybrid"
    return "Unavailable"


def _preferred_source_policy(descriptor: Any) -> str:
    policy = (
        str(getattr(descriptor, "preferred_source_policy", "") or "").strip().lower()
    )
    return policy or "auto"


def _is_local_first(policy: str, preferred_source: str) -> bool:
    if policy in {"local_first", "cli_first"}:
        return True
    if policy in {"api_first", "web_first"}:
        return False
    return preferred_source in {"", "auto", "cli", "local", "oauth", "local_cli"}


def _resolution_reason(
    preferred_source: str,
    active_source: str,
    fallback_active: bool,
    fallback_reason: str,
) -> str:
    if not active_source:
        return "unresolved_source"
    if fallback_active:
        if fallback_reason == "auto_selected":
            return "auto_selected_best_source"
        if fallback_reason == "local_unavailable":
            return "local_unavailable_fallback"
        if fallback_reason == "unavailable":
            return "preferred_source_unavailable"
        if fallback_reason == "source_error":
            return "fallback_after_source_error"
        return "fallback_selected"
    if preferred_source and _source_family(preferred_source) == _source_family(
        active_source
    ):
        return "preferred_source_applied"
    if preferred_source and _source_family(preferred_source) != _source_family(
        active_source
    ):
        return "provider_reported_active_source"
    return "default_source"


def _auth_valid(auth_state: str) -> bool | None:
    if auth_state == "authenticated":
        return True
    if auth_state in {"auth_required", "unavailable"}:
        return False
    return None


def _rate_limit_state(provider: ProviderState) -> str:
    extras = provider.extras if isinstance(provider.extras, dict) else {}
    explicit = extras.get("rateLimitState")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip().lower()
    if extras.get("hasRateLimits") is False:
        return "unavailable"
    error_text = str(provider.error or "").lower()
    if "rate limit" in error_text:
        return "limited"
    if provider.installed is False:
        return "unavailable"
    if provider.primary_metric or provider.secondary_metric:
        return "ok"
    return "unknown"


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
) -> list[str]:
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
) -> str:
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
    *, fallback_reason: str, resolution_reason: str
) -> str:
    if fallback_reason:
        return f"Using fallback: {fallback_reason.replace('_', ' ')}"
    if resolution_reason:
        return f"Source selection: {resolution_reason.replace('_', ' ')}"
    return ""


def _settings_strategy_label(
    *,
    preferred_source: str,
    active_source: str,
    available_sources: list[str],
    fallback_reason: str,
    resolution_reason: str,
) -> str:
    preferred = preferred_source or "auto"
    active = active_source or preferred
    available = "/".join([source.upper() for source in available_sources if source])
    reason = (
        f"fallback: {fallback_reason.replace('_', ' ')}"
        if fallback_reason
        else resolution_reason.replace("_", " ")
    )
    parts = [f"Preferred {_source_token(preferred)}", f"Active {_source_token(active)}"]
    if available:
        parts.append(f"available {available}")
    if reason:
        parts.append(reason)
    return " · ".join(parts)


def _settings_subtitle(source_mode_label: str, provider: ProviderState) -> str:
    if provider.installed is False:
        return f"{source_mode_label} · unavailable"
    if provider.error:
        return f"{source_mode_label} · needs attention"
    return f"{source_mode_label} · ready"


def _fallback_state(
    preferred_source: str, active_source: str, provider: ProviderState
) -> tuple[bool, str]:
    fallback_active = bool(
        preferred_source
        and active_source
        and _source_family(preferred_source) != _source_family(active_source)
    )
    if not fallback_active:
        return False, ""
    if preferred_source == "auto":
        return True, "auto_selected"
    if _source_family(preferred_source) == "local_cli" and _source_family(
        active_source
    ) in {"api", "web"}:
        return True, "local_unavailable"
    if provider.installed is False:
        return True, "unavailable"
    if provider.error:
        return True, "source_error"
    return True, "fallback_selected"


def _build_source_details(
    *,
    preferred_source: str,
    active_source: str,
    fallback_active: bool,
    resolution_reason: str,
    auth_state: str,
    has_local_capability: bool,
    local_tool_detected: bool,
    has_api_capability: bool,
    api_configured: bool,
) -> str:
    details_parts: list[str] = []
    if preferred_source:
        details_parts.append(f"Preferred {_source_token(preferred_source)}")
    if active_source:
        details_parts.append(f"Active {_source_token(active_source)}")
    if fallback_active:
        details_parts.append("Fallback active")
    if resolution_reason:
        details_parts.append(f"Reason {resolution_reason.replace('_', ' ')}")
    if auth_state == "auth_required":
        details_parts.append("Authentication required")
    elif auth_state == "unavailable":
        details_parts.append("Provider unavailable")
    elif auth_state == "error":
        details_parts.append("Source error")
    if has_local_capability and not local_tool_detected:
        details_parts.append("Local tool not detected")
    if has_api_capability and not api_configured:
        details_parts.append("API not configured")
    return " · ".join(details_parts)


def _build_settings_presentation(
    *,
    source_mode_label: str,
    preferred_source: str,
    active_source: str,
    available_sources: list[str],
    fallback_reason: str,
    resolution_reason: str,
    has_local_capability: bool,
    has_api_capability: bool,
    has_web_capability: bool,
    local_tool_detected: bool,
    api_configured: bool,
    api_key_present: bool,
    auth_valid: bool | None,
    rate_limit_state: str,
    provider: ProviderState,
    installed: bool,
    fallback_active: bool,
) -> dict[str, Any]:
    status_tags = _settings_status_tags(
        has_local_capability=has_local_capability,
        has_api_capability=has_api_capability,
        has_web_capability=has_web_capability,
        local_tool_detected=local_tool_detected,
        api_configured=api_configured,
        api_key_present=api_key_present,
        fallback_active=fallback_active,
        installed=installed,
    )
    active_source_label = (
        f"Active {_source_token(active_source or preferred_source or 'auto')}"
    )
    preferred_source_label = f"Preferred {_source_token(preferred_source or 'auto')}"
    fallback_presentation_label = (
        f"Fallback {fallback_reason.replace('_', ' ')}" if fallback_reason else ""
    )
    return {
        "sourceModeLabel": source_mode_label,
        "activeSourceLabel": active_source_label,
        "sourceStatusLabel": _settings_status_label(status_tags),
        "fallbackLabel": fallback_presentation_label,
        "availabilityLabel": _settings_availability_label(
            has_local_capability=has_local_capability,
            has_api_capability=has_api_capability,
            has_web_capability=has_web_capability,
            local_tool_detected=local_tool_detected,
            api_configured=api_configured,
            api_key_present=api_key_present,
            auth_valid=auth_valid,
            rate_limit_state=rate_limit_state,
        ),
        "subtitle": _settings_subtitle(source_mode_label, provider),
        "preferredSourceLabel": preferred_source_label,
        "statusTags": status_tags,
        "sourceReasonLabel": _settings_source_reason_label(
            fallback_reason=fallback_reason,
            resolution_reason=resolution_reason,
        ),
        "strategyLabel": _settings_strategy_label(
            preferred_source=preferred_source,
            active_source=active_source,
            available_sources=available_sources,
            fallback_reason=fallback_reason,
            resolution_reason=resolution_reason,
        ),
        "capabilitiesLabel": _settings_capabilities_label(
            has_local_capability=has_local_capability,
            has_api_capability=has_api_capability,
            has_web_capability=has_web_capability,
        ),
    }


def _source_capabilities(
    available_sources: list[str], active_source: str
) -> tuple[bool, bool, bool]:
    has_local_capability = _has_local_capability(available_sources, active_source)
    has_api_capability = _has_api_capability(available_sources, active_source)
    has_web_capability = _has_web_capability(available_sources, active_source)
    return has_local_capability, has_api_capability, has_web_capability


def _resolution_runtime(
    resolution_data: dict[str, Any],
) -> tuple[bool, list[str], list[dict[str, str]]]:
    supports_probe = bool(resolution_data.get("supportsProbe"))
    fallback_chain = _unique_strings(
        [
            _norm_source(item)
            for item in list(resolution_data.get("fallbackChain") or [])
            if _norm_source(item)
        ]
    )
    candidates: list[dict[str, str]] = []
    for item in list(resolution_data.get("candidates") or []):
        if not isinstance(item, dict):
            continue
        source = _norm_source(item.get("source"))
        if not source:
            continue
        candidates.append(
            {
                "source": source,
                "kind": str(item.get("kind") or "").strip() or source,
            }
        )
    return supports_probe, fallback_chain, candidates


def _fallback_label(
    preferred_source: str, active_source: str, fallback_active: bool
) -> str:
    if not (fallback_active and preferred_source and active_source):
        return ""
    return f"{_source_token(preferred_source)} → {_source_token(active_source)}"


def _source_strategy_payload(
    *,
    preferred_source: str,
    active_source: str,
    preferred_policy: str,
    fallback_reason: str,
    resolution_reason: str,
    fallback_active: bool,
    supports_probe: bool,
    fallback_chain: list[str],
    candidates: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "preferredSource": preferred_source,
        "resolvedSource": active_source,
        "policy": preferred_policy,
        "fallbackReason": fallback_reason or None,
        "resolutionReason": resolution_reason,
        "fallbackActive": fallback_active,
        "supportsProbe": supports_probe,
        "fallbackChain": fallback_chain,
        "candidates": candidates,
    }


def _availability_payload(
    *,
    has_local_capability: bool,
    local_tool_detected: bool,
    api_key_present: bool,
    api_configured: bool,
    auth_valid: bool | None,
    rate_limit_state: str,
) -> dict[str, Any]:
    return {
        "localToolInstalled": local_tool_detected if has_local_capability else False,
        "apiKeyPresent": api_key_present,
        "apiConfigured": api_configured,
        "authValid": auth_valid,
        "rateLimitState": rate_limit_state,
    }


def _provider_source_model_payload(
    *,
    inputs: dict[str, Any],
    runtime: dict[str, Any],
    payloads: dict[str, Any],
) -> dict[str, Any]:
    source_strategy = payloads["source_strategy"]
    availability = payloads["availability"]
    settings_presentation = payloads["settings_presentation"]

    preferred_source = str(inputs["preferred_source"])
    preferred_policy = str(inputs["preferred_policy"])
    active_source = str(inputs["active_source"])
    available_sources = list(inputs["available_sources"])

    has_local_capability = bool(runtime["has_local_capability"])
    has_api_capability = bool(runtime["has_api_capability"])
    has_web_capability = bool(runtime["has_web_capability"])
    supports_probe = bool(runtime["supports_probe"])
    fallback_chain = list(runtime["fallback_chain"])
    candidates = list(runtime["candidates"])
    fallback_active = bool(runtime["fallback_active"])
    fallback_reason = str(runtime["fallback_reason"])
    fallback_label = str(runtime["fallback_label"])
    source_label = str(runtime["source_label"])
    source_details = str(runtime["source_details"])
    auth_state = str(runtime["auth_state"])
    local_tool_detected = bool(runtime["local_tool_detected"])
    api_configured = bool(runtime["api_configured"])
    api_key_present = bool(runtime["api_key_present"])
    auth_valid = runtime["auth_valid"]
    rate_limit_state = str(runtime["rate_limit_state"])
    resolution_reason = str(runtime["resolution_reason"])
    canonical_mode = str(runtime["canonical_mode"])

    return {
        "canonicalMode": canonical_mode,
        "providerCapabilities": {
            "supportsLocalCli": has_local_capability,
            "supportsApi": has_api_capability,
            "supportsWeb": has_web_capability,
        },
        "sourceStrategy": source_strategy,
        "availability": availability,
        "preferredSource": preferred_source,
        "preferredSourcePolicy": preferred_policy,
        "activeSource": active_source,
        "availableSources": available_sources,
        "supportsProbe": supports_probe,
        "fallbackChain": fallback_chain,
        "sourceCandidates": candidates,
        "fallbackState": {
            "active": fallback_active,
            "from": preferred_source or None,
            "to": active_source or None,
            "reason": fallback_reason or None,
            "label": fallback_label or None,
        },
        "sourceLabel": source_label,
        "sourceDetails": source_details,
        "authState": auth_state,
        "localToolDetected": local_tool_detected,
        "apiConfigured": api_configured,
        "localToolInstalled": local_tool_detected if has_local_capability else False,
        "apiKeyPresent": api_key_present,
        "authValid": auth_valid,
        "rateLimitState": rate_limit_state,
        "resolvedSource": active_source,
        "fallbackReason": fallback_reason or None,
        "resolutionReason": resolution_reason,
        "settingsPresentation": settings_presentation,
    }


def _source_model_inputs(
    provider: ProviderState,
    descriptor: Any,
    settings: dict[str, Any] | None,
    configured_source: str | None,
    resolution: dict[str, Any] | None,
) -> dict[str, Any]:
    descriptor_sources = list(getattr(descriptor, "source_modes", ()) or [])
    available_sources = _unique_strings(
        [_norm_source(item) for item in descriptor_sources]
    )
    preferred_policy = _preferred_source_policy(descriptor)
    resolution_data = resolution if isinstance(resolution, dict) else {}
    preferred_source = _norm_source(
        resolution_data.get("preferredSource")
        or configured_source
        or (settings or {}).get("source")
        or provider.source
    )
    active_source = _norm_source(provider.source or preferred_source)
    if active_source and active_source not in available_sources:
        available_sources = _unique_strings(available_sources + [active_source])
    return {
        "available_sources": available_sources,
        "preferred_policy": preferred_policy,
        "resolution_data": resolution_data,
        "preferred_source": preferred_source,
        "active_source": active_source,
    }


def _source_model_runtime(
    provider: ProviderState,
    settings: dict[str, Any] | None,
    inputs: dict[str, Any],
) -> dict[str, Any]:
    available_sources = list(inputs["available_sources"])
    active_source = str(inputs["active_source"])
    preferred_source = str(inputs["preferred_source"])
    preferred_policy = str(inputs["preferred_policy"])
    resolution_data = dict(inputs["resolution_data"])

    has_local_capability, has_api_capability, has_web_capability = _source_capabilities(
        available_sources, active_source
    )
    api_capability_for_mode = has_api_capability or has_web_capability
    local_tool_detected = bool(provider.installed) if has_local_capability else False
    api_configured = _api_configured(
        settings, active_source, installed=bool(provider.installed)
    )
    api_key_present = _api_key_present(settings)
    auth_state = _auth_state(provider)
    auth_valid = _auth_valid(auth_state)
    rate_limit_state = _rate_limit_state(provider)

    fallback_active, fallback_reason = _fallback_state(
        preferred_source=preferred_source,
        active_source=active_source,
        provider=provider,
    )

    local_first = _is_local_first(preferred_policy, preferred_source)
    canonical_mode = _canonical_mode(
        provider=provider,
        active_source=active_source,
        has_local_capability=has_local_capability,
        has_api_capability=api_capability_for_mode,
        has_web_capability=has_web_capability,
    )
    source_label = _source_label(
        canonical_mode, local_first=local_first, active_source=active_source
    )
    resolution_reason = str(
        resolution_data.get("resolutionReason") or ""
    ).strip().lower() or _resolution_reason(
        preferred_source=preferred_source,
        active_source=active_source,
        fallback_active=fallback_active,
        fallback_reason=fallback_reason,
    )
    supports_probe, fallback_chain, candidates = _resolution_runtime(resolution_data)
    source_details = _build_source_details(
        preferred_source=preferred_source,
        active_source=active_source,
        fallback_active=fallback_active,
        resolution_reason=resolution_reason,
        auth_state=auth_state,
        has_local_capability=has_local_capability,
        local_tool_detected=local_tool_detected,
        has_api_capability=has_api_capability,
        api_configured=api_configured,
    )
    fallback_label = _fallback_label(preferred_source, active_source, fallback_active)
    return {
        "has_local_capability": has_local_capability,
        "has_api_capability": has_api_capability,
        "has_web_capability": has_web_capability,
        "local_tool_detected": local_tool_detected,
        "api_configured": api_configured,
        "api_key_present": api_key_present,
        "auth_state": auth_state,
        "auth_valid": auth_valid,
        "rate_limit_state": rate_limit_state,
        "fallback_active": fallback_active,
        "fallback_reason": fallback_reason,
        "canonical_mode": canonical_mode,
        "source_label": source_label,
        "resolution_reason": resolution_reason,
        "supports_probe": supports_probe,
        "fallback_chain": fallback_chain,
        "candidates": candidates,
        "source_details": source_details,
        "fallback_label": fallback_label,
    }


def _source_model_payloads(
    provider: ProviderState,
    inputs: dict[str, Any],
    runtime: dict[str, Any],
) -> dict[str, Any]:
    available_sources = list(inputs["available_sources"])
    preferred_source = str(inputs["preferred_source"])
    active_source = str(inputs["active_source"])
    preferred_policy = str(inputs["preferred_policy"])

    source_strategy = _source_strategy_payload(
        preferred_source=preferred_source,
        active_source=active_source,
        preferred_policy=preferred_policy,
        fallback_reason=str(runtime["fallback_reason"]),
        resolution_reason=str(runtime["resolution_reason"]),
        fallback_active=bool(runtime["fallback_active"]),
        supports_probe=bool(runtime["supports_probe"]),
        fallback_chain=list(runtime["fallback_chain"]),
        candidates=list(runtime["candidates"]),
    )
    availability = _availability_payload(
        has_local_capability=bool(runtime["has_local_capability"]),
        local_tool_detected=bool(runtime["local_tool_detected"]),
        api_key_present=bool(runtime["api_key_present"]),
        api_configured=bool(runtime["api_configured"]),
        auth_valid=runtime["auth_valid"],
        rate_limit_state=str(runtime["rate_limit_state"]),
    )
    settings_presentation = _build_settings_presentation(
        source_mode_label=str(runtime["source_label"]),
        preferred_source=preferred_source,
        active_source=active_source,
        available_sources=available_sources,
        fallback_reason=str(runtime["fallback_reason"]),
        resolution_reason=str(runtime["resolution_reason"]),
        has_local_capability=bool(runtime["has_local_capability"]),
        has_api_capability=bool(runtime["has_api_capability"]),
        has_web_capability=bool(runtime["has_web_capability"]),
        local_tool_detected=bool(runtime["local_tool_detected"]),
        api_configured=bool(runtime["api_configured"]),
        api_key_present=bool(runtime["api_key_present"]),
        auth_valid=runtime["auth_valid"],
        rate_limit_state=str(runtime["rate_limit_state"]),
        provider=provider,
        installed=bool(provider.installed),
        fallback_active=bool(runtime["fallback_active"]),
    )
    return {
        "source_strategy": source_strategy,
        "availability": availability,
        "settings_presentation": settings_presentation,
    }


def build_provider_source_model(
    provider: ProviderState,
    descriptor: Any,
    settings: dict[str, Any] | None,
    configured_source: str | None = None,
    resolution: dict[str, Any] | None = None,
) -> dict[str, Any]:
    inputs = _source_model_inputs(
        provider=provider,
        descriptor=descriptor,
        settings=settings,
        configured_source=configured_source,
        resolution=resolution,
    )
    runtime = _source_model_runtime(
        provider=provider,
        settings=settings,
        inputs=inputs,
    )
    payloads = _source_model_payloads(
        provider=provider,
        inputs=inputs,
        runtime=runtime,
    )
    return _provider_source_model_payload(
        inputs=inputs,
        runtime=runtime,
        payloads=payloads,
    )
