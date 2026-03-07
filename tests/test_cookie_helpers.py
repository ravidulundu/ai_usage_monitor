import unittest

from core.ai_usage_monitor.cookies import cookie_header_from_settings, cookie_source_from_settings, normalize_cookie_header


class CookieHelperTests(unittest.TestCase):
    def test_normalize_cookie_header_strips_prefix(self):
        self.assertEqual(normalize_cookie_header("Cookie: session=abc"), "session=abc")

    def test_cookie_source_defaults(self):
        self.assertEqual(cookie_source_from_settings({}, default="off"), "off")

    def test_cookie_header_reads_settings(self):
        self.assertEqual(cookie_header_from_settings({"manualCookieHeader": "session=abc"}), "session=abc")


if __name__ == "__main__":
    unittest.main()
