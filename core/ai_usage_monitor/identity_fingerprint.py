from __future__ import annotations

import hashlib
import json
from typing import Any

from core.ai_usage_monitor.models import ProviderState


_ACCOUNT_KEYS = (
    "accountId",
    "account_id",
    "organizationId",
    "organization_id",
    "orgId",
    "org_id",
    "teamId",
    "team_id",
    "email",
    "userId",
    "user_id",
    "ownerId",
    "owner_id",
    "workspaceId",
    "workspace_id",
    "projectId",
    "project_id",
    "groupId",
    "group_id",
)

_SESSION_KEYS = (
    "sessionId",
    "session_id",
    "threadId",
    "thread_id",
    "conversationId",
    "conversation_id",
)

_LOCAL_SOURCE_IDS = {"cli", "local", "oauth", "local_cli"}
_API_SOURCE_IDS = {"api"}
_WEB_SOURCE_IDS = {"web"}


def normalize(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def mapping_value(mapping: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = normalize(mapping.get(key))
        if value:
            return value
    return ""


def legacy_mapping(legacy: Any) -> dict[str, Any]:
    return legacy if isinstance(legacy, dict) else {}


def identity_fingerprint(identity: dict[str, str]) -> str:
    raw = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:20]


def source_id(provider: ProviderState, configured_source: str) -> str:
    source_model = (
        provider.source_model if isinstance(provider.source_model, dict) else {}
    )
    source_strategy_raw = source_model.get("sourceStrategy")
    strategy: dict[str, Any] = (
        source_strategy_raw if isinstance(source_strategy_raw, dict) else {}
    )
    resolved = (
        normalize(strategy.get("resolvedSource"))
        or normalize(source_model.get("activeSource"))
        or normalize(provider.source)
        or normalize(configured_source)
    )
    return resolved or "unknown"


def source_mode(source_id_value: str) -> str:
    normalized = normalize(source_id_value)
    if normalized == "remote":
        normalized = "web"
    if normalized in _LOCAL_SOURCE_IDS:
        return "local_cli"
    if normalized in _API_SOURCE_IDS:
        return "api"
    if normalized in _WEB_SOURCE_IDS:
        return "web"
    if normalized in {"probe", "auto"}:
        return "probe"
    return normalized or "unknown"


def account_fingerprint(provider_id: str, account_id: str, session_id: str) -> str:
    return identity_fingerprint(
        {
            "providerId": provider_id,
            "accountId": account_id,
            "sessionId": session_id,
        }
    )


def state_key(
    provider_id: str, account_fingerprint_value: str, source_mode_value: str
) -> str:
    return f"{provider_id}:{account_fingerprint_value}:{source_mode_value or 'unknown'}"


def state_fingerprint(
    provider_id: str, account_fingerprint_value: str, source_mode_value: str
) -> str:
    return identity_fingerprint(
        {
            "providerId": provider_id,
            "accountFingerprint": account_fingerprint_value,
            "sourceMode": source_mode_value or "unknown",
        }
    )


def provider_identity_payload(
    provider: ProviderState, provider_legacy: Any, configured_source: str
) -> dict[str, str]:
    extras = provider.extras if isinstance(provider.extras, dict) else {}
    metadata = provider.metadata if isinstance(provider.metadata, dict) else {}
    legacy = legacy_mapping(provider_legacy)
    provider_id = normalize(provider.id)

    account_id = (
        mapping_value(extras, _ACCOUNT_KEYS)
        or mapping_value(metadata, _ACCOUNT_KEYS)
        or mapping_value(legacy, _ACCOUNT_KEYS)
    )
    session_id = (
        mapping_value(extras, _SESSION_KEYS)
        or mapping_value(metadata, _SESSION_KEYS)
        or mapping_value(legacy, _SESSION_KEYS)
    )
    source_id_value = source_id(provider, configured_source)
    source_mode_value = source_mode(source_id_value)
    account_fingerprint_value = account_fingerprint(provider_id, account_id, session_id)
    state_key_value = state_key(
        provider_id, account_fingerprint_value, source_mode_value
    )
    state_fingerprint_value = state_fingerprint(
        provider_id, account_fingerprint_value, source_mode_value
    )

    return {
        "providerId": provider_id,
        "sourceId": source_id_value,
        "sourceMode": source_mode_value,
        "accountId": account_id,
        "sessionId": session_id,
        "accountFingerprint": account_fingerprint_value,
        "stateKey": state_key_value,
        "stateFingerprint": state_fingerprint_value,
    }
