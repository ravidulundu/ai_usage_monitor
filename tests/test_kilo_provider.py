import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from core.ai_usage_monitor.providers.kilo import (
    _cli_token,
    collect_kilo,
    parse_kilo_snapshot,
)


class KiloProviderTests(unittest.TestCase):
    def test_cli_token_reads_auth_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            auth_file = home / ".local" / "share" / "kilo" / "auth.json"
            auth_file.parent.mkdir(parents=True)
            auth_file.write_text(json.dumps({"kilo": {"access": "kilo_token"}}))

            with mock.patch("pathlib.Path.home", return_value=home):
                self.assertEqual(_cli_token(), "kilo_token")

    def test_parse_kilo_snapshot_extracts_credit_and_pass_fields(self):
        payload = [
            {
                "result": {
                    "data": {
                        "json": {
                            "creditBlocks": [
                                {"amount_mUsd": 100000000, "balance_mUsd": 40000000}
                            ]
                        }
                    }
                }
            },
            {
                "result": {
                    "data": {
                        "json": {
                            "subscription": {
                                "tier": "tier_49",
                                "currentPeriodUsageUsd": 12,
                                "currentPeriodBaseCreditsUsd": 20,
                                "currentPeriodBonusCreditsUsd": 5,
                                "nextBillingAt": "2026-04-01T00:00:00Z",
                            }
                        }
                    }
                }
            },
            {"result": {"data": {"json": {"enabled": True, "paymentMethod": "visa"}}}},
        ]

        parsed = parse_kilo_snapshot(json.dumps(payload).encode())

        self.assertEqual(parsed["credits_total"], 100.0)
        self.assertEqual(parsed["credits_remaining"], 40.0)
        self.assertEqual(parsed["plan_name"], "Pro")
        self.assertEqual(parsed["pass_total"], 25.0)
        self.assertEqual(parsed["auto_top_up_method"], "visa")

    def test_collect_kilo_returns_not_installed_when_no_credentials_exist(self):
        with mock.patch(
            "core.ai_usage_monitor.providers.kilo._api_key", return_value=None
        ):
            with mock.patch(
                "core.ai_usage_monitor.providers.kilo._cli_token", return_value=None
            ):
                legacy, state = collect_kilo({"source": "auto"})

        self.assertEqual(legacy, {"installed": False})
        self.assertFalse(state.installed)
        self.assertEqual(state.source, "auto")


if __name__ == "__main__":
    unittest.main()
