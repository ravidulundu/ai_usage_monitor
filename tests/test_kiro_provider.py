import unittest
from unittest import mock
import subprocess

from core.ai_usage_monitor.archived_providers.kiro import (
    collect_kiro,
    parse_kiro_output,
)


class KiroProviderTests(unittest.TestCase):
    def test_parse_kiro_output_extracts_primary_and_bonus_usage(self):
        output = """
Plan: Kiro Pro
Monthly credits:
██████████████████████ 42% (resets on 01/15)
(21.00 of 50 covered in plan)
Bonus credits:
10.00/100 credits used, expires in 88 days
"""
        parsed = parse_kiro_output(output)

        self.assertEqual(parsed["plan_name"], "Kiro Pro")
        self.assertEqual(parsed["credits_percent"], 42.0)
        self.assertEqual(parsed["bonus_used"], 10.0)
        self.assertEqual(parsed["bonus_total"], 100.0)
        self.assertEqual(parsed["bonus_days"], 88)

    def test_collect_kiro_reports_not_installed_when_binary_missing(self):
        with mock.patch(
            "core.ai_usage_monitor.archived_providers.kiro.resolve_cli_binary",
            return_value=None,
        ):
            legacy, state = collect_kiro()
        self.assertFalse(legacy["installed"])
        self.assertFalse(state.installed)

    def test_collect_kiro_uses_resolved_binary_path(self):
        usage_output = """
Plan: Kiro Pro
Monthly credits:
██████████████████████ 42% (resets on 01/15)
(21.00 of 50 covered in plan)
"""
        whoami_result = subprocess.CompletedProcess(
            args=["/tmp/kiro-cli", "whoami"], returncode=0, stdout="ok", stderr=""
        )
        usage_result = subprocess.CompletedProcess(
            args=["/tmp/kiro-cli", "chat"], returncode=0, stdout=usage_output, stderr=""
        )
        with mock.patch(
            "core.ai_usage_monitor.archived_providers.kiro.resolve_cli_binary",
            return_value="/tmp/kiro-cli",
        ):
            with mock.patch(
                "core.ai_usage_monitor.archived_providers.kiro.subprocess.run",
                side_effect=[whoami_result, usage_result],
            ) as run_mock:
                legacy, state = collect_kiro()

        self.assertTrue(legacy["installed"])
        self.assertTrue(state.installed)
        self.assertEqual(run_mock.call_args_list[0].args[0][0], "/tmp/kiro-cli")
        self.assertEqual(run_mock.call_args_list[1].args[0][0], "/tmp/kiro-cli")


if __name__ == "__main__":
    unittest.main()
