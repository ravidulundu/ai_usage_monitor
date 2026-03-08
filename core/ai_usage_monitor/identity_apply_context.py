from __future__ import annotations

from typing import Any

from core.ai_usage_monitor.identity_fingerprint import normalize, source_mode
from core.ai_usage_monitor.identity_snapshot import apply_provider_snapshot
from core.ai_usage_monitor.models import ProviderState


def previous_entry(providers_store: dict[str, Any], provider_id: str) -> dict[str, Any]:
    entry = providers_store.get(provider_id)
    return entry if isinstance(entry, dict) else {}


def previous_identity_fields(previous: dict[str, Any]) -> dict[str, str]:
    return {
        "stateFingerprint": normalize(
            previous.get("stateFingerprint") or previous.get("fingerprint")
        ),
        "stateKey": normalize(previous.get("stateKey")),
        "accountFingerprint": normalize(previous.get("accountFingerprint")),
        "sourceMode": normalize(
            previous.get("sourceMode")
            or source_mode(normalize(previous.get("sourceId")))
        ),
    }


def identity_switch_flags(
    previous_fields: dict[str, str],
    state_fingerprint: str,
    account_fingerprint: str,
    source_mode_value: str,
) -> tuple[bool, bool, bool]:
    switched = bool(
        previous_fields["stateFingerprint"]
        and previous_fields["stateFingerprint"] != state_fingerprint
    )
    account_switched = bool(
        previous_fields["accountFingerprint"]
        and previous_fields["accountFingerprint"] != account_fingerprint
    )
    source_switched = bool(
        previous_fields["sourceMode"]
        and previous_fields["sourceMode"] != source_mode_value
    )
    return switched, account_switched, source_switched


def identity_presence(identity: dict[str, str]) -> tuple[bool, str, str]:
    account_known = bool(identity["accountId"])
    session_known = bool(identity["sessionId"])
    known = account_known or session_known
    scope = "account" if account_known else ("session" if session_known else "provider")
    confidence = "high" if account_known else ("medium" if session_known else "low")
    return known, scope, confidence


def restore_snapshot_if_available(
    provider: ProviderState,
    snapshots: dict[str, Any],
    *,
    switched: bool,
    identity_known: bool,
    state_key: str,
    state_fingerprint: str,
) -> bool:
    if not (switched and provider.installed and provider.enabled and identity_known):
        return False
    previous_snapshot = snapshots.get(state_key) or snapshots.get(state_fingerprint)
    if isinstance(previous_snapshot, dict):
        return apply_provider_snapshot(provider, previous_snapshot)
    return False


def build_identity_payload(
    identity: dict[str, str],
    *,
    state_fingerprint: str,
    identity_known: bool,
    identity_scope: str,
    identity_confidence: str,
    switched: bool,
    account_switched: bool,
    source_switched: bool,
    changed: bool,
    restored_from_snapshot: bool,
) -> dict[str, Any]:
    return {
        **identity,
        "fingerprint": state_fingerprint,
        "known": identity_known,
        "scope": identity_scope,
        "confidence": identity_confidence,
        "switched": switched,
        "accountChanged": account_switched,
        "sourceChanged": source_switched,
        "changed": changed,
        "restoredFromSnapshot": restored_from_snapshot,
    }
