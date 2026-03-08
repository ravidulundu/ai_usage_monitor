import unittest

from core.ai_usage_monitor.providers.kimik2 import collect_kimik2
from core.ai_usage_monitor.providers.openrouter import _base_url as openrouter_base_url
from core.ai_usage_monitor.providers.warp import _api_key as warp_api_key
from core.ai_usage_monitor.providers.zai import _api_url as zai_api_url


class APIProviderTests(unittest.TestCase):
    def test_openrouter_base_url_defaults(self):
        self.assertEqual(openrouter_base_url({}), "https://openrouter.ai/api/v1")

    def test_zai_api_url_defaults(self):
        self.assertEqual(
            zai_api_url({}), "https://api.z.ai/api/monitor/usage/quota/limit"
        )

    def test_warp_api_key_reads_settings(self):
        self.assertEqual(warp_api_key({"apiKey": "wk-test"}), "wk-test")

    def test_kimik2_returns_not_installed_without_key(self):
        legacy, state = collect_kimik2({})
        self.assertFalse(legacy["installed"])
        self.assertFalse(state.installed)


if __name__ == "__main__":
    unittest.main()
