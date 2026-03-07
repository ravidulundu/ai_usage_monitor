import unittest

from core.ai_usage_monitor.providers.amp import parse_amp_html


class AmpProviderTests(unittest.TestCase):
    def test_parse_amp_html_extracts_free_tier_usage(self):
        html = """
<script>
const freeTierUsage = {"quota": 50, "used": 12.5, "hourlyReplenishment": 2.5, "windowHours": 24};
</script>
"""
        parsed = parse_amp_html(html)

        self.assertEqual(parsed["quota"], 50.0)
        self.assertEqual(parsed["used"], 12.5)
        self.assertEqual(parsed["hourly_replenishment"], 2.5)
        self.assertEqual(parsed["window_hours"], 24.0)


if __name__ == "__main__":
    unittest.main()
