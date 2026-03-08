from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from core.ai_usage_monitor.identity_apply_context import (
    build_identity_payload,
    identity_presence,
    identity_switch_flags,
    previous_entry,
    previous_identity_fields,
    restore_snapshot_if_available,
)
from core.ai_usage_monitor.identity_apply_store import (
    apply_identity_to_provider_extras,
    clear_provider_usage_on_change,
    next_snapshots,
    store_identity_entry,
)
from core.ai_usage_monitor.identity_fingerprint import (
    normalize,
    provider_identity_payload,
)
from core.ai_usage_monitor.identity_snapshot import (
    load_identity_store,
    save_identity_store,
    snapshot_store,
)
from core.ai_usage_monitor.models import ProviderState


def apply_identity_to_provider(
    provider: ProviderState,
    provider_legacy: Any,
    configured_source: str,
    store: dict[str, Any],
) -> bool:
    now_iso = datetime.now(timezone.utc).isoformat()
    providers_store = store.setdefault("providers", {})
    previous = previous_entry(
        providers_store if isinstance(providers_store, dict) else {}, provider.id
    )

    identity = provider_identity_payload(provider, provider_legacy, configured_source)
    state_fingerprint = normalize(identity.get("stateFingerprint"))
    state_key = normalize(identity.get("stateKey"))
    account_fingerprint = normalize(identity.get("accountFingerprint"))
    source_mode_value = normalize(identity.get("sourceMode")) or "unknown"

    previous_fields = previous_identity_fields(previous)
    switched, account_switched, source_switched = identity_switch_flags(
        previous_fields,
        state_fingerprint,
        account_fingerprint,
        source_mode_value,
    )

    identity_known, identity_scope, identity_confidence = identity_presence(identity)
    snapshots = snapshot_store(previous.get("snapshots"))
    restored_from_snapshot = restore_snapshot_if_available(
        provider,
        snapshots,
        switched=switched,
        identity_known=identity_known,
        state_key=state_key,
        state_fingerprint=state_fingerprint,
    )
    changed = switched and not restored_from_snapshot

    identity_payload = build_identity_payload(
        identity,
        state_fingerprint=state_fingerprint,
        identity_known=identity_known,
        identity_scope=identity_scope,
        identity_confidence=identity_confidence,
        switched=switched,
        account_switched=account_switched,
        source_switched=source_switched,
        changed=changed,
        restored_from_snapshot=restored_from_snapshot,
    )
    apply_identity_to_provider_extras(
        provider,
        identity=identity,
        identity_payload=identity_payload,
        state_fingerprint=state_fingerprint,
        state_key=state_key,
        source_mode_value=source_mode_value,
        account_fingerprint=account_fingerprint,
        identity_known=identity_known,
        identity_scope=identity_scope,
        identity_confidence=identity_confidence,
        switched=switched,
        account_switched=account_switched,
        source_switched=source_switched,
        changed=changed,
        restored_from_snapshot=restored_from_snapshot,
    )
    if changed and provider.installed and provider.enabled:
        clear_provider_usage_on_change(provider)

    providers_store[provider.id] = store_identity_entry(
        state_fingerprint=state_fingerprint,
        state_key=state_key,
        identity=identity,
        source_mode_value=source_mode_value,
        account_fingerprint=account_fingerprint,
        previous_state_key=previous_fields["stateKey"],
        now_iso=now_iso,
        identity_known=identity_known,
        identity_scope=identity_scope,
        identity_confidence=identity_confidence,
        snapshots=next_snapshots(
            snapshots,
            identity_known=identity_known,
            provider=provider,
            state_key=state_key,
            now_iso=now_iso,
        ),
    )
    return changed


__all__ = [
    "apply_identity_to_provider",
    "load_identity_store",
    "save_identity_store",
]
