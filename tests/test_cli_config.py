import base64
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from core.ai_usage_monitor.cli import config_ui_payload, config_ui_state_payload, main


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

        popup_mock.assert_called_once_with(preferred_provider_id="codex")

    def test_config_save_writes_normalized_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
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

            with mock.patch("pathlib.Path.home", return_value=home):
                main(["config-save", encoded])
                config_file = home / ".config" / "ai-usage-monitor" / "config.json"
                self.assertTrue(config_file.exists())
                written = json.loads(config_file.read_text())
                provider_map = {entry["id"]: entry for entry in written["providers"]}
                self.assertEqual(provider_map["copilot"]["apiKey"], "gho_test")

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


if __name__ == "__main__":
    unittest.main()
