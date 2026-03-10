import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from core.ai_usage_monitor.local_usage import (
    scan_claude_local_usage,
    scan_codex_local_usage,
    scan_opencode_local_usage,
    scan_vertex_local_usage,
)


class LocalUsageTests(unittest.TestCase):
    def test_scan_codex_local_usage_aggregates_latest_and_rolling_tokens(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / ".codex" / "sessions" / "2026" / "03" / "07"
            root.mkdir(parents=True)
            file_path = root / "session.jsonl"
            rows = [
                {
                    "timestamp": "2026-03-07T01:00:00Z",
                    "type": "event_msg",
                    "payload": {
                        "type": "token_count",
                        "info": {"total_token_usage": {"total_tokens": 100}},
                    },
                },
                {
                    "timestamp": "2026-03-07T02:00:00Z",
                    "type": "event_msg",
                    "payload": {
                        "type": "token_count",
                        "info": {"total_token_usage": {"total_tokens": 150}},
                    },
                },
            ]
            file_path.write_text("\n".join(json.dumps(row) for row in rows))

            with mock.patch("pathlib.Path.home", return_value=Path(tmp)):
                snapshot = scan_codex_local_usage()

            self.assertIsNotNone(snapshot)
            self.assertEqual(snapshot.session_tokens, 150)
            self.assertEqual(snapshot.last_30_days_tokens, 150)

    def test_scan_codex_local_usage_uses_supplied_files_without_reglobbing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / ".codex" / "sessions" / "2026" / "03" / "07"
            root.mkdir(parents=True)
            file_path = root / "session.jsonl"
            file_path.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "timestamp": "2026-03-07T01:00:00Z",
                                "type": "event_msg",
                                "payload": {
                                    "type": "token_count",
                                    "info": {
                                        "total_token_usage": {"total_tokens": 100}
                                    },
                                },
                            }
                        )
                    ]
                )
            )

            with mock.patch("pathlib.Path.home", return_value=Path(tmp)):
                with mock.patch(
                    "core.ai_usage_monitor.local_usage._iter_files",
                    side_effect=AssertionError("unexpected _iter_files call"),
                ):
                    snapshot = scan_codex_local_usage(files=[file_path])

            self.assertIsNotNone(snapshot)
            self.assertEqual(snapshot.session_tokens, 100)
            self.assertEqual(snapshot.last_30_days_tokens, 100)

    def test_scan_claude_local_usage_aggregates_message_usage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / ".claude" / "projects"
            root.mkdir(parents=True)
            file_path = root / "session.jsonl"
            rows = [
                {
                    "timestamp": "2026-03-07T01:00:00Z",
                    "message": {
                        "usage": {
                            "input_tokens": 10,
                            "cache_read_input_tokens": 5,
                            "cache_creation_input_tokens": 0,
                            "output_tokens": 3,
                        }
                    },
                },
                {
                    "timestamp": "2026-03-07T02:00:00Z",
                    "message": {
                        "usage": {
                            "input_tokens": 20,
                            "cache_read_input_tokens": 0,
                            "cache_creation_input_tokens": 2,
                            "output_tokens": 4,
                        }
                    },
                },
            ]
            file_path.write_text("\n".join(json.dumps(row) for row in rows))

            with mock.patch("pathlib.Path.home", return_value=Path(tmp)):
                snapshot = scan_claude_local_usage()

            self.assertIsNotNone(snapshot)
            self.assertEqual(snapshot.session_tokens, 44)
            self.assertEqual(snapshot.last_30_days_tokens, 44)

    def test_scan_claude_local_usage_tolerates_malformed_token_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / ".claude" / "projects"
            root.mkdir(parents=True)
            file_path = root / "session.jsonl"
            rows = [
                {
                    "timestamp": "2026-03-07T01:00:00Z",
                    "message": {
                        "usage": {
                            "input_tokens": "not-a-number",
                            "cache_read_input_tokens": 5,
                            "cache_creation_input_tokens": None,
                            "output_tokens": "7",
                        }
                    },
                }
            ]
            file_path.write_text("\n".join(json.dumps(row) for row in rows))

            with mock.patch("pathlib.Path.home", return_value=Path(tmp)):
                snapshot = scan_claude_local_usage()

            self.assertIsNotNone(snapshot)
            self.assertEqual(snapshot.session_tokens, 12)

    def test_scan_claude_local_usage_reuses_cached_snapshot_when_files_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / ".claude" / "projects"
            root.mkdir(parents=True)
            file_path = root / "session.jsonl"
            file_path.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "timestamp": "2026-03-07T01:00:00Z",
                                "message": {
                                    "usage": {
                                        "input_tokens": 10,
                                        "cache_read_input_tokens": 0,
                                        "cache_creation_input_tokens": 0,
                                        "output_tokens": 5,
                                    }
                                },
                            }
                        )
                    ]
                )
            )

            with mock.patch("pathlib.Path.home", return_value=Path(tmp)):
                with mock.patch.dict(
                    os.environ, {"AI_USAGE_MONITOR_STATE_DIR": tmp}, clear=False
                ):
                    first = scan_claude_local_usage()
                    with mock.patch(
                        "builtins.open",
                        side_effect=AssertionError("unexpected file open"),
                    ):
                        second = scan_claude_local_usage()

            self.assertIsNotNone(first)
            self.assertIsNotNone(second)
            self.assertEqual(first.session_tokens, second.session_tokens)

    def test_scan_vertex_local_usage_reuses_cached_snapshot_when_files_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / ".claude" / "projects"
            root.mkdir(parents=True)
            file_path = root / "session.jsonl"
            file_path.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "timestamp": "2026-03-07T01:00:00Z",
                                "message": {
                                    "model": "claude-sonnet@vertex",
                                    "usage": {
                                        "input_tokens": 10,
                                        "cache_read_input_tokens": 0,
                                        "cache_creation_input_tokens": 0,
                                        "output_tokens": 5,
                                    },
                                },
                            }
                        )
                    ]
                )
            )

            with mock.patch("pathlib.Path.home", return_value=Path(tmp)):
                with mock.patch.dict(
                    os.environ, {"AI_USAGE_MONITOR_STATE_DIR": tmp}, clear=False
                ):
                    first = scan_vertex_local_usage()
                    with mock.patch(
                        "builtins.open",
                        side_effect=AssertionError("unexpected file open"),
                    ):
                        second = scan_vertex_local_usage()

            self.assertIsNotNone(first)
            self.assertIsNotNone(second)
            self.assertEqual(first.session_tokens, second.session_tokens)

    def test_scan_vertex_local_usage_ignores_non_vertex_messages(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / ".claude" / "projects"
            root.mkdir(parents=True)
            file_path = root / "session.jsonl"
            rows = [
                {
                    "timestamp": "2026-03-07T01:00:00Z",
                    "message": {
                        "model": "claude-sonnet",
                        "usage": {
                            "input_tokens": 50,
                            "cache_read_input_tokens": 0,
                            "cache_creation_input_tokens": 0,
                            "output_tokens": 10,
                        },
                    },
                },
                {
                    "timestamp": "2026-03-07T02:00:00Z",
                    "message": {
                        "model": "claude-sonnet@vertex",
                        "usage": {
                            "input_tokens": 10,
                            "cache_read_input_tokens": 0,
                            "cache_creation_input_tokens": 0,
                            "output_tokens": 5,
                        },
                    },
                },
            ]
            file_path.write_text("\n".join(json.dumps(row) for row in rows))

            with mock.patch("pathlib.Path.home", return_value=Path(tmp)):
                snapshot = scan_vertex_local_usage()

            self.assertIsNotNone(snapshot)
            self.assertEqual(snapshot.session_tokens, 15)
            self.assertEqual(snapshot.last_30_days_tokens, 15)

    def test_scan_opencode_local_usage_tracks_latest_session_and_rolling_totals(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / ".local" / "share" / "opencode" / "storage" / "message"
            root.mkdir(parents=True)
            now = datetime.now(timezone.utc)
            t1 = int((now - timedelta(hours=4)).timestamp() * 1000)
            t2 = int((now - timedelta(hours=2)).timestamp() * 1000)
            t3 = int((now - timedelta(hours=1)).timestamp() * 1000)

            rows = [
                {
                    "file": "m1.json",
                    "payload": {
                        "providerID": "opencode",
                        "sessionID": "sess_a",
                        "tokens": {
                            "input": 10,
                            "output": 5,
                            "reasoning": 0,
                            "cache": {"read": 2, "write": 0},
                        },
                        "time": {"completed": t1},
                    },
                },
                {
                    "file": "m2.json",
                    "payload": {
                        "providerID": "opencode",
                        "sessionID": "sess_b",
                        "tokens": {
                            "input": 20,
                            "output": 10,
                            "reasoning": 5,
                            "cache": {"read": 0, "write": 1},
                        },
                        "time": {"completed": t2},
                    },
                },
                {
                    "file": "m3.json",
                    "payload": {
                        "providerID": "opencode",
                        "sessionID": "sess_b",
                        "tokens": {
                            "input": 4,
                            "output": 6,
                            "reasoning": 0,
                            "cache": {"read": 1, "write": 0},
                        },
                        "time": {"completed": t3},
                    },
                },
            ]

            for row in rows:
                (root / row["file"]).write_text(json.dumps(row["payload"]))

            with mock.patch("pathlib.Path.home", return_value=Path(tmp)):
                snapshot = scan_opencode_local_usage()

            self.assertIsNotNone(snapshot)
            self.assertEqual(snapshot.session_tokens, 47)
            self.assertEqual(snapshot.last_30_days_tokens, 64)

    def test_scan_opencode_local_usage_ignores_non_opencode_and_invalid_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / ".local" / "share" / "opencode" / "storage" / "message"
            root.mkdir(parents=True)

            (root / "invalid.json").write_text(
                json.dumps({"providerID": "other", "tokens": {"input": 10}})
            )
            (root / "missing_completed.json").write_text(
                json.dumps(
                    {
                        "providerID": "opencode",
                        "sessionID": "sess_x",
                        "tokens": {
                            "input": 3,
                            "output": 2,
                            "reasoning": 0,
                            "cache": {"read": 0, "write": 0},
                        },
                        "time": {},
                    }
                )
            )

            with mock.patch("pathlib.Path.home", return_value=Path(tmp)):
                snapshot = scan_opencode_local_usage()

            self.assertIsNone(snapshot)

    def test_scan_opencode_local_usage_reads_config_fallback_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / ".config" / "opencode" / "storage" / "message"
            root.mkdir(parents=True)
            now = int(datetime.now(timezone.utc).timestamp() * 1000)
            (root / "m1.json").write_text(
                json.dumps(
                    {
                        "providerID": "opencode",
                        "sessionID": "sess_cfg",
                        "tokens": {
                            "input": 7,
                            "output": 3,
                            "reasoning": 0,
                            "cache": {"read": 0, "write": 0},
                        },
                        "time": {"completed": now},
                    }
                )
            )

            with mock.patch("pathlib.Path.home", return_value=Path(tmp)):
                snapshot = scan_opencode_local_usage()

            self.assertIsNotNone(snapshot)
            self.assertEqual(snapshot.session_tokens, 10)
            self.assertEqual(snapshot.last_30_days_tokens, 10)


if __name__ == "__main__":
    unittest.main()
