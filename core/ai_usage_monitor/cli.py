from __future__ import annotations

import json
import sys

from core.ai_usage_monitor.collector import (
    collect_legacy_usage,
    collect_popup_vm_payload,
    collect_state_payload,
)
from core.ai_usage_monitor.config import (
    config_contains_sensitive_fields,
    decode_base64_json,
    is_sensitive_provider_field,
    load_config,
    merge_sensitive_provider_fields,
    sanitize_config_for_ui,
    save_config,
    update_provider_config,
)
from core.ai_usage_monitor.providers.registry import ProviderRegistry


def config_ui_payload(include_state: bool = False) -> dict:
    registry = ProviderRegistry()
    payload = {
        "config": sanitize_config_for_ui(load_config()),
        "descriptors": registry.descriptor_payload(include_secret_fields=False),
    }
    if include_state:
        payload["state"] = collect_state_payload()
    return payload


def config_ui_state_payload() -> dict:
    return {"state": collect_state_payload()}


def parse_cli_value(raw: str) -> str | bool | None:
    if raw == "__null__":
        return None
    if raw == "true":
        return True
    if raw == "false":
        return False
    return raw


def parse_preferred_provider_id(raw: str | None) -> str | None:
    if raw is None:
        return None
    value = str(raw).strip()
    if value in {"", "auto", "overview"}:
        return None
    return value


def parse_popup_vm_args(argv: list[str]) -> tuple[str | None, bool]:
    preferred_provider_id: str | None = None
    force = False
    for raw in argv:
        if raw == "--force":
            force = True
            continue
        if preferred_provider_id is None:
            preferred_provider_id = parse_preferred_provider_id(raw)
    return preferred_provider_id, force


def parse_mode(argv: list[str]) -> tuple[str, list[str]]:
    modes = {
        "legacy",
        "state",
        "popup-vm",
        "config-ui",
        "config-ui-full",
        "config-ui-state",
        "config-save",
        "config-save-json",
        "config-set-provider",
    }
    if argv and argv[0] in modes:
        return argv[0], argv[1:]
    return "legacy", argv


def _handle_legacy(_argv: list[str]) -> dict:
    return collect_legacy_usage()


def _handle_state(_argv: list[str]) -> dict:
    return collect_state_payload()


def _handle_popup_vm(argv: list[str]) -> dict:
    preferred_provider_id, force = parse_popup_vm_args(argv)
    return collect_popup_vm_payload(
        preferred_provider_id=preferred_provider_id,
        force=force,
    )


def _handle_config_ui(_argv: list[str]) -> dict:
    return config_ui_payload()


def _handle_config_ui_full(_argv: list[str]) -> dict:
    return config_ui_payload(include_state=True)


def _handle_config_ui_state(_argv: list[str]) -> dict:
    return config_ui_state_payload()


def _handle_config_save(argv: list[str]) -> dict:
    if not argv:
        raise SystemExit("config-save requires a base64 JSON payload")
    payload = decode_base64_json(argv[0])
    if config_contains_sensitive_fields(payload):
        raise SystemExit(
            "config-save does not accept sensitive fields over argv; use config file or env"
        )
    merged = merge_sensitive_provider_fields(payload)
    saved = save_config(merged)
    return {
        "ok": True,
        "config": sanitize_config_for_ui(saved),
    }


def _handle_config_save_json(argv: list[str]) -> dict:
    if not argv:
        raise SystemExit("config-save-json requires a JSON payload")
    payload = json.loads(argv[0])
    if not isinstance(payload, dict):
        raise SystemExit("config-save-json payload must be a JSON object")
    if config_contains_sensitive_fields(payload):
        raise SystemExit(
            "config-save-json does not accept sensitive fields over argv; use config file or env"
        )
    merged = merge_sensitive_provider_fields(payload)
    saved = save_config(merged)
    return {
        "ok": True,
        "config": sanitize_config_for_ui(saved),
    }


def _handle_config_set_provider(argv: list[str]) -> dict:
    if len(argv) < 3:
        raise SystemExit("config-set-provider requires: <providerId> <field> <value>")
    provider_id = argv[0]
    field = argv[1]
    if is_sensitive_provider_field(provider_id, field):
        raise SystemExit(
            f"config-set-provider does not accept sensitive field over argv: {field}"
        )
    try:
        config = update_provider_config(provider_id, field, parse_cli_value(argv[2]))
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    return {"ok": True, "config": config}


COMMAND_HANDLERS = {
    "legacy": _handle_legacy,
    "state": _handle_state,
    "popup-vm": _handle_popup_vm,
    "config-ui": _handle_config_ui,
    "config-ui-full": _handle_config_ui_full,
    "config-ui-state": _handle_config_ui_state,
    "config-save": _handle_config_save,
    "config-save-json": _handle_config_save_json,
    "config-set-provider": _handle_config_set_provider,
}


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    mode, rest = parse_mode(argv)
    payload = COMMAND_HANDLERS[mode](rest)
    print(json.dumps(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
