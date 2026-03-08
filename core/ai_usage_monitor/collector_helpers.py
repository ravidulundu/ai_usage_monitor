from __future__ import annotations

from typing import Any, Callable, cast

from core.ai_usage_monitor.identity import apply_identity_to_provider
from core.ai_usage_monitor.models import ProviderState
from core.ai_usage_monitor.providers.base import ProviderDescriptor
from core.ai_usage_monitor.providers.fetch_strategies import fetch_strategy_for
from core.ai_usage_monitor.providers.registry import ProviderRegistry
from core.ai_usage_monitor.sources import (
    build_provider_source_model,
    resolve_provider_source_plan,
)

ProviderCollector = Callable[[dict[str, Any]], tuple[dict[str, Any], object]]


def source_attempt_sequence(
    source_plan: dict[str, Any], preferred_source: str
) -> list[str]:
    candidates = [
        str(item.get("source") or "").strip().lower()
        for item in list(source_plan.get("candidates") or [])
        if isinstance(item, dict) and str(item.get("source") or "").strip()
    ]
    if not candidates:
        resolved_hint = str(source_plan.get("resolvedSourceHint") or "").strip().lower()
        if resolved_hint:
            candidates = [resolved_hint]

    if preferred_source in {"auto", "probe", "local_cli"}:
        return candidates

    explicit = str(preferred_source or "").strip().lower()
    if explicit and explicit not in {"probe", "local_cli"}:
        return [explicit]
    return candidates


def attempt_is_authoritative(provider_state: ProviderState) -> bool:
    return provider_state.installed is not False and not provider_state.error


def disabled_provider_state(
    provider_id: str,
    descriptor: ProviderDescriptor | None,
    settings: dict[str, Any],
) -> ProviderState:
    return ProviderState(
        id=provider_id,
        display_name=descriptor.display_name if descriptor else provider_id,
        enabled=False,
        installed=False,
        authenticated=False,
        status="disabled",
        source=str(
            settings.get("source", descriptor.source_modes[0] if descriptor else "auto")
        ),
        metadata={},
    )


def collect_provider(
    provider_id: str,
    collector: ProviderCollector,
    settings: dict[str, Any],
    descriptor: ProviderDescriptor | None,
) -> tuple[dict[str, Any], ProviderState, str, bool]:
    source_plan = resolve_provider_source_plan(
        descriptor, settings, configured_source=str(settings.get("source", ""))
    )
    base_settings = dict(settings or {})
    preferred_source = str(source_plan.get("preferredSource") or "").strip()
    attempt_sources = source_attempt_sequence(source_plan, preferred_source)

    enabled = bool(
        settings.get("enabled", descriptor.default_enabled if descriptor else True)
    )
    if enabled:
        provider_legacy = {"installed": False}
        provider_state = ProviderState(
            id=provider_id,
            display_name=descriptor.display_name if descriptor else provider_id,
            installed=False,
        )
        attempts = attempt_sources or [
            str(source_plan.get("resolvedSourceHint") or preferred_source or "")
            .strip()
            .lower()
        ]
        attempted = False
        for attempt_source in attempts:
            normalized_source = str(attempt_source or "").strip().lower()
            if not normalized_source or normalized_source in {"probe", "local_cli"}:
                continue
            attempt_settings = dict(base_settings)
            attempt_settings["source"] = normalized_source
            provider_legacy, raw_state = collector(attempt_settings)
            provider_state = cast(ProviderState, raw_state)
            attempted = True
            if attempt_is_authoritative(provider_state):
                break

        if not attempted:
            fallback_source = (
                str(source_plan.get("resolvedSourceHint") or "").strip().lower()
            )
            attempt_settings = dict(base_settings)
            if fallback_source and fallback_source not in {"probe", "local_cli"}:
                attempt_settings["source"] = fallback_source
            provider_legacy, raw_state = collector(attempt_settings)
            provider_state = cast(ProviderState, raw_state)
    else:
        provider_legacy = {"installed": False, "enabled": False}
        provider_state = disabled_provider_state(provider_id, descriptor, settings)

    provider_state.enabled = enabled
    provider_state.metadata = dict(provider_state.metadata or {})
    configured_source = str(
        source_plan.get("preferredSource")
        or settings.get(
            "source",
            descriptor.source_modes[0]
            if descriptor
            else provider_state.source or "auto",
        )
    )
    provider_state.metadata["configuredSource"] = configured_source
    provider_state.metadata["sourceResolutionPlan"] = source_plan
    if descriptor:
        provider_state.metadata["branding"] = descriptor.branding.to_dict()
        strategy = fetch_strategy_for(provider_id)
        provider_state.metadata["fetchStrategy"] = {
            "supportsProbe": bool(strategy.supports_probe)
            if strategy
            else bool(source_plan.get("supportsProbe")),
        }
    provider_state.source_model = build_provider_source_model(
        provider=provider_state,
        descriptor=descriptor,
        settings=base_settings,
        configured_source=configured_source,
        resolution=source_plan,
    )
    provider_state.metadata["sourceModel"] = provider_state.source_model
    return provider_legacy, provider_state, configured_source, enabled


def identity_switched(provider_state: ProviderState) -> bool:
    identity_payload = (
        provider_state.metadata.get("identity")
        if isinstance(provider_state.metadata, dict)
        else {}
    )
    return (
        bool(identity_payload.get("switched"))
        if isinstance(identity_payload, dict)
        else False
    )


def build_provider_records(
    registry: ProviderRegistry,
    settings_map: dict[str, dict[str, Any]],
    identity_store: dict[str, Any],
    collectors: dict[str, ProviderCollector],
) -> list[dict[str, Any]]:
    provider_records: list[dict[str, Any]] = []
    for descriptor in registry.list_descriptors():
        provider_id = descriptor.id
        collector = collectors.get(provider_id)
        if collector is None:
            continue
        settings = settings_map.get(provider_id, {})
        provider_legacy, provider_state, configured_source, enabled = collect_provider(
            provider_id, collector, settings, descriptor
        )
        identity_changed = apply_identity_to_provider(
            provider_state,
            provider_legacy,
            configured_source=configured_source,
            store=identity_store,
        )

        provider_records.append(
            {
                "provider_id": provider_id,
                "collector": collector,
                "settings": settings,
                "descriptor": descriptor,
                "enabled": enabled,
                "configured_source": configured_source,
                "legacy": provider_legacy,
                "state": provider_state,
                "identity_changed": identity_changed,
                "identity_switched": identity_switched(provider_state),
            }
        )
    return provider_records


def changed_provider_ids(provider_records: list[dict[str, Any]]) -> set[str]:
    return {
        record["provider_id"]
        for record in provider_records
        if (record["identity_changed"] or record["identity_switched"])
        and record["enabled"]
        and record["state"].installed
    }


def refresh_changed_provider_records(
    provider_records: list[dict[str, Any]],
    changed_ids: set[str],
    identity_store: dict[str, Any],
) -> None:
    if not changed_ids:
        return
    for record in provider_records:
        if record["provider_id"] not in changed_ids:
            continue
        provider_legacy, provider_state, configured_source, _enabled = collect_provider(
            record["provider_id"],
            record["collector"],
            record["settings"],
            record["descriptor"],
        )
        apply_identity_to_provider(
            provider_state,
            provider_legacy,
            configured_source=configured_source,
            store=identity_store,
        )
        identity = provider_state.metadata.get("identity")
        if isinstance(identity, dict):
            identity["refetchedAfterChange"] = True
        record["legacy"] = provider_legacy
        record["state"] = provider_state
