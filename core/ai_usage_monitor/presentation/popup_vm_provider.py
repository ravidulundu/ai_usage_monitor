from __future__ import annotations

from typing import Any

from core.ai_usage_monitor.models import ProviderState
from core.ai_usage_monitor.presentation.identity_vm import (
    provider_account_fingerprint,
    provider_identity_fingerprint,
    provider_identity_source_mode,
    provider_state_identity_key,
    switching_state_vm,
)
from core.ai_usage_monitor.presentation.popup_vm_actions import actions_vm
from core.ai_usage_monitor.presentation.popup_vm_common import (
    branding,
    plan_label,
    provider_badge_text,
    provider_short_name,
)
from core.ai_usage_monitor.presentation.popup_vm_metrics import (
    cost_vm,
    extra_usage_vm,
    provider_error_state,
    provider_metrics_vm,
)
from core.ai_usage_monitor.presentation.popup_vm_source_model import (
    provider_source_model,
    provider_subtitle,
    status_page_url,
    usage_dashboard_url,
)
from core.ai_usage_monitor.presentation.popup_vm_source_presentation import (
    source_presentation_vm,
)
from core.ai_usage_monitor.presentation.status_vm import (
    provider_status_state,
    status_presentation_vm,
)


def provider_vm(
    provider: ProviderState,
    descriptor_map: dict[str, Any],
    selected: bool,
    stale: bool,
    updated_text: str,
) -> dict[str, Any]:
    descriptor = descriptor_map.get(provider.id)
    provider_branding = branding(provider)
    short_name = provider_short_name(
        provider.id,
        provider.display_name,
        descriptor.short_name if descriptor else None,
    )
    rate_limits_missing = (
        provider.id == "codex" and provider.extras.get("hasRateLimits") is False
    )
    provider_available = provider.installed and not provider.error

    source_model = provider_source_model(provider)
    dashboard_url = usage_dashboard_url(provider, descriptor, source_model)
    status_url = status_page_url(provider.id, descriptor)
    source_presentation = source_presentation_vm(
        provider=provider,
        source_model=source_model,
        rate_limits_missing=rate_limits_missing,
    )
    status_state = provider_status_state(
        provider=provider,
        status_url=status_url,
        stale=stale,
        source_presentation=source_presentation,
    )
    status_presentation = status_presentation_vm(status_state)
    metrics = provider_metrics_vm(
        provider=provider,
        stale=stale,
        rate_limits_missing=rate_limits_missing,
        source_presentation=source_presentation,
    )
    error_message, source_unavailable_text = provider_error_state(
        provider, source_presentation
    )
    effective_status_url = status_state.get("statusPageUrl") or status_url

    return {
        "id": provider.id,
        "displayName": provider.display_name,
        "shortName": short_name,
        "badgeText": provider_badge_text(
            provider.id,
            provider.display_name,
            provider_branding.get("badgeText"),
        ),
        "sourceModel": source_model,
        "providerCapabilities": source_model.get("providerCapabilities", {}),
        "sourceStrategy": source_model.get("sourceStrategy", {}),
        "availability": source_model.get("availability", {}),
        "sourceLabel": source_model.get("sourceLabel"),
        "sourceDetails": source_model.get("sourceDetails"),
        "sourcePresentation": source_presentation,
        "statusState": status_state,
        "statusPresentation": status_presentation,
        "authState": source_model.get("authState"),
        "fallbackState": source_model.get("fallbackState"),
        "preferredSource": source_model.get("preferredSource"),
        "resolvedSource": source_model.get("resolvedSource"),
        "availableSources": source_model.get("availableSources", []),
        "fallbackReason": source_model.get("fallbackReason"),
        "localToolInstalled": source_model.get("localToolInstalled"),
        "apiConfigured": source_model.get("apiConfigured"),
        "authValid": source_model.get("authValid"),
        "identity": provider.metadata.get("identity")
        if isinstance(provider.metadata, dict)
        else None,
        "identityFingerprint": provider_identity_fingerprint(provider),
        "accountFingerprint": provider_account_fingerprint(provider),
        "sourceMode": provider_identity_source_mode(provider, source_model),
        "stateIdentityKey": provider_state_identity_key(provider),
        "switchingState": switching_state_vm(provider),
        "selected": selected,
        "visible": True,
        "available": provider_available,
        "stale": stale,
        "errorState": {
            "hasError": error_message is not None
            or bool(source_unavailable_text and not provider.error),
            "message": error_message or source_unavailable_text,
        },
        "planLabel": plan_label(provider),
        "updatedText": updated_text,
        "subtitle": provider_subtitle(provider, source_presentation),
        "links": {"dashboardUrl": dashboard_url, "statusUrl": effective_status_url},
        "metrics": metrics,
        "extraUsage": extra_usage_vm(provider),
        "cost": cost_vm(provider),
        "actions": actions_vm(dashboard_url, effective_status_url),
    }
