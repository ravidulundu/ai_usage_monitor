import os
import tempfile
import unittest
from unittest import mock

from core.ai_usage_monitor.status import fetch_google_workspace_status, fetch_statuspage


class StatusTests(unittest.TestCase):
    def test_fetch_statuspage_reuses_ttl_cache(self):
        payload = {
            "status": {"indicator": "none", "description": "All Systems Operational"},
            "page": {"updated_at": "2026-03-08T00:00:00Z"},
        }
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(
                os.environ, {"AI_USAGE_MONITOR_STATE_DIR": tmp}, clear=False
            ):
                with mock.patch(
                    "core.ai_usage_monitor.status._read_json_uncached",
                    return_value=payload,
                ) as read_mock:
                    first = fetch_statuspage("https://status.openai.com")
                    second = fetch_statuspage("https://status.openai.com")

        self.assertEqual(first, second)
        self.assertEqual(read_mock.call_count, 1)

    def test_fetch_google_workspace_status_reuses_ttl_cache(self):
        payload = [
            {
                "currently_affected_products": [{"id": "gmail"}],
                "most_recent_update": {
                    "status": "SERVICE_INFORMATION",
                    "text": "Summary\\nMail delivery delayed",
                    "when": "2026-03-08T00:00:00Z",
                },
            }
        ]
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(
                os.environ, {"AI_USAGE_MONITOR_STATE_DIR": tmp}, clear=False
            ):
                with mock.patch(
                    "core.ai_usage_monitor.status._read_json_uncached",
                    return_value=payload,
                ) as read_mock:
                    first = fetch_google_workspace_status("gmail")
                    second = fetch_google_workspace_status("gmail")

        self.assertEqual(first, second)
        self.assertEqual(read_mock.call_count, 1)

    def test_fetch_statuspage_returns_none_for_malformed_payload(self):
        with mock.patch(
            "core.ai_usage_monitor.status._read_json",
            return_value=["not-a-dict"],
        ):
            status = fetch_statuspage("https://status.openai.com")
        self.assertIsNone(status)

    def test_fetch_google_workspace_status_ignores_non_dict_incidents(self):
        payload = [
            "bad",
            {
                "currently_affected_products": [{"id": "gmail"}],
                "most_recent_update": {},
            },
        ]
        with mock.patch(
            "core.ai_usage_monitor.status._read_json", return_value=payload
        ):
            status = fetch_google_workspace_status("gmail")
        self.assertIsInstance(status, dict)

    def test_fetch_statuspage_uses_failure_backoff_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(
                os.environ, {"AI_USAGE_MONITOR_STATE_DIR": tmp}, clear=False
            ):
                with mock.patch(
                    "core.ai_usage_monitor.status._read_json_uncached",
                    side_effect=RuntimeError("network down"),
                ) as read_mock:
                    first = fetch_statuspage("https://status.openai.com")
                    second = fetch_statuspage("https://status.openai.com")

        self.assertIsNone(first)
        self.assertIsNone(second)
        self.assertEqual(read_mock.call_count, 1)

    def test_fetch_google_workspace_status_handles_mixed_datetime_formats(self):
        payload = [
            {
                "currently_affected_products": [{"id": "gmail"}],
                "most_recent_update": {
                    "status": "SERVICE_INFORMATION",
                    "text": "Summary\\nAware time update",
                    "when": "2026-03-08T00:10:00Z",
                },
            },
            {
                "currently_affected_products": [{"id": "gmail"}],
                "most_recent_update": {
                    "status": "SERVICE_INFORMATION",
                    "text": "Summary\\nNaive time update",
                    "when": "2026-03-08T00:05:00",
                },
            },
        ]
        with mock.patch(
            "core.ai_usage_monitor.status._read_json",
            return_value=payload,
        ):
            status = fetch_google_workspace_status("gmail")
        self.assertIsInstance(status, dict)


if __name__ == "__main__":
    unittest.main()
