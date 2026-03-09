import base64
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from core.ai_usage_monitor.cli import (
    config_ui_payload,
    config_ui_state_payload,
    main,
    parse_popup_vm_args,
)


class CLIConfigTests(unittest.TestCase):
    def test_config_ui_payload_includes_descriptors_and_config(self):
        payload = config_ui_payload()

        self.assertIn("config", payload)
        self.assertIn("descriptors", payload)
        self.assertNotIn("state", payload)
        self.assertTrue(any(item["id"] == "copilot" for item in payload["descriptors"]))
        self.assertFalse(any(item["id"] == "kimi" for item in payload["descriptors"]))
        copilot = next(
            item for item in payload["descriptors"] if item["id"] == "copilot"
        )
        self.assertIn("branding", copilot)
        self.assertIn("providerCapabilities", copilot)
        self.assertIn("iconKey", copilot)
        self.assertIn("settingsAvailability", copilot)
        self.assertIn("statusPageUrl", copilot)
        self.assertIn("usageDashboardUrl", copilot)
        self.assertIn("usageDashboardBySource", copilot)
        self.assertIn("supportedSources", copilot)
        self.assertIn("preferredSourcePolicy", copilot)
        self.assertIn("fetchStrategy", copilot)
        config_map = {entry["id"]: entry for entry in payload["config"]["providers"]}
        self.assertNotIn("apiKey", config_map["copilot"])
        copilot_fields = [item["key"] for item in copilot["configFields"]]
        self.assertNotIn("apiKey", copilot_fields)

    def test_config_ui_state_payload_wraps_state(self):
        with mock.patch(
            "core.ai_usage_monitor.cli.collect_state_payload",
            return_value={"providers": [{"id": "codex"}]},
        ):
            payload = config_ui_state_payload()

        self.assertIn("state", payload)
        self.assertEqual(payload["state"]["providers"][0]["id"], "codex")

    def test_config_ui_full_mode_includes_state(self):
        with mock.patch(
            "core.ai_usage_monitor.cli.config_ui_payload",
            return_value={
                "config": {"providers": []},
                "descriptors": [],
                "state": {"providers": []},
            },
        ) as payload_mock:
            with mock.patch("builtins.print") as print_mock:
                main(["config-ui-full"])

        payload_mock.assert_called_once_with(include_state=True)
        print_mock.assert_called_once()
        printed = print_mock.call_args[0][0]
        self.assertIn('"state"', printed)

    def test_popup_vm_mode_uses_popup_payload(self):
        with mock.patch(
            "core.ai_usage_monitor.cli.collect_popup_vm_payload",
            return_value={"popup": {"providers": []}},
        ):
            with mock.patch("builtins.print") as print_mock:
                main(["popup-vm"])

        print_mock.assert_called_once()
        printed = print_mock.call_args[0][0]
        self.assertIn('"popup"', printed)

    def test_popup_vm_mode_forwards_preferred_provider_id(self):
        with mock.patch(
            "core.ai_usage_monitor.cli.collect_popup_vm_payload",
            return_value={"popup": {"providers": []}},
        ) as popup_mock:
            with mock.patch("builtins.print"):
                main(["popup-vm", "codex"])

        popup_mock.assert_called_once_with(preferred_provider_id="codex", force=False)

    def test_parse_popup_vm_args_supports_force_without_provider(self):
        preferred_provider_id, force = parse_popup_vm_args(["--force"])

        self.assertIsNone(preferred_provider_id)
        self.assertTrue(force)

    def test_parse_popup_vm_args_supports_provider_and_force(self):
        preferred_provider_id, force = parse_popup_vm_args(["codex", "--force"])

        self.assertEqual(preferred_provider_id, "codex")
        self.assertTrue(force)

    def test_popup_vm_mode_forwards_force_flag(self):
        with mock.patch(
            "core.ai_usage_monitor.cli.collect_popup_vm_payload",
            return_value={"popup": {"providers": []}},
        ) as popup_mock:
            with mock.patch("builtins.print"):
                main(["popup-vm", "codex", "--force"])

        popup_mock.assert_called_once_with(preferred_provider_id="codex", force=True)

    def test_config_save_writes_normalized_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            raw = {
                "providers": [
                    {
                        "id": "copilot",
                        "enabled": True,
                        "source": "api",
                    }
                ]
            }
            encoded = base64.urlsafe_b64encode(json.dumps(raw).encode("utf-8")).decode(
                "utf-8"
            )

            with mock.patch("pathlib.Path.home", return_value=home):
                main(["config-save", encoded])
                config_file = home / ".config" / "ai-usage-monitor" / "config.json"
                self.assertTrue(config_file.exists())
                written = json.loads(config_file.read_text())
                provider_map = {entry["id"]: entry for entry in written["providers"]}
                self.assertEqual(provider_map["copilot"]["source"], "api")

    def test_config_save_rejects_sensitive_fields_over_argv(self):
        raw = {
            "providers": [
                {
                    "id": "copilot",
                    "enabled": True,
                    "source": "api",
                    "apiKey": "gho_test",
                }
            ]
        }
        encoded = base64.urlsafe_b64encode(json.dumps(raw).encode("utf-8")).decode(
            "utf-8"
        )
        with self.assertRaises(SystemExit):
            main(["config-save", encoded])

    def test_config_save_json_writes_normalized_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            raw = {"providers": [{"id": "opencode", "enabled": False, "source": "web"}]}

            with mock.patch("pathlib.Path.home", return_value=home):
                main(["config-save-json", json.dumps(raw)])
                config_file = home / ".config" / "ai-usage-monitor" / "config.json"
                written = json.loads(config_file.read_text())
                provider_map = {entry["id"]: entry for entry in written["providers"]}
                self.assertFalse(provider_map["opencode"]["enabled"])
                self.assertEqual(provider_map["opencode"]["source"], "web")

    def test_config_save_json_accepts_opencode_cookie_source_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            raw = {
                "providers": [
                    {
                        "id": "opencode",
                        "enabled": True,
                        "source": "auto",
                        "cookieSource": "off",
                    }
                ]
            }

            with mock.patch("pathlib.Path.home", return_value=home):
                main(["config-save-json", json.dumps(raw)])
                config_file = home / ".config" / "ai-usage-monitor" / "config.json"
                written = json.loads(config_file.read_text())
                provider_map = {entry["id"]: entry for entry in written["providers"]}
                self.assertEqual(provider_map["opencode"]["cookieSource"], "off")

    def test_config_save_json_rejects_non_object_payload(self):
        with self.assertRaises(SystemExit):
            main(["config-save-json", "[]"])

    def test_config_save_json_rejects_sensitive_fields_over_argv(self):
        raw = {"providers": [{"id": "copilot", "apiKey": "gho_test"}]}
        with self.assertRaises(SystemExit):
            main(["config-save-json", json.dumps(raw)])

    def test_config_save_json_preserves_existing_secret_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            config_dir = home / ".config" / "ai-usage-monitor"
            config_dir.mkdir(parents=True, exist_ok=True)
            existing = {
                "version": 1,
                "refreshInterval": 60,
                "overviewProviderIds": [],
                "providers": [
                    {
                        "id": "copilot",
                        "enabled": True,
                        "source": "api",
                        "apiKey": "gho_existing",
                    }
                ],
            }
            (config_dir / "config.json").write_text(json.dumps(existing))
            incoming = {
                "providers": [{"id": "copilot", "enabled": False, "source": "api"}]
            }
            with mock.patch("pathlib.Path.home", return_value=home):
                main(["config-save-json", json.dumps(incoming)])
                written = json.loads((config_dir / "config.json").read_text())
            provider_map = {entry["id"]: entry for entry in written["providers"]}
            self.assertEqual(provider_map["copilot"]["apiKey"], "gho_existing")
            self.assertFalse(provider_map["copilot"]["enabled"])

    def test_config_set_provider_rejects_sensitive_field_over_argv(self):
        with self.assertRaises(SystemExit):
            main(["config-set-provider", "copilot", "apiKey", "gho_test"])

    def test_config_save_json_returns_sanitized_config_for_followup_saves(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            config_dir = home / ".config" / "ai-usage-monitor"
            config_dir.mkdir(parents=True, exist_ok=True)
            existing = {
                "version": 1,
                "refreshInterval": 60,
                "overviewProviderIds": [],
                "providers": [
                    {
                        "id": "copilot",
                        "enabled": True,
                        "source": "api",
                        "apiKey": "gho_existing",
                    }
                ],
            }
            (config_dir / "config.json").write_text(json.dumps(existing))
            incoming = {
                "providers": [{"id": "copilot", "enabled": False, "source": "api"}]
            }

            with mock.patch("pathlib.Path.home", return_value=home):
                with mock.patch("builtins.print") as print_mock:
                    main(["config-save-json", json.dumps(incoming)])
                first_payload = json.loads(print_mock.call_args[0][0])
                self.assertNotIn(
                    "apiKey",
                    {
                        entry["id"]: entry
                        for entry in first_payload["config"]["providers"]
                    }["copilot"],
                )
                main(["config-save-json", json.dumps(first_payload["config"])])


if __name__ == "__main__":
    unittest.main()
