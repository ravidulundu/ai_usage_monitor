import unittest

from core.ai_usage_monitor.providers.opencode import normalize_workspace_id, parse_subscription_text


class OpenCodeProviderTests(unittest.TestCase):
    def test_normalize_workspace_id_accepts_raw_and_url(self):
        self.assertEqual(normalize_workspace_id("wrk_abc123"), "wrk_abc123")
        self.assertEqual(
            normalize_workspace_id("https://opencode.ai/workspace/wrk_abc123/billing"),
            "wrk_abc123",
        )

    def test_parse_subscription_text_extracts_usage_windows(self):
        text = """
        {
          "rollingUsage": {"usagePercent": 42, "resetInSec": 1800},
          "weeklyUsage": {"usagePercent": 61, "resetInSec": 7200}
        }
        """
        parsed = parse_subscription_text(text)

        self.assertEqual(parsed["rolling_pct"], 42.0)
        self.assertEqual(parsed["weekly_pct"], 61.0)


if __name__ == "__main__":
    unittest.main()
