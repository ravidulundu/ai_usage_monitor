import unittest
import stat
from unittest import mock
from pathlib import Path
from tempfile import TemporaryDirectory

from core.ai_usage_monitor.providers.codex import (
    _codex_identity_state_path,
    _load_codex_identity_state,
    _save_codex_identity_state,
    _latest_token_count_snapshot,
    collect_codex,
    normalize_codex_rate_limits,
)


class CodexNormalizationTests(unittest.TestCase):
    def test_codex_normalization_returns_primary_and_secondary_windows(self):
        raw = {
            "rate_limits": {
                "primary": {"used_percent": 20, "resets_at": 1700000000},
                "secondary": {"used_percent": 55, "resets_at": 1700100000},
                "plan_type": "pro",
            }
        }

        state = normalize_codex_rate_limits(raw, model="gpt-5-codex")

        self.assertEqual(state.primary_metric.label, "5h")
        self.assertEqual(state.secondary_metric.label, "7d")
        self.assertEqual(state.source, "cli")

    def test_latest_token_count_snapshot_picks_newest_timestamp_across_files(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            older = root / "2026" / "03" / "06" / "a.jsonl"
            newer = root / "2026" / "03" / "07" / "b.jsonl"
            older.parent.mkdir(parents=True, exist_ok=True)
            newer.parent.mkdir(parents=True, exist_ok=True)

            older.write_text(
                "\n".join(
                    [
                        '{"type":"turn_context","payload":{"model":"gpt-5.4"}}',
                        '{"timestamp":"2026-03-07T05:40:00.000Z","type":"event_msg","payload":{"type":"token_count","rate_limits":{"primary":{"used_percent":72},"secondary":{"used_percent":39}}}}',
                    ]
                )
            )
            newer.write_text(
                "\n".join(
                    [
                        '{"type":"turn_context","payload":{"model":"gpt-5.4-high"}}',
                        '{"timestamp":"2026-03-07T05:41:00.000Z","type":"event_msg","payload":{"type":"token_count","rate_limits":{"primary":{"used_percent":80},"secondary":{"used_percent":41}}}}',
                    ]
                )
            )

            payload, model, _local_usage = _latest_token_count_snapshot(root)

        self.assertEqual(
            (payload.get("rate_limits") or {}).get("primary", {}).get("used_percent"),
            80,
        )
        self.assertEqual(
            (payload.get("rate_limits") or {}).get("secondary", {}).get("used_percent"),
            41,
        )
        self.assertEqual(model, "gpt-5.4-high")

    def test_latest_token_count_snapshot_respects_min_timestamp(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot_file = root / "2026" / "03" / "07" / "a.jsonl"
            snapshot_file.parent.mkdir(parents=True, exist_ok=True)
            snapshot_file.write_text(
                "\n".join(
                    [
                        '{"type":"turn_context","payload":{"model":"gpt-5.4"}}',
                        '{"timestamp":"2026-03-07T05:40:00.000Z","type":"event_msg","payload":{"type":"token_count","rate_limits":{"primary":{"used_percent":72},"secondary":{"used_percent":39}}}}',
                    ]
                )
            )

            payload, model, _local_usage = _latest_token_count_snapshot(
                root, min_timestamp="2026-03-07T05:41:00+00:00"
            )

        self.assertIsNone(payload)
        self.assertEqual(model, "")

    def test_latest_token_count_snapshot_uses_supplied_files_without_reglobbing(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot_file = root / "2026" / "03" / "07" / "a.jsonl"
            snapshot_file.parent.mkdir(parents=True, exist_ok=True)
            snapshot_file.write_text(
                "\n".join(
                    [
                        '{"type":"turn_context","payload":{"model":"gpt-5.4"}}',
                        '{"timestamp":"2026-03-07T05:40:00.000Z","type":"event_msg","payload":{"type":"token_count","rate_limits":{"primary":{"used_percent":72},"secondary":{"used_percent":39}}}}',
                    ]
                )
            )

            with mock.patch.object(
                Path, "rglob", side_effect=AssertionError("unexpected rglob")
            ):
                payload, model, _local_usage = _latest_token_count_snapshot(
                    root, files=[snapshot_file]
                )

        self.assertIsNotNone(payload)
        self.assertEqual(model, "gpt-5.4")

    def test_codex_normalization_tolerates_missing_rate_limits(self):
        state = normalize_codex_rate_limits({"rate_limits": None}, model="gpt-5-codex")

        self.assertIsNone(state.primary_metric)
        self.assertIsNone(state.secondary_metric)
        self.assertEqual(state.extras.get("model"), "gpt-5-codex")
        self.assertFalse(state.extras.get("hasRateLimits"))

    def test_collect_codex_invalidates_old_snapshot_after_account_switch(self):
        with TemporaryDirectory() as tmp:
            home = Path(tmp)
            sessions_file = (
                home / ".codex" / "sessions" / "2026" / "03" / "07" / "rollout.jsonl"
            )
            sessions_file.parent.mkdir(parents=True, exist_ok=True)
            sessions_file.write_text(
                "\n".join(
                    [
                        '{"type":"turn_context","payload":{"model":"gpt-5.4"}}',
                        '{"timestamp":"2026-03-07T05:40:00.000Z","type":"event_msg","payload":{"type":"token_count","rate_limits":{"primary":{"used_percent":72,"resets_at":1700000000},"secondary":{"used_percent":39,"resets_at":1700100000}}}}',
                    ]
                )
            )

            auth_file = home / ".codex" / "auth.json"
            auth_file.parent.mkdir(parents=True, exist_ok=True)
            auth_file.write_text(
                '{"auth_mode":"chatgpt","tokens":{"account_id":"new-account","access_token":"x","refresh_token":"y","id_token":"z"}}'
            )

            identity_state = (
                home / ".cache" / "ai-usage-monitor" / "codex_identity_state.json"
            )
            identity_state.parent.mkdir(parents=True, exist_ok=True)
            identity_state.write_text(
                '{"version":1,"accountId":"old-account","switchDetectedAt":"2026-03-07T05:41:00+00:00"}'
            )

            with mock.patch("pathlib.Path.home", return_value=home):
                with mock.patch(
                    "core.ai_usage_monitor.providers.codex.fetch_statuspage",
                    return_value=None,
                ):
                    legacy, state = collect_codex()

        self.assertTrue(legacy.get("installed"))
        self.assertFalse(legacy.get("has_data"))
        self.assertTrue(state.installed)
        self.assertEqual(state.extras.get("accountId"), "new-account")
        self.assertFalse(state.extras.get("hasData", True))

    def test_codex_identity_state_respects_runtime_state_dir_and_permissions(self):
        with TemporaryDirectory() as tmp:
            with mock.patch.dict(
                "os.environ", {"AI_USAGE_MONITOR_STATE_DIR": tmp}, clear=False
            ):
                _save_codex_identity_state(
                    identity_key="account-1",
                    account_id="account-1",
                    switch_detected_at="2026-03-09T00:00:00+00:00",
                )
                path = _codex_identity_state_path()
                payload = _load_codex_identity_state()
                self.assertEqual(path, Path(tmp) / "codex_identity_state.json")
                self.assertTrue(path.exists())
                self.assertEqual(payload.get("identityKey"), "account-1")
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)


if __name__ == "__main__":
    unittest.main()
