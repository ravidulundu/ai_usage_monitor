import unittest

from core.ai_usage_monitor.providers.ollama import parse_ollama_html


class OllamaProviderTests(unittest.TestCase):
    def test_parse_ollama_html_extracts_plan_and_usage_windows(self):
        html = """
<span>Cloud Usage</span><span>Pro</span>
<div id="header-email">user@example.com</div>
<div>Session usage</div>
<div>42% used</div>
<span data-time="2026-03-08T01:00:00Z"></span>
<div>Weekly usage</div>
<div style="width: 61%"></div>
<span data-time="2026-03-10T01:00:00Z"></span>
"""
        parsed = parse_ollama_html(html)

        self.assertEqual(parsed["plan"], "Pro")
        self.assertEqual(parsed["email"], "user@example.com")
        self.assertEqual(parsed["session"]["used"], 42.0)
        self.assertEqual(parsed["weekly"]["used"], 61.0)


if __name__ == "__main__":
    unittest.main()
