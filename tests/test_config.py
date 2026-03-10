import unittest
import tempfile
import stat
from pathlib import Path
from unittest import mock

from core.ai_usage_monitor.config import (
    config_contains_sensitive_fields,
    save_config,
    normalize_config,
    sanitize_config_for_ui,
)


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
        self.assertEqual(provider_map["opencode"]["source"], "auto")
        self.assertNotIn("kimi", provider_map)
        self.assertNotIn("kiro", provider_map)
        self.assertNotIn("jetbrains", provider_map)
        self.assertNotIn("kimik2", provider_map)
        self.assertNotIn("warp", provider_map)

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

    def test_normalize_config_defaults_hybrid_provider_to_auto(self):
        config = normalize_config({"providers": [{"id": "opencode", "enabled": True}]})
        provider_map = {entry["id"]: entry for entry in config["providers"]}
        self.assertEqual(provider_map["opencode"]["source"], "auto")

    def test_normalize_config_keeps_explicit_opencode_web_source(self):
        config = normalize_config(
            {
                "providers": [
                    {"id": "opencode", "enabled": True, "source": "web"},
                ],
            }
        )
        provider_map = {entry["id"]: entry for entry in config["providers"]}
        self.assertEqual(provider_map["opencode"]["source"], "web")

    def test_normalize_config_maps_legacy_remote_source_to_web(self):
        config = normalize_config(
            {
                "providers": [
                    {"id": "ollama", "enabled": True, "source": "remote"},
                ],
            }
        )

        provider_map = {entry["id"]: entry for entry in config["providers"]}
        self.assertEqual(provider_map["ollama"]["source"], "web")

    def test_normalize_config_adds_default_polling_cache_seconds(self):
        config = normalize_config({})

        self.assertEqual(config["pollingCacheSeconds"], 10)

    def test_normalize_config_clamps_polling_cache_seconds(self):
        config = normalize_config({"pollingCacheSeconds": 120})
        zeroed = normalize_config({"pollingCacheSeconds": -5})

        self.assertEqual(config["pollingCacheSeconds"], 60)
        self.assertEqual(zeroed["pollingCacheSeconds"], 0)

    def test_normalize_config_defaults_expensive_niche_providers_to_disabled(self):
        config = normalize_config({})
        provider_map = {entry["id"]: entry for entry in config["providers"]}

        self.assertFalse(provider_map["vertexai"]["enabled"])
        self.assertFalse(provider_map["openrouter"]["enabled"])
        self.assertFalse(provider_map["ollama"]["enabled"])
        self.assertFalse(provider_map["amp"]["enabled"])

    def test_normalize_config_drops_unknown_provider_fields(self):
        config = normalize_config(
            {
                "providers": [
                    {
                        "id": "copilot",
                        "enabled": True,
                        "source": "api",
                        "unexpected": {"nested": 1},
                    }
                ]
            }
        )
        provider_map = {entry["id"]: entry for entry in config["providers"]}
        self.assertNotIn("unexpected", provider_map["copilot"])

    def test_sanitize_config_for_ui_hides_secret_provider_fields(self):
        config = sanitize_config_for_ui(
            {
                "providers": [
                    {
                        "id": "copilot",
                        "enabled": True,
                        "source": "api",
                        "apiKey": "gho_test",
                    }
                ]
            }
        )
        provider_map = {entry["id"]: entry for entry in config["providers"]}
        self.assertNotIn("apiKey", provider_map["copilot"])

    def test_config_contains_sensitive_fields_allows_non_secret_cookie_source(self):
        config = {
            "providers": [
                {
                    "id": "opencode",
                    "enabled": True,
                    "source": "auto",
                    "cookieSource": "off",
                }
            ]
        }
        self.assertFalse(config_contains_sensitive_fields(config))

    def test_save_config_writes_atomic_file_with_private_permissions(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            with mock.patch("pathlib.Path.home", return_value=home):
                saved = save_config({"providers": [{"id": "codex", "enabled": True}]})
                config_file = home / ".config" / "ai-usage-monitor" / "config.json"
                self.assertTrue(config_file.exists())
                self.assertEqual(saved["version"], 1)
                self.assertEqual(stat.S_IMODE(config_file.stat().st_mode), 0o600)


if __name__ == "__main__":
    unittest.main()
