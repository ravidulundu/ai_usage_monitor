from __future__ import annotations

import json
import sys

from core.ai_usage_monitor.collector import (
    collect_legacy_usage,
    collect_popup_vm_payload,
    collect_state_payload,
)
from core.ai_usage_monitor.config import (
    decode_base64_json,
    load_config,
    save_config,
    update_provider_config,
)
from core.ai_usage_monitor.providers.registry import ProviderRegistry


def config_ui_payload(include_state: bool = False) -> dict:
    registry = ProviderRegistry()
    payload = {
        "config": load_config(),
        "descriptors": registry.descriptor_payload(),
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


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    mode = "legacy"
    if argv and argv[0] in {
        "legacy",
        "state",
        "popup-vm",
        "config-ui",
        "config-ui-full",
        "config-ui-state",
        "config-save",
        "config-save-json",
        "config-set-provider",
    }:
        mode = argv[0]

    if mode == "state":
        payload = collect_state_payload()
    elif mode == "popup-vm":
        preferred_provider_id = parse_preferred_provider_id(
            argv[1] if len(argv) > 1 else None
        )
        payload = collect_popup_vm_payload(preferred_provider_id=preferred_provider_id)
    elif mode == "config-ui":
        payload = config_ui_payload()
    elif mode == "config-ui-full":
        payload = config_ui_payload(include_state=True)
    elif mode == "config-ui-state":
        payload = config_ui_state_payload()
    elif mode == "config-save":
        if len(argv) < 2:
            raise SystemExit("config-save requires a base64 JSON payload")
        payload = {
            "ok": True,
            "config": save_config(decode_base64_json(argv[1])),
        }
    elif mode == "config-save-json":
        if len(argv) < 2:
            raise SystemExit("config-save-json requires a JSON payload")
        payload = {
            "ok": True,
            "config": save_config(json.loads(argv[1])),
        }
    elif mode == "config-set-provider":
        if len(argv) < 4:
            raise SystemExit(
                "config-set-provider requires: <providerId> <field> <value>"
            )
        payload = {
            "ok": True,
            "config": update_provider_config(
                argv[1], argv[2], parse_cli_value(argv[3])
            ),
        }
    else:
        payload = collect_legacy_usage()
    print(json.dumps(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
