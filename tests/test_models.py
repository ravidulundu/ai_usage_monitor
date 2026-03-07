import unittest

from core.ai_usage_monitor.models import MetricWindow, ProviderState


class ProviderStateTests(unittest.TestCase):
    def test_provider_state_serializes_with_primary_and_secondary_metrics(self):
        state = ProviderState(
            id="codex",
            display_name="OpenAI Codex",
            enabled=True,
            installed=True,
            authenticated=True,
            status="ok",
            source="cli",
            primary_metric=MetricWindow(label="5h", used_pct=42, reset_at="2026-03-07T15:00:00Z"),
            secondary_metric=MetricWindow(label="7d", used_pct=61, reset_at="2026-03-10T00:00:00Z"),
        )

        data = state.to_dict()

        self.assertEqual(data["id"], "codex")
        self.assertEqual(data["primaryMetric"]["label"], "5h")
        self.assertEqual(data["secondaryMetric"]["label"], "7d")


if __name__ == "__main__":
    unittest.main()
