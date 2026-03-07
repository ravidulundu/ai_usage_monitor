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
        payload = AppState(providers=[ProviderState(id="codex", display_name="OpenAI Codex")]).to_dict()

        self.assertEqual(payload["version"], 1)
        self.assertIn("updatedAt", payload)
        self.assertEqual(payload["providers"][0]["id"], "codex")

    def test_registry_descriptor_payload_includes_short_names(self):
        payload = ProviderRegistry().descriptor_payload()
        by_id = {entry["id"]: entry for entry in payload}

        self.assertEqual(by_id["codex"]["shortName"], "Codex")
        self.assertEqual(by_id["copilot"]["shortName"], "Copilot")
        self.assertNotIn("kimik2", by_id)


if __name__ == "__main__":
    unittest.main()
