from __future__ import annotations

from typing import Any

from core.ai_usage_monitor.models import ProviderState
from core.ai_usage_monitor.sources.common import (
    API_SOURCE_IDS,
    LOCAL_SOURCE_IDS,
    WEB_SOURCE_IDS,
    norm_source,
    source_family,
    source_token,
    unique_strings,
)
from core.ai_usage_monitor.sources.model_types import (
    SourceModelInputs,
    SourceModelRuntime,
)
from core.ai_usage_monitor.sources.payloads import build_provider_source_payload
from core.ai_usage_monitor.sources.settings_presentation import (
    build_settings_presentation,
)


def _has_local_capability(available_sources: list[str], active_source: str) -> bool:
    if active_source in LOCAL_SOURCE_IDS:
        return True
    return any(source in LOCAL_SOURCE_IDS for source in available_sources)


def _has_api_capability(available_sources: list[str], active_source: str) -> bool:
    if active_source in API_SOURCE_IDS:
        return True
    return any(source in API_SOURCE_IDS for source in available_sources)


def _has_web_capability(available_sources: list[str], active_source: str) -> bool:
    if active_source in WEB_SOURCE_IDS:
        return True
    return any(source in WEB_SOURCE_IDS for source in available_sources)


def _api_configured(
    settings: dict[str, Any] | None, active_source: str, installed: bool
) -> bool:
    if active_source in (API_SOURCE_IDS | WEB_SOURCE_IDS) and installed:
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
    if active_source in LOCAL_SOURCE_IDS or has_local_capability:
        return "local_cli"
    if (
        active_source in (API_SOURCE_IDS | WEB_SOURCE_IDS)
        or has_api_capability
        or has_web_capability
    ):
        return "api"
    return "unavailable"


