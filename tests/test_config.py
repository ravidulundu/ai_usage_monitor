import unittest

from core.ai_usage_monitor.config import normalize_config


class ConfigTests(unittest.TestCase):
    def test_normalize_config_appends_known_providers_and_respects_overrides(self):
        config = normalize_config(
            {
                "refreshInterval": 120,
                "providers": [
                    {"id": "claude", "enabled": False, "source": "auto"},
                    {
                        "id": "copilot",
                        "enabled": True,
                        "source": "api",
                        "apiKey": "gho_test",
                    },
                ],
            }
        )

        provider_map = {entry["id"]: entry for entry in config["providers"]}

        self.assertEqual(config["refreshInterval"], 120)
        self.assertFalse(provider_map["claude"]["enabled"])
        self.assertEqual(provider_map["copilot"]["apiKey"], "gho_test")
        self.assertEqual(provider_map["opencode"]["source"], "local_cli")
        self.assertNotIn("kimi", provider_map)
        self.assertNotIn("kiro", provider_map)
        self.assertNotIn("jetbrains", provider_map)

    def test_normalize_config_coerces_legacy_string_enabled_values(self):
        config = normalize_config(
            {
                "providers": [
                    {"id": "claude", "enabled": "false", "source": "auto"},
                    {"id": "codex", "enabled": "true", "source": "auto"},
                ],
            }
        )

        provider_map = {entry["id"]: entry for entry in config["providers"]}
        self.assertFalse(provider_map["claude"]["enabled"])
        self.assertTrue(provider_map["codex"]["enabled"])

    def test_normalize_config_limits_overview_provider_ids_to_three_known_unique(self):
        config = normalize_config(
            {
                "overviewProviderIds": [
                    "codex",
                    "claude",
                    "gemini",
                    "codex",
                    "unknown",
                    "copilot",
                ],
            }
        )

        self.assertEqual(config["overviewProviderIds"], ["codex", "claude", "gemini"])

    def test_normalize_config_keeps_local_cli_for_local_first_hybrid_provider(self):
        config = normalize_config(
            {
                "providers": [
                    {"id": "opencode", "enabled": True, "source": "local_cli"},
                ],
            }
        )

        provider_map = {entry["id"]: entry for entry in config["providers"]}
        self.assertEqual(provider_map["opencode"]["source"], "local_cli")


if __name__ == "__main__":
    unittest.main()
