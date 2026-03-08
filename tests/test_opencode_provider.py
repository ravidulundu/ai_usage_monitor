import json
import stat
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from core.ai_usage_monitor.providers.opencode import (
    _has_local_opencode_install,
    _local_auth_type,
    collect_opencode,
    normalize_workspace_id,
    parse_subscription_text,
)


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

    def test_collect_opencode_uses_local_cli_mode_when_install_detected(self):
        with mock.patch(
            "core.ai_usage_monitor.providers.opencode._has_local_opencode_install",
            return_value=True,
        ):
            with mock.patch(
                "core.ai_usage_monitor.providers.opencode.scan_opencode_local_usage"
            ) as usage_mock:
                usage_mock.return_value = mock.Mock(
                    session_tokens=1234, last_30_days_tokens=5678
                )
                with mock.patch(
                    "core.ai_usage_monitor.providers.opencode._local_auth_type",
                    return_value="api",
                ):
                    legacy, state = collect_opencode({"source": "auto"})

        self.assertTrue(legacy["installed"])
        self.assertEqual(legacy["auth_type"], "api")
        self.assertTrue(state.installed)
        self.assertEqual(state.source, "cli")
        self.assertIsNone(state.error)
        self.assertEqual(state.extras["plan"], "api")

    def test_collect_opencode_auto_prefers_web_quota_when_cookie_available(self):
        with mock.patch(
            "core.ai_usage_monitor.providers.opencode._cookie_header",
            return_value=("auth=1", "manual"),
        ):
            with mock.patch(
                "core.ai_usage_monitor.providers.opencode._fetch_server_text"
            ) as fetch_mock:
                fetch_mock.side_effect = [
                    '{"id":"wrk_abc123"}',
                    '{"rollingUsage":{"usagePercent":42,"resetInSec":1800},"weeklyUsage":{"usagePercent":61,"resetInSec":7200}}',
                ]
                with mock.patch(
                    "core.ai_usage_monitor.providers.opencode._has_local_opencode_install",
                    return_value=True,
                ):
                    with mock.patch(
                        "core.ai_usage_monitor.providers.opencode.scan_opencode_local_usage"
                    ) as usage_mock:
                        usage_mock.return_value = mock.Mock(
                            session_tokens=1234, last_30_days_tokens=5678
                        )
                        legacy, state = collect_opencode({"source": "auto"})

        self.assertEqual(legacy["rolling_used_pct"], 42)
        self.assertEqual(state.source, "web")
        self.assertIsNotNone(state.primary_metric)
        self.assertIsNotNone(state.secondary_metric)

    def test_local_auth_type_reads_opencode_auth_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            auth_file = home / ".local" / "share" / "opencode" / "auth.json"
            auth_file.parent.mkdir(parents=True)
            auth_file.write_text(
                json.dumps({"opencode": {"type": "api", "key": "test"}})
            )

            with mock.patch("pathlib.Path.home", return_value=home):
                self.assertEqual(_local_auth_type(), "api")

    def test_local_auth_type_reads_opencode_auth_file_from_config_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            auth_file = home / ".config" / "opencode" / "auth.json"
            auth_file.parent.mkdir(parents=True)
            auth_file.write_text(json.dumps({"type": "oauth"}))

            with mock.patch("pathlib.Path.home", return_value=home):
                self.assertEqual(_local_auth_type(), "oauth")

    def test_has_local_opencode_install_detects_user_bin_without_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            binary = home / ".local" / "bin" / "opencode"
            binary.parent.mkdir(parents=True)
            binary.write_text("#!/bin/sh\nexit 0\n")
            binary.chmod(binary.stat().st_mode | stat.S_IXUSR)

            with mock.patch("pathlib.Path.home", return_value=home):
                with mock.patch(
                    "core.ai_usage_monitor.cli_detect.shutil.which", return_value=None
                ):
                    self.assertTrue(_has_local_opencode_install())


if __name__ == "__main__":
    unittest.main()
