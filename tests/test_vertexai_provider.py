import unittest

from core.ai_usage_monitor.providers.vertexai import _compute_highest_usage_percent


class VertexAIProviderTests(unittest.TestCase):
    def test_compute_highest_usage_percent_matches_usage_and_limit_series(self):
        usage_payload = {
            "timeSeries": [
                {
                    "metric": {"labels": {"quota_metric": "a", "limit_name": "b"}},
                    "resource": {"labels": {"location": "global"}},
                    "points": [{"value": {"doubleValue": 20}}],
                }
            ]
        }
        limit_payload = {
            "timeSeries": [
                {
                    "metric": {"labels": {"quota_metric": "a", "limit_name": "b"}},
                    "resource": {"labels": {"location": "global"}},
                    "points": [{"value": {"doubleValue": 100}}],
                }
            ]
        }

        pct = _compute_highest_usage_percent(usage_payload, limit_payload)

        self.assertEqual(pct, 20.0)


if __name__ == "__main__":
    unittest.main()
