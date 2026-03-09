import unittest
from unittest import mock

from core.ai_usage_monitor.models import LocalUsageSnapshot
from core.ai_usage_monitor.providers.vertexai import (
    _compute_highest_usage_percent,
    collect_vertexai,
)


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

    def test_collect_vertexai_returns_error_state_when_project_missing(self):
        with mock.patch(
            "core.ai_usage_monitor.providers.vertexai._load_adc",
            return_value={"access_token": "tok"},
        ):
            with mock.patch(
                "core.ai_usage_monitor.providers.vertexai._project_id_from_sources",
                return_value=None,
            ):
                with mock.patch(
                    "core.ai_usage_monitor.providers.vertexai.scan_vertex_local_usage",
                    return_value=LocalUsageSnapshot(
                        session_tokens=7, last_30_days_tokens=7
                    ),
                ):
                    legacy, state = collect_vertexai()

        self.assertTrue(legacy["installed"])
        self.assertEqual(legacy["fail_reason"], "invalid_credentials")
        self.assertEqual(state.status, "error")
        self.assertFalse(state.authenticated)
        self.assertEqual(state.error, "No Google Cloud project configured.")
        self.assertEqual(state.local_usage.session_tokens, 7)

    def test_collect_vertexai_maps_successful_quota_payload(self):
        with mock.patch(
            "core.ai_usage_monitor.providers.vertexai._load_adc",
            return_value={"access_token": "tok"},
        ):
            with mock.patch(
                "core.ai_usage_monitor.providers.vertexai._project_id_from_sources",
                return_value="demo-project",
            ):
                with mock.patch(
                    "core.ai_usage_monitor.providers.vertexai._access_token_from_adc",
                    return_value="access-token",
                ):
                    with mock.patch(
                        "core.ai_usage_monitor.providers.vertexai._fetch_timeseries",
                        side_effect=[
                            {
                                "timeSeries": [
                                    {
                                        "metric": {
                                            "labels": {
                                                "quota_metric": "a",
                                                "limit_name": "b",
                                            }
                                        },
                                        "resource": {"labels": {"location": "global"}},
                                        "points": [{"value": {"doubleValue": 25}}],
                                    }
                                ]
                            },
                            {
                                "timeSeries": [
                                    {
                                        "metric": {
                                            "labels": {
                                                "quota_metric": "a",
                                                "limit_name": "b",
                                            }
                                        },
                                        "resource": {"labels": {"location": "global"}},
                                        "points": [{"value": {"doubleValue": 100}}],
                                    }
                                ]
                            },
                        ],
                    ):
                        with mock.patch(
                            "core.ai_usage_monitor.providers.vertexai.scan_vertex_local_usage",
                            return_value=LocalUsageSnapshot(
                                session_tokens=10, last_30_days_tokens=30
                            ),
                        ):
                            legacy, state = collect_vertexai()

        self.assertEqual(legacy["project_id"], "demo-project")
        self.assertEqual(legacy["account_id"], "demo-project")
        self.assertEqual(legacy["used_pct"], 25)
        self.assertTrue(state.authenticated)
        self.assertEqual(state.primary_metric.used_pct, 25.0)
        self.assertEqual(state.extras["projectId"], "demo-project")
        self.assertEqual(state.local_usage.last_30_days_tokens, 30)


if __name__ == "__main__":
    unittest.main()
