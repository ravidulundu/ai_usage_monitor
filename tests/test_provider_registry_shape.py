import unittest

from core.ai_usage_monitor.models import AppState, ProviderState
from core.ai_usage_monitor.providers.registry import ProviderRegistry


class CollectorShapeTests(unittest.TestCase):
    def test_registry_returns_known_provider_ids(self):
        registry = ProviderRegistry()

        self.assertIn("amp", registry.list_ids())
        self.assertIn("claude", registry.list_ids())
        self.assertIn("codex", registry.list_ids())
        self.assertIn("gemini", registry.list_ids())
        self.assertIn("copilot", registry.list_ids())
        self.assertIn("vertexai", registry.list_ids())
        self.assertIn("openrouter", registry.list_ids())
        self.assertIn("zai", registry.list_ids())
        self.assertIn("kilo", registry.list_ids())
        self.assertIn("ollama", registry.list_ids())
        self.assertIn("opencode", registry.list_ids())
        self.assertIn("minimax", registry.list_ids())

    def test_app_state_serializes_top_level_fields(self):
        payload = AppState(
            providers=[ProviderState(id="codex", display_name="OpenAI Codex")]
        ).to_dict()

        self.assertEqual(payload["version"], 1)
        self.assertIn("updatedAt", payload)
        self.assertEqual(payload["providers"][0]["id"], "codex")

    def test_registry_descriptor_payload_includes_short_names(self):
        payload = ProviderRegistry().descriptor_payload()
        by_id = {entry["id"]: entry for entry in payload}

        self.assertEqual(by_id["codex"]["shortName"], "Codex")
        self.assertEqual(by_id["copilot"]["shortName"], "Copilot")
        self.assertNotIn("jetbrains", by_id)
        self.assertNotIn("kiro", by_id)
        self.assertNotIn("kimik2", by_id)
        self.assertNotIn("warp", by_id)

    def test_registry_descriptor_payload_derives_capabilities_for_auto_modes(self):
        payload = ProviderRegistry().descriptor_payload()
        by_id = {entry["id"]: entry for entry in payload}

        codex_caps = by_id["codex"]["providerCapabilities"]
        claude_caps = by_id["claude"]["providerCapabilities"]
        gemini_caps = by_id["gemini"]["providerCapabilities"]

        self.assertTrue(codex_caps["supportsLocalCli"])
        self.assertTrue(codex_caps["supportsApi"])
        self.assertFalse(codex_caps["supportsWeb"])

        self.assertTrue(claude_caps["supportsLocalCli"])
        self.assertTrue(claude_caps["supportsApi"])
        self.assertFalse(claude_caps["supportsWeb"])

        self.assertFalse(gemini_caps["supportsLocalCli"])
        self.assertTrue(gemini_caps["supportsApi"])
        self.assertFalse(gemini_caps["supportsWeb"])

    def test_registry_descriptor_payload_keeps_ollama_web_only_capability(self):
        payload = ProviderRegistry().descriptor_payload()
        by_id = {entry["id"]: entry for entry in payload}
        ollama_caps = by_id["ollama"]["providerCapabilities"]

        self.assertFalse(ollama_caps["supportsLocalCli"])
        self.assertFalse(ollama_caps["supportsApi"])
        self.assertTrue(ollama_caps["supportsWeb"])


if __name__ == "__main__":
    unittest.main()
