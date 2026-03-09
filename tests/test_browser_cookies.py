import sqlite3
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from core.ai_usage_monitor.browser_cookies import import_cookie_header


class BrowserCookieTests(unittest.TestCase):
    def test_import_cookie_header_reads_firefox_cookie_db(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "cookies.sqlite"
            conn = sqlite3.connect(db)
            conn.execute("CREATE TABLE moz_cookies (name TEXT, value TEXT, host TEXT)")
            conn.execute(
                "INSERT INTO moz_cookies (name, value, host) VALUES (?, ?, ?)",
                ("session", "abc123", "ampcode.com"),
            )
            conn.commit()
            conn.close()

            result = import_cookie_header(
                domains=["ampcode.com"],
                cookie_names={"session"},
                firefox_paths=[("Firefox (test)", db)],
                chromium_paths=[],
            )

            self.assertIsNotNone(result)
            self.assertEqual(result.header, "session=abc123")

    def test_import_cookie_header_reads_chromium_cookie_db(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "Cookies"
            conn = sqlite3.connect(db)
            conn.execute("CREATE TABLE cookies (name TEXT, value TEXT, host_key TEXT)")
            conn.execute(
                "INSERT INTO cookies (name, value, host_key) VALUES (?, ?, ?)",
                ("session", "xyz789", ".ollama.com"),
            )
            conn.commit()
            conn.close()

            result = import_cookie_header(
                domains=["ollama.com"],
                cookie_names={"session"},
                firefox_paths=[],
                chromium_paths=[("Chrome (test)", db)],
            )

            self.assertIsNotNone(result)
            self.assertEqual(result.header, "session=xyz789")

    def test_import_cookie_header_reuses_cached_result_for_same_db_fingerprint(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "Cookies"
            conn = sqlite3.connect(db)
            conn.execute("CREATE TABLE cookies (name TEXT, value TEXT, host_key TEXT)")
            conn.execute(
                "INSERT INTO cookies (name, value, host_key) VALUES (?, ?, ?)",
                ("session", "xyz789", ".ollama.com"),
            )
            conn.commit()
            conn.close()

            with mock.patch.dict(
                "os.environ", {"AI_USAGE_MONITOR_STATE_DIR": tmp}, clear=False
            ):
                with mock.patch(
                    "core.ai_usage_monitor.browser_cookies._query_chromium",
                    wraps=(
                        __import__(
                            "core.ai_usage_monitor.browser_cookies",
                            fromlist=["_query_chromium"],
                        )._query_chromium
                    ),
                ) as query_mock:
                    first = import_cookie_header(
                        domains=["ollama.com"],
                        cookie_names={"session"},
                        firefox_paths=[],
                        chromium_paths=[("Chrome (test)", db)],
                    )
                    second = import_cookie_header(
                        domains=["ollama.com"],
                        cookie_names={"session"},
                        firefox_paths=[],
                        chromium_paths=[("Chrome (test)", db)],
                    )

            self.assertIsNotNone(first)
            self.assertIsNotNone(second)
            self.assertEqual(first.header, second.header)
            self.assertEqual(query_mock.call_count, 1)

    def test_import_cookie_header_caches_negative_lookup(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(
                "os.environ", {"AI_USAGE_MONITOR_STATE_DIR": tmp}, clear=False
            ):
                with mock.patch(
                    "core.ai_usage_monitor.browser_cookies._query_chromium",
                    return_value=None,
                ) as query_mock:
                    first = import_cookie_header(
                        domains=["example.com"],
                        cookie_names={"session"},
                        firefox_paths=[],
                        chromium_paths=[("Chrome (test)", Path(tmp) / "missing")],
                    )
                    second = import_cookie_header(
                        domains=["example.com"],
                        cookie_names={"session"},
                        firefox_paths=[],
                        chromium_paths=[("Chrome (test)", Path(tmp) / "missing")],
                    )
            self.assertIsNone(first)
            self.assertIsNone(second)
            self.assertEqual(query_mock.call_count, 1)


if __name__ == "__main__":
    unittest.main()
