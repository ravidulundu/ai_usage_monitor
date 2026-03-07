import unittest

from core.ai_usage_monitor.config import normalize_config


class ConfigTests(unittest.TestCase):
    def test_normalize_config_appends_known_providers_and_respects_overrides(self):
        config = normalize_config(
            {
                "refreshInterval": 120,
                "providers": [
                    {"id": "claude", "enabled": False, "source": "auto"},
                    {"id": "copilot", "enabled": True, "source": "api", "apiKey": "gho_test"},
                ],
            }
        )

        provider_map = {entry["id"]: entry for entry in config["providers"]}

        self.assertEqual(config["refreshInterval"], 120)
        self.assertFalse(provider_map["claude"]["enabled"])
        self.assertEqual(provider_map["copilot"]["apiKey"], "gho_test")
        self.assertEqual(provider_map["opencode"]["source"], "auto")
        self.assertNotIn("kimi", provider_map)
        self.assertNotIn("kiro", provider_map)
        self.assertNotIn("jetbrains", provider_map)


if __name__ == "__main__":
    unittest.main()
