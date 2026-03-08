from __future__ import annotations

from typing import Any

from core.ai_usage_monitor.models import ProviderState


def provider_identity_refreshing(provider: ProviderState) -> bool:
    extras = provider.extras if isinstance(provider.extras, dict) else {}
    if extras.get("identityChanged") is True:
        return True
    metadata = provider.metadata if isinstance(provider.metadata, dict) else {}
    identity = metadata.get("identity")
    return isinstance(identity, dict) and identity.get("changed") is True


def provider_identity_fingerprint(provider: ProviderState | None) -> str:
    if provider is None:
        return ""
    metadata = provider.metadata if isinstance(provider.metadata, dict) else {}
    identity = metadata.get("identity")
    if isinstance(identity, dict):
        fingerprint = identity.get("fingerprint")
        if fingerprint:
            return str(fingerprint)
    extras = provider.extras if isinstance(provider.extras, dict) else {}
    fallback = extras.get("identityFingerprint")
    return str(fallback) if fallback else ""


def provider_account_fingerprint(provider: ProviderState | None) -> str:
    if provider is None:
        return ""
    metadata = provider.metadata if isinstance(provider.metadata, dict) else {}
    identity = metadata.get("identity")
    if isinstance(identity, dict):
        account_fp = identity.get("accountFingerprint")
        if account_fp:
            return str(account_fp)
    extras = provider.extras if isinstance(provider.extras, dict) else {}
    fallback = extras.get("accountFingerprint")
    return str(fallback) if fallback else ""


def provider_state_identity_key(provider: ProviderState | None) -> str:
    if provider is None:
        return ""
    metadata = provider.metadata if isinstance(provider.metadata, dict) else {}
    identity = metadata.get("identity")
    if isinstance(identity, dict):
        state_key = identity.get("stateKey")
        if state_key:
            return str(state_key)
    extras = provider.extras if isinstance(provider.extras, dict) else {}
    fallback = extras.get("stateIdentityKey")
    return str(fallback) if fallback else ""


def provider_identity_source_mode(
    provider: ProviderState | None, source_model: dict[str, Any]
) -> str:
    if provider is None:
        return ""
    metadata = provider.metadata if isinstance(provider.metadata, dict) else {}
    identity = metadata.get("identity")
    if isinstance(identity, dict):
        source_mode = identity.get("sourceMode")
        if source_mode:
            return str(source_mode)
    extras = provider.extras if isinstance(provider.extras, dict) else {}
    if extras.get("sourceMode"):
        return str(extras.get("sourceMode"))
    raw_strategy = source_model.get("sourceStrategy")
    strategy: dict[str, Any] = raw_strategy if isinstance(raw_strategy, dict) else {}
    resolved = strategy.get("resolvedSource") or source_model.get("activeSource")
    return str(resolved or provider.source or "")


def provider_identity_vm(provider: ProviderState | None) -> dict[str, Any] | None:
    if provider is None:
        return None
    metadata = provider.metadata if isinstance(provider.metadata, dict) else {}
    identity = metadata.get("identity")
    if not isinstance(identity, dict):
        return None
    return dict(identity)


def switching_state_vm(provider: ProviderState) -> dict[str, Any]:
    refreshing = provider_identity_refreshing(provider)
    metadata = provider.metadata if isinstance(provider.metadata, dict) else {}
    raw_identity = metadata.get("identity")
    identity: dict[str, Any] = raw_identity if isinstance(raw_identity, dict) else {}
    extras = provider.extras if isinstance(provider.extras, dict) else {}
    source_changed = bool(identity.get("sourceChanged") or extras.get("sourceSwitched"))
    account_changed = bool(
        identity.get("accountChanged") or extras.get("accountSwitched")
    )

    kind = "identity"
    title = "Switching account/source"
    message = "Refreshing usage for active identity"
    if account_changed and source_changed:
        kind = "account_source"
        title = "Account and source switched"
        message = "Refreshing usage for active account and source"
    elif account_changed:
        kind = "account"
        title = "Account switched"
        message = "Refreshing usage for active account"
    elif source_changed:
        kind = "source"
        title = "Source switched"
        message = "Refreshing usage for active source"

    return {
        "active": refreshing,
        "kind": kind,
        "title": title,
        "message": message,
    }
