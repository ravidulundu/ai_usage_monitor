import unittest
from unittest import mock

from core.ai_usage_monitor.providers.gemini import (
    _group_bucket_kind,
    _pick_bucket,
    collect_gemini,
)


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

    def test_collect_gemini_returns_not_installed_when_creds_missing(self):
        with mock.patch(
            "core.ai_usage_monitor.providers.gemini._gemini_creds_path"
        ) as creds_path_mock:
            creds_path_mock.return_value = mock.Mock(
                exists=mock.Mock(return_value=False)
            )

            legacy, state = collect_gemini()

        self.assertEqual(legacy, {"installed": False})
        self.assertFalse(state.installed)
        self.assertEqual(state.source, "oauth")

    def test_collect_gemini_maps_successful_bucket_response(self):
        creds_path = mock.Mock()
        creds_path.exists.return_value = True
        with mock.patch(
            "core.ai_usage_monitor.providers.gemini._gemini_creds_path",
            return_value=creds_path,
        ):
            with mock.patch(
                "core.ai_usage_monitor.providers.gemini._load_gemini_creds",
                return_value={"access_token": "tok", "email": "user@example.com"},
            ):
                with mock.patch(
                    "core.ai_usage_monitor.providers.gemini._fetch_gemini_buckets",
                    return_value=(
                        [
                            {
                                "modelId": "models/gemini-2.0-flash",
                                "remainingFraction": 0.58,
                                "resetTime": "2026-03-10T00:00:00Z",
                            }
                        ],
                        "gemini-2.0-flash",
                    ),
                ):
                    with mock.patch(
                        "core.ai_usage_monitor.providers.gemini.fetch_google_workspace_status",
                        return_value={"title": "ok"},
                    ):
                        legacy, state = collect_gemini()

        self.assertTrue(legacy["installed"])
        self.assertTrue(legacy["authenticated"])
        self.assertEqual(legacy["model"], "gemini-2.0-flash")
        self.assertEqual(state.source, "oauth")
        self.assertIsNotNone(state.primary_metric)
        self.assertEqual(state.extras["model"], "gemini-2.0-flash")

    def test_collect_gemini_retries_after_token_refresh(self):
        creds_path = mock.Mock()
        creds_path.exists.return_value = True
        unauthorized = __import__("urllib.error").error.HTTPError(
            "https://example.test", 401, "Unauthorized", {}, None
        )
        with mock.patch(
            "core.ai_usage_monitor.providers.gemini._gemini_creds_path",
            return_value=creds_path,
        ):
            with mock.patch(
                "core.ai_usage_monitor.providers.gemini._load_gemini_creds",
                side_effect=[
                    {"access_token": "expired", "refresh_token": "refresh"},
                    {"access_token": "fresh", "refresh_token": "refresh"},
                ],
            ):
                with mock.patch(
                    "core.ai_usage_monitor.providers.gemini._fetch_gemini_buckets",
                    side_effect=[
                        unauthorized,
                        ([{"modelId": "models/gemini-2.0-flash"}], "gemini-2.0-flash"),
                    ],
                ):
                    with mock.patch(
                        "core.ai_usage_monitor.providers.gemini.refresh_gemini_token",
                        return_value=(
                            True,
                            {"access_token": "fresh", "refresh_token": "refresh"},
                            None,
                        ),
                    ) as refresh_mock:
                        with mock.patch(
                            "core.ai_usage_monitor.providers.gemini.fetch_google_workspace_status",
                            return_value=None,
                        ):
                            legacy, state = collect_gemini()

        self.assertTrue(legacy["installed"])
        self.assertTrue(state.authenticated)
        self.assertEqual(refresh_mock.call_count, 1)


if __name__ == "__main__":
    unittest.main()
