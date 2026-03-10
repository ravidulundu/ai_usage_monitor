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

    def test_resolve_cli_binary_uses_login_shell_fallback(self):
        with mock.patch.dict("os.environ", {"SHELL": "/bin/zsh"}, clear=False):
            with mock.patch(
                "core.ai_usage_monitor.cli_detect.shutil.which", return_value=None
            ):
                with mock.patch(
                    "core.ai_usage_monitor.cli_detect._candidate_bin_dirs",
                    return_value=[],
                ):
                    with mock.patch(
                        "core.ai_usage_monitor.cli_detect._is_executable_file",
                        side_effect=lambda p: (
                            str(p) in {"/bin/zsh", "/opt/bin/opencode"}
                        ),
                    ):
                        completed = mock.Mock(stdout="/opt/bin/opencode\n")
                        with mock.patch(
                            "core.ai_usage_monitor.cli_detect.subprocess.run",
                            return_value=completed,
                        ) as run_mock:
                            resolved = resolve_cli_binary("opencode")

        self.assertEqual(resolved, "/opt/bin/opencode")
        run_mock.assert_called_once()

    def test_resolve_cli_binary_rejects_unsafe_binary_name_for_shell_fallback(self):
        with mock.patch(
            "core.ai_usage_monitor.cli_detect.shutil.which", return_value=None
        ):
            with mock.patch(
                "core.ai_usage_monitor.cli_detect._candidate_bin_dirs",
                return_value=[],
            ):
                with mock.patch(
                    "core.ai_usage_monitor.cli_detect.subprocess.run"
                ) as run_mock:
                    resolved = resolve_cli_binary("opencode; rm -rf /")

        self.assertIsNone(resolved)
        run_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
