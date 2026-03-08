from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any

from core.ai_usage_monitor.providers.base import ProviderDescriptor
from core.ai_usage_monitor.providers.registry import ProviderRegistry

_LOCAL_SOURCE_IDS = {"cli", "local", "oauth"}
_REMOTE_SOURCE_IDS = {"api", "web", "remote"}


def coerce_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "on"}:
            return True
        if lowered in {"false", "0", "no", "off"}:
            return False
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    return default


def default_config() -> dict[str, Any]:
    registry = ProviderRegistry()
    return {
        "version": 1,
        "refreshInterval": 60,
        "overviewProviderIds": [],
        "providers": [
            {
                "id": descriptor.id,
                "enabled": descriptor.default_enabled,
                "source": _default_source_for_descriptor(descriptor),
            }
            for descriptor in registry.list_descriptors()
        ],
    }


def _supports_local_first_source(descriptor: ProviderDescriptor) -> bool:
    source_modes = set(descriptor.source_modes or ())
    supports_local = len(source_modes & _LOCAL_SOURCE_IDS) > 0
    supports_remote = len(source_modes & _REMOTE_SOURCE_IDS) > 0
    return supports_local and supports_remote


def _allowed_sources_for_descriptor(descriptor: ProviderDescriptor) -> set[str]:
    allowed = set(descriptor.source_modes or ())
    if _supports_local_first_source(descriptor):
        allowed.add("local_cli")
    return allowed


def _default_source_for_descriptor(descriptor: ProviderDescriptor) -> str:
    if (
        _supports_local_first_source(descriptor)
        and str(descriptor.preferred_source_policy or "").strip().lower()
        == "local_first"
    ):
        return "local_cli"
    return str(descriptor.source_modes[0])


def config_path() -> Path:
    return Path.home() / ".config" / "ai-usage-monitor" / "config.json"


def ensure_config_dir() -> None:
    config_path().parent.mkdir(parents=True, exist_ok=True)


def _normalize_overview_provider_ids(
    raw_overview: Any, provider_ids: set[str]
) -> list[str]:
    if not isinstance(raw_overview, list):
        return []
    selected_ids: list[str] = []
    for value in raw_overview:
        if not isinstance(value, str):
            continue
        if value not in provider_ids:
            continue
        if value in selected_ids:
            continue
        selected_ids.append(value)
        if len(selected_ids) >= 3:
            break
    return selected_ids


def _user_provider_entries(data: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not isinstance(data, dict) or not isinstance(data.get("providers"), list):
        return {}
    user_entries: dict[str, dict[str, Any]] = {}
    for entry in data["providers"]:
        if isinstance(entry, dict) and isinstance(entry.get("id"), str):
            user_entries[entry["id"]] = entry
    return user_entries


def _normalize_provider_entry(
    descriptor: ProviderDescriptor, entry: dict[str, Any] | None
) -> dict[str, Any]:
    entry_data: dict[str, Any] = dict(entry) if isinstance(entry, dict) else {}
    source = entry_data.get("source")
    if descriptor.id == "opencode" and source == "web":
        source = "auto"
    allowed_sources = _allowed_sources_for_descriptor(descriptor)
    if source not in allowed_sources:
        source = _default_source_for_descriptor(descriptor)

    entry_data["id"] = descriptor.id
    entry_data["enabled"] = coerce_bool(
        entry_data.get("enabled"),
        descriptor.default_enabled,
    )
    entry_data["source"] = source
    return entry_data


def normalize_config(data: dict[str, Any] | None) -> dict[str, Any]:
    registry = ProviderRegistry()
    defaults = default_config()
    provider_ids = set(registry.list_ids())
    normalized: dict[str, Any] = {
        "version": 1,
        "refreshInterval": defaults["refreshInterval"],
        "overviewProviderIds": [],
        "providers": [],
    }

    if isinstance(data, dict):
        refresh = data.get("refreshInterval")
        if isinstance(refresh, int) and refresh > 0:
            normalized["refreshInterval"] = refresh
        normalized["overviewProviderIds"] = _normalize_overview_provider_ids(
            data.get("overviewProviderIds"), provider_ids
        )

    user_entries = _user_provider_entries(data)

    for descriptor in registry.list_descriptors():
        normalized["providers"].append(
            _normalize_provider_entry(descriptor, user_entries.get(descriptor.id))
        )

    return normalized


def provider_settings_map(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    providers = config.get("providers") if isinstance(config, dict) else []
    if not isinstance(providers, list):
        return {}
    result = {}
    for entry in providers:
        if isinstance(entry, dict) and isinstance(entry.get("id"), str):
            result[entry["id"]] = entry
    return result


def load_config() -> dict[str, Any]:
    path = config_path()
    if not path.exists():
        return default_config()
    try:
        data = json.loads(path.read_text())
    except Exception:
        return default_config()
    return normalize_config(data)


def save_config(data: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_config(data)
    ensure_config_dir()
    path = config_path()
    path.write_text(json.dumps(normalized, indent=2) + "\n")
    try:
        os.chmod(path, 0o600)
    except Exception:
        pass
    return normalized


def decode_base64_json(encoded: str) -> dict[str, Any]:
    raw = base64.urlsafe_b64decode(encoded.encode("utf-8")).decode("utf-8")
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("Config payload must be a JSON object.")
    return parsed


def update_provider_config(provider_id: str, field: str, value: Any) -> dict[str, Any]:
    config = load_config()
    providers = config.get("providers", [])
    if not isinstance(providers, list):
        providers = []
        config["providers"] = providers

    target = None
    for entry in providers:
        if isinstance(entry, dict) and entry.get("id") == provider_id:
            target = entry
            break

    if target is None:
        target = {"id": provider_id}
        providers.append(target)

    if value is None:
        target.pop(field, None)
    else:
        target[field] = value

    return save_config(config)
