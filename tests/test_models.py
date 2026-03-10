import unittest

from core.ai_usage_monitor.models import LocalUsageSnapshot, MetricWindow, ProviderState


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
            primary_metric=MetricWindow(
                label="5h", used_pct=42, reset_at="2026-03-07T15:00:00Z"
            ),
            secondary_metric=MetricWindow(
                label="7d", used_pct=61, reset_at="2026-03-10T00:00:00Z"
            ),
        )

        data = state.to_dict()

        self.assertEqual(data["id"], "codex")
        self.assertEqual(data["primaryMetric"]["label"], "5h")
        self.assertEqual(data["secondaryMetric"]["label"], "7d")

    def test_provider_state_roundtrips_from_dict(self):
        state = ProviderState(
            id="claude",
            display_name="Claude",
            installed=True,
            source="oauth",
            primary_metric=MetricWindow("5h", 20, "2026-03-08T00:00:00Z"),
            local_usage=LocalUsageSnapshot(session_tokens=12, last_30_days_tokens=34),
            extras={"accountId": "acc-1"},
        )

        restored = ProviderState.from_dict(state.to_dict())

        self.assertEqual(restored.id, "claude")
        self.assertIsNotNone(restored.primary_metric)
        self.assertEqual(restored.primary_metric.used_pct, 20.0)
        self.assertIsNotNone(restored.local_usage)
        self.assertEqual(restored.local_usage.session_tokens, 12)


if __name__ == "__main__":
    unittest.main()
