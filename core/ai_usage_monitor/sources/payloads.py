from __future__ import annotations

from typing import Any

from core.ai_usage_monitor.sources.model_types import (
    SourceModelInputs,
    SourceModelRuntime,
)


def build_source_strategy_payload(
    *,
    inputs: SourceModelInputs,
    runtime: SourceModelRuntime,
) -> dict[str, Any]:
    return {
        "preferredSource": inputs.preferred_source,
        "resolvedSource": inputs.active_source,
        "policy": inputs.preferred_policy,
        "fallbackReason": runtime.fallback_reason or None,
        "resolutionReason": runtime.resolution_reason,
        "fallbackActive": runtime.fallback_active,
        "supportsProbe": runtime.supports_probe,
        "fallbackChain": list(runtime.fallback_chain),
        "candidates": list(runtime.candidates),
    }


def build_availability_payload(runtime: SourceModelRuntime) -> dict[str, Any]:
    return {
        "localToolInstalled": runtime.local_tool_detected
        if runtime.has_local_capability
        else False,
        "apiKeyPresent": runtime.api_key_present,
        "apiConfigured": runtime.api_configured,
        "authValid": runtime.auth_valid,
        "rateLimitState": runtime.rate_limit_state,
    }


def build_provider_source_payload(
    *,
    inputs: SourceModelInputs,
    runtime: SourceModelRuntime,
    settings_presentation: dict[str, Any],
) -> dict[str, Any]:
    source_strategy = build_source_strategy_payload(inputs=inputs, runtime=runtime)
    availability = build_availability_payload(runtime)
    return {
        "canonicalMode": runtime.canonical_mode,
        "providerCapabilities": {
            "supportsLocalCli": runtime.has_local_capability,
            "supportsApi": runtime.has_api_capability,
            "supportsWeb": runtime.has_web_capability,
        },
        "sourceStrategy": source_strategy,
        "availability": availability,
        "preferredSource": inputs.preferred_source,
        "preferredSourcePolicy": inputs.preferred_policy,
        "activeSource": inputs.active_source,
        "availableSources": list(inputs.available_sources),
        "supportsProbe": runtime.supports_probe,
        "fallbackChain": list(runtime.fallback_chain),
        "sourceCandidates": list(runtime.candidates),
        "fallbackState": {
            "active": runtime.fallback_active,
            "from": inputs.preferred_source or None,
            "to": inputs.active_source or None,
            "reason": runtime.fallback_reason or None,
            "label": runtime.fallback_label or None,
        },
        "sourceLabel": runtime.source_label,
        "sourceDetails": runtime.source_details,
        "authState": runtime.auth_state,
        "localToolDetected": runtime.local_tool_detected,
        "apiConfigured": runtime.api_configured,
        "localToolInstalled": runtime.local_tool_detected
        if runtime.has_local_capability
        else False,
        "apiKeyPresent": runtime.api_key_present,
        "authValid": runtime.auth_valid,
        "rateLimitState": runtime.rate_limit_state,
        "resolvedSource": inputs.active_source,
        "fallbackReason": runtime.fallback_reason or None,
        "resolutionReason": runtime.resolution_reason,
        "settingsPresentation": settings_presentation,
    }
