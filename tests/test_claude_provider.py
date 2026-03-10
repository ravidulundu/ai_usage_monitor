import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from core.ai_usage_monitor.models import LocalUsageSnapshot
from core.ai_usage_monitor.providers.claude import collect_claude


class ClaudeProviderTests(unittest.TestCase):
    def test_collect_claude_returns_not_installed_when_credentials_missing(self):
        with TemporaryDirectory() as tmp:
            with mock.patch("pathlib.Path.home", return_value=Path(tmp)):
                legacy, state = collect_claude()

        self.assertEqual(legacy, {"installed": False})
        self.assertFalse(state.installed)
        self.assertEqual(state.source, "oauth")

    def test_collect_claude_maps_usage_identity_and_incident(self):
        with TemporaryDirectory() as tmp:
            home = Path(tmp)
            creds_path = home / ".claude" / ".credentials.json"
            creds_path.parent.mkdir(parents=True, exist_ok=True)
            creds_path.write_text(
                json.dumps(
                    {
                        "claudeAiOauth": {
                            "accessToken": "token-123",
                            "accountId": "acc-1",
                            "user": {"email": "dev@example.com"},
                        }
                    }
                )
            )

            response = mock.MagicMock()
            response.read.return_value = json.dumps(
                {
                    "five_hour": {
                        "utilization": 22,
                        "resets_at": "2026-03-09T12:00:00Z",
                    },
                    "seven_day": {
                        "utilization": 61,
                        "resets_at": "2026-03-10T00:00:00Z",
                    },
                }
            ).encode("utf-8")
            response.__enter__.return_value = response
            response.__exit__.return_value = None

            with mock.patch("pathlib.Path.home", return_value=home):
                with mock.patch(
                    "core.ai_usage_monitor.providers.claude.urllib.request.urlopen",
                    return_value=response,
                ):
                    with mock.patch(
                        "core.ai_usage_monitor.providers.claude.scan_claude_local_usage",
                        return_value=LocalUsageSnapshot(
                            session_tokens=12, last_30_days_tokens=34
                        ),
                    ):
                        with mock.patch(
                            "core.ai_usage_monitor.providers.claude.fetch_statuspage",
                            return_value={"indicator": "none"},
                        ):
                            legacy, state = collect_claude()

        self.assertTrue(legacy["installed"])
        self.assertEqual(legacy["five_hour_pct"], 22)
        self.assertEqual(legacy["seven_day_pct"], 61)
        self.assertTrue(state.authenticated)
        self.assertEqual(state.primary_metric.used_pct, 22)
        self.assertEqual(state.secondary_metric.used_pct, 61)
        self.assertEqual(state.extras["accountId"], "acc-1")
        self.assertEqual(state.extras["email"], "dev@example.com")
        self.assertEqual(state.incident["indicator"], "none")
        self.assertEqual(state.local_usage.last_30_days_tokens, 34)


if __name__ == "__main__":
    unittest.main()
