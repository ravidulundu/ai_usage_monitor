import unittest

from core.ai_usage_monitor.providers.gemini import _group_bucket_kind, _pick_bucket


class GeminiProviderTests(unittest.TestCase):
    def test_group_bucket_kind_detects_pro_and_flash(self):
        self.assertEqual(_group_bucket_kind("models/gemini-3-pro-preview"), "pro")
        self.assertEqual(_group_bucket_kind("models/gemini-2.0-flash"), "flash")

    def test_pick_bucket_chooses_most_used_for_kind(self):
        buckets = [
            {"modelId": "models/gemini-3-pro-preview", "remainingFraction": 0.8},
            {"modelId": "models/gemini-3-pro", "remainingFraction": 0.6},
            {"modelId": "models/gemini-2.0-flash", "remainingFraction": 0.95},
        ]
        picked = _pick_bucket(buckets, "pro")
        self.assertEqual(picked["modelId"], "models/gemini-3-pro")


if __name__ == "__main__":
    unittest.main()
