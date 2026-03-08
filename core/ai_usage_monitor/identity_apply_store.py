from __future__ import annotations

from typing import Any

from core.ai_usage_monitor.identity_fingerprint import normalize
from core.ai_usage_monitor.identity_snapshot import (
    provider_has_usage_snapshot,
    provider_snapshot_payload,
    prune_snapshots,
)
from core.ai_usage_monitor.models import ProviderState


def apply_identity_to_provider_extras(
    provider: ProviderState,
    *,
    identity: dict[str, str],
    identity_payload: dict[str, Any],
    state_fingerprint: str,
    state_key: str,
    source_mode_value: str,
    account_fingerprint: str,
    identity_known: bool,
    identity_scope: str,
    identity_confidence: str,
    switched: bool,
    account_switched: bool,
    source_switched: bool,
    changed: bool,
    restored_from_snapshot: bool,
) -> None:
    provider.metadata = dict(provider.metadata or {})
    provider.metadata["identity"] = identity_payload

    provider.extras = dict(provider.extras or {})
    provider.extras["identityFingerprint"] = state_fingerprint
    provider.extras["stateFingerprint"] = state_fingerprint
    provider.extras["stateIdentityKey"] = state_key
    provider.extras["providerStateKey"] = (
        f"{identity['providerId']}:{source_mode_value}"
    )
    provider.extras["accountStateKey"] = (
        f"{identity['providerId']}:{account_fingerprint}"
    )
    provider.extras["accountFingerprint"] = account_fingerprint
    provider.extras["sourceMode"] = source_mode_value
    provider.extras["identityKnown"] = identity_known
    provider.extras["identityScope"] = identity_scope
    provider.extras["identityConfidence"] = identity_confidence
    provider.extras["identityMissing"] = not identity_known
    if identity["accountId"] and not normalize(provider.extras.get("accountId")):
        provider.extras["accountId"] = identity["accountId"]
    if switched:
        provider.extras["identitySwitched"] = True
    if account_switched:
        provider.extras["accountSwitched"] = True
    if source_switched:
        provider.extras["sourceSwitched"] = True
    if changed:
        provider.extras["identityChanged"] = True
    else:
        provider.extras.pop("identityChanged", None)
    if restored_from_snapshot:
        provider.extras["accountSnapshotRestored"] = True
    else:
        provider.extras.pop("accountSnapshotRestored", None)


def clear_provider_usage_on_change(provider: ProviderState) -> None:
    provider.primary_metric = None
    provider.secondary_metric = None
    provider.local_usage = None
    provider.extras["hasData"] = False
    if "buckets" in provider.extras:
        provider.extras["buckets"] = []


def next_snapshots(
    snapshots: dict[str, Any],
    *,
    identity_known: bool,
    provider: ProviderState,
    state_key: str,
    now_iso: str,
) -> dict[str, Any]:
    next_state = dict(snapshots)
    if (
        identity_known
        and provider.installed
        and provider.enabled
        and not provider.error
        and provider_has_usage_snapshot(provider)
    ):
        next_state[state_key] = provider_snapshot_payload(provider, captured_at=now_iso)
        return prune_snapshots(next_state)
    return next_state


def store_identity_entry(
    *,
    state_fingerprint: str,
    state_key: str,
    identity: dict[str, str],
    source_mode_value: str,
    account_fingerprint: str,
    previous_state_key: str,
    now_iso: str,
    identity_known: bool,
    identity_scope: str,
    identity_confidence: str,
    snapshots: dict[str, Any],
) -> dict[str, Any]:
    return {
        "fingerprint": state_fingerprint,
        "stateFingerprint": state_fingerprint,
        "stateKey": state_key,
        "providerId": identity["providerId"],
        "sourceId": identity["sourceId"],
        "sourceMode": source_mode_value,
        "accountId": identity["accountId"],
        "sessionId": identity["sessionId"],
        "accountFingerprint": account_fingerprint,
        "previousStateKey": previous_state_key or None,
        "updatedAt": now_iso,
        "identityKnown": identity_known,
        "identityScope": identity_scope,
        "identityConfidence": identity_confidence,
        "snapshots": snapshots,
    }
