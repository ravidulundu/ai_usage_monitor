import unittest

from core.ai_usage_monitor.providers.copilot import _make_metric


class CopilotProviderTests(unittest.TestCase):
    def test_make_metric_maps_percent_remaining_to_used_percent(self):
        metric = _make_metric({"percentRemaining": 73}, "Premium")

        self.assertIsNotNone(metric)
        self.assertEqual(metric.label, "Premium")
        self.assertEqual(metric.used_pct, 27)


if __name__ == "__main__":
    unittest.main()
