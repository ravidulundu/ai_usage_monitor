import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from core.ai_usage_monitor.providers.codex import _latest_token_count_snapshot, normalize_codex_rate_limits


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

            payload, model = _latest_token_count_snapshot(root)

        self.assertEqual((payload.get("rate_limits") or {}).get("primary", {}).get("used_percent"), 80)
        self.assertEqual((payload.get("rate_limits") or {}).get("secondary", {}).get("used_percent"), 41)
        self.assertEqual(model, "gpt-5.4-high")


if __name__ == "__main__":
    unittest.main()
