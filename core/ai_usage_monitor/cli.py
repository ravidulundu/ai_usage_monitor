from __future__ import annotations

import json
import sys

from core.ai_usage_monitor.collector import collect_legacy_usage, collect_state_payload
from core.ai_usage_monitor.config import decode_base64_json, load_config, save_config, update_provider_config
from core.ai_usage_monitor.providers.registry import ProviderRegistry


def config_ui_payload() -> dict:
    registry = ProviderRegistry()
    state = collect_state_payload()
    return {
        "config": load_config(),
        "descriptors": registry.descriptor_payload(),
        "state": state,
    }


def parse_cli_value(raw: str):
    if raw == "__null__":
        return None
    if raw == "true":
        return True
    if raw == "false":
        return False
    return raw


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    mode = "legacy"
    if argv and argv[0] in {"legacy", "state", "config-ui", "config-save", "config-save-json", "config-set-provider"}:
        mode = argv[0]

    if mode == "state":
        payload = collect_state_payload()
    elif mode == "config-ui":
        payload = config_ui_payload()
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
            raise SystemExit("config-set-provider requires: <providerId> <field> <value>")
        payload = {
            "ok": True,
            "config": update_provider_config(argv[1], argv[2], parse_cli_value(argv[3])),
        }
    else:
        payload = collect_legacy_usage()
    print(json.dumps(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
