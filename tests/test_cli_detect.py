import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from core.ai_usage_monitor.cli_detect import resolve_cli_binary


class CliDetectTests(unittest.TestCase):
    def test_resolve_cli_binary_uses_explicit_env_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            binary = Path(tmp) / "custom-opencode"
            binary.write_text("#!/bin/sh\nexit 0\n")
            binary.chmod(binary.stat().st_mode | stat.S_IXUSR)

            with mock.patch.dict(
                "os.environ",
                {"AI_USAGE_MONITOR_OPENCODE_BIN": str(binary)},
                clear=False,
            ):
                with mock.patch(
                    "core.ai_usage_monitor.cli_detect.shutil.which", return_value=None
                ):
                    resolved = resolve_cli_binary(
                        "opencode", env_var="AI_USAGE_MONITOR_OPENCODE_BIN"
                    )

        self.assertEqual(resolved, str(binary))

    def test_resolve_cli_binary_checks_user_bin_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            binary = home / ".local" / "bin" / "kiro-cli"
            binary.parent.mkdir(parents=True)
            binary.write_text("#!/bin/sh\nexit 0\n")
            binary.chmod(binary.stat().st_mode | stat.S_IXUSR)

            with mock.patch("pathlib.Path.home", return_value=home):
                with mock.patch(
                    "core.ai_usage_monitor.cli_detect.shutil.which", return_value=None
                ):
                    resolved = resolve_cli_binary("kiro-cli")

        self.assertEqual(resolved, str(binary))


if __name__ == "__main__":
    unittest.main()
