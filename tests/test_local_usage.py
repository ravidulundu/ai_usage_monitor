import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from core.ai_usage_monitor.local_usage import scan_claude_local_usage, scan_codex_local_usage


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


if __name__ == "__main__":
    unittest.main()
