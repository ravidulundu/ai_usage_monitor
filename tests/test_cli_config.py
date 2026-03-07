import base64
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from core.ai_usage_monitor.cli import config_ui_payload, main


class CLIConfigTests(unittest.TestCase):
    def test_config_ui_payload_includes_descriptors_and_config(self):
        payload = config_ui_payload()

        self.assertIn("config", payload)
        self.assertIn("descriptors", payload)
        self.assertTrue(any(item["id"] == "copilot" for item in payload["descriptors"]))
        self.assertFalse(any(item["id"] == "kimi" for item in payload["descriptors"]))
        copilot = next(item for item in payload["descriptors"] if item["id"] == "copilot")
        self.assertIn("branding", copilot)

    def test_config_save_writes_normalized_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            raw = {"providers": [{"id": "copilot", "enabled": True, "source": "api", "apiKey": "gho_test"}]}
            encoded = base64.urlsafe_b64encode(json.dumps(raw).encode("utf-8")).decode("utf-8")

            with mock.patch("pathlib.Path.home", return_value=home):
                main(["config-save", encoded])
                config_file = home / ".config" / "ai-usage-monitor" / "config.json"
                self.assertTrue(config_file.exists())
                written = json.loads(config_file.read_text())
                provider_map = {entry["id"]: entry for entry in written["providers"]}
                self.assertEqual(provider_map["copilot"]["apiKey"], "gho_test")


if __name__ == "__main__":
    unittest.main()
