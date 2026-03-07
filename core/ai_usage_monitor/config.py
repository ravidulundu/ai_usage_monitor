from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any

from core.ai_usage_monitor.providers.registry import ProviderRegistry


def default_config() -> dict[str, Any]:
    registry = ProviderRegistry()
    return {
        "version": 1,
        "refreshInterval": 60,
        "providers": [
            {
                "id": descriptor.id,
                "enabled": descriptor.default_enabled,
                "source": descriptor.source_modes[0],
            }
            for descriptor in registry.list_descriptors()
        ],
    }


def config_path() -> Path:
    return Path.home() / ".config" / "ai-usage-monitor" / "config.json"


def ensure_config_dir() -> None:
    config_path().parent.mkdir(parents=True, exist_ok=True)


def normalize_config(data: dict[str, Any] | None) -> dict[str, Any]:
    registry = ProviderRegistry()
    defaults = default_config()
    normalized: dict[str, Any] = {
        "version": 1,
        "refreshInterval": defaults["refreshInterval"],
        "providers": [],
    }

    if isinstance(data, dict):
        refresh = data.get("refreshInterval")
        if isinstance(refresh, int) and refresh > 0:
            normalized["refreshInterval"] = refresh

    user_entries = {}
    if isinstance(data, dict) and isinstance(data.get("providers"), list):
        for entry in data["providers"]:
            if isinstance(entry, dict) and isinstance(entry.get("id"), str):
                user_entries[entry["id"]] = entry

    for descriptor in registry.list_descriptors():
        entry = user_entries.get(descriptor.id, {})
        normalized_entry = dict(entry) if isinstance(entry, dict) else {}
        source = entry.get("source")
        if descriptor.id == "opencode" and source == "web":
            source = "auto"
        if source not in descriptor.source_modes:
            source = descriptor.source_modes[0]
        normalized_entry["id"] = descriptor.id
        normalized_entry["enabled"] = bool(entry.get("enabled", descriptor.default_enabled))
        normalized_entry["source"] = source
        normalized["providers"].append(normalized_entry)

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