def _source_label(canonical_mode: str, local_first: bool, active_source: str) -> str:
    if active_source in WEB_SOURCE_IDS:
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
    if preferred_source and source_family(preferred_source) == source_family(
        active_source
    ):
        return "preferred_source_applied"
    if preferred_source and source_family(preferred_source) != source_family(
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


def _fallback_state(
    preferred_source: str, active_source: str, provider: ProviderState
) -> tuple[bool, str]:
    fallback_active = bool(
        preferred_source
        and active_source
        and source_family(preferred_source) != source_family(active_source)
    )
    if not fallback_active:
        return False, ""
    if preferred_source == "auto":
        return True, "auto_selected"
    if source_family(preferred_source) == "local_cli" and source_family(
        active_source
    ) in {
        "api",
        "web",
    }:
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
        details_parts.append(f"Preferred {source_token(preferred_source)}")
    if active_source:
        details_parts.append(f"Active {source_token(active_source)}")
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


def _source_capabilities(
    available_sources: list[str], active_source: str
) -> tuple[bool, bool, bool]:
    has_local_capability = _has_local_capability(available_sources, active_source)
    has_api_capability = _has_api_capability(available_sources, active_source)
    has_web_capability = _has_web_capability(available_sources, active_source)
    return has_local_capability, has_api_capability, has_web_capability


def _resolution_runtime(
    resolution_data: dict[str, Any],
) -> tuple[bool, tuple[str, ...], tuple[dict[str, str], ...]]:
    supports_probe = bool(resolution_data.get("supportsProbe"))
    fallback_chain = tuple(
        unique_strings(
            [
                norm_source(item)
                for item in list(resolution_data.get("fallbackChain") or [])
                if norm_source(item)
            ]
        )
    )
    candidates: list[dict[str, str]] = []
    for item in list(resolution_data.get("candidates") or []):
        if not isinstance(item, dict):
            continue
        source = norm_source(item.get("source"))
        if not source:
            continue
        candidates.append(
            {
                "source": source,
                "kind": str(item.get("kind") or "").strip() or source,
            }
        )
    return supports_probe, fallback_chain, tuple(candidates)


def _fallback_label(
    preferred_source: str, active_source: str, fallback_active: bool
) -> str:
    if not (fallback_active and preferred_source and active_source):
        return ""
    return f"{source_token(preferred_source)} → {source_token(active_source)}"


def build_source_model_inputs(
    *,
    provider: ProviderState,
    descriptor: Any,
    settings: dict[str, Any] | None,
    configured_source: str | None,
    resolution: dict[str, Any] | None,
) -> SourceModelInputs:
    descriptor_sources = list(getattr(descriptor, "source_modes", ()) or [])
    available_sources = unique_strings(
        [norm_source(item) for item in descriptor_sources]
    )
    preferred_policy = _preferred_source_policy(descriptor)
    resolution_data = resolution if isinstance(resolution, dict) else {}
    preferred_source = norm_source(
        resolution_data.get("preferredSource")
        or configured_source
        or (settings or {}).get("source")
        or provider.source
    )
    active_source = norm_source(provider.source or preferred_source)
    if active_source and active_source not in available_sources:
        available_sources = unique_strings(available_sources + [active_source])
    return SourceModelInputs(
        available_sources=tuple(available_sources),
        preferred_policy=preferred_policy,
        resolution_data=dict(resolution_data),
        preferred_source=preferred_source,
        active_source=active_source,
    )


def build_source_model_runtime(
    *,
    provider: ProviderState,
    settings: dict[str, Any] | None,
    inputs: SourceModelInputs,
) -> SourceModelRuntime:
    available_sources = list(inputs.available_sources)
    has_local_capability, has_api_capability, has_web_capability = _source_capabilities(
        available_sources, inputs.active_source
    )
    api_capability_for_mode = has_api_capability or has_web_capability
    local_tool_detected = bool(provider.installed) if has_local_capability else False
    api_configured = _api_configured(
        settings,
        inputs.active_source,
        installed=bool(provider.installed),
    )
    api_key_present = _api_key_present(settings)
    auth_state = _auth_state(provider)
    auth_valid = _auth_valid(auth_state)
    rate_limit_state = _rate_limit_state(provider)
    fallback_active, fallback_reason = _fallback_state(
        preferred_source=inputs.preferred_source,
        active_source=inputs.active_source,
        provider=provider,
    )
    local_first = _is_local_first(inputs.preferred_policy, inputs.preferred_source)
    canonical_mode = _canonical_mode(
        provider=provider,
        active_source=inputs.active_source,
        has_local_capability=has_local_capability,
        has_api_capability=api_capability_for_mode,
        has_web_capability=has_web_capability,
    )
    source_label = _source_label(
        canonical_mode,
        local_first=local_first,
        active_source=inputs.active_source,
    )
    resolution_reason = str(
        inputs.resolution_data.get("resolutionReason") or ""
    ).strip().lower() or _resolution_reason(
        preferred_source=inputs.preferred_source,
        active_source=inputs.active_source,
        fallback_active=fallback_active,
        fallback_reason=fallback_reason,
    )
    supports_probe, fallback_chain, candidates = _resolution_runtime(
        inputs.resolution_data
    )
    source_details = _build_source_details(
        preferred_source=inputs.preferred_source,
        active_source=inputs.active_source,
        fallback_active=fallback_active,
        resolution_reason=resolution_reason,
        auth_state=auth_state,
        has_local_capability=has_local_capability,
        local_tool_detected=local_tool_detected,
        has_api_capability=has_api_capability,
        api_configured=api_configured,
    )
    fallback_label = _fallback_label(
        inputs.preferred_source, inputs.active_source, fallback_active
    )
    return SourceModelRuntime(
        has_local_capability=has_local_capability,
        has_api_capability=has_api_capability,
        has_web_capability=has_web_capability,
        local_tool_detected=local_tool_detected,
        api_configured=api_configured,
        api_key_present=api_key_present,
        auth_state=auth_state,
        auth_valid=auth_valid,
        rate_limit_state=rate_limit_state,
        fallback_active=fallback_active,
        fallback_reason=fallback_reason,
        canonical_mode=canonical_mode,
        source_label=source_label,
        resolution_reason=resolution_reason,
        supports_probe=supports_probe,
        fallback_chain=fallback_chain,
        candidates=candidates,
        source_details=source_details,
        fallback_label=fallback_label,
    )


def build_provider_source_model(
    provider: ProviderState,
    descriptor: Any,
    settings: dict[str, Any] | None,
    configured_source: str | None = None,
    resolution: dict[str, Any] | None = None,
) -> dict[str, Any]:
    inputs = build_source_model_inputs(
        provider=provider,
        descriptor=descriptor,
        settings=settings,
        configured_source=configured_source,
        resolution=resolution,
    )
    runtime = build_source_model_runtime(
        provider=provider,
        settings=settings,
        inputs=inputs,
    )
    settings_presentation = build_settings_presentation(
        provider=provider,
        inputs=inputs,
        runtime=runtime,
    )
    return build_provider_source_payload(
        inputs=inputs,
        runtime=runtime,
        settings_presentation=settings_presentation,
    )
