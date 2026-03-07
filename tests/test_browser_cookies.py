import sqlite3
import tempfile
import unittest
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


if __name__ == "__main__":
    unittest.main()
