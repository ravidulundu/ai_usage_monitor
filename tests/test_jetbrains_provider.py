import unittest

from core.ai_usage_monitor.providers.jetbrains import parse_jetbrains_xml


class JetBrainsProviderTests(unittest.TestCase):
    def test_parse_jetbrains_xml_extracts_quota_and_refill(self):
        xml = """
<application>
  <component name="AIAssistantQuotaManager2">
    <option name="quotaInfo" value="{&quot;type&quot;:&quot;Available&quot;,&quot;current&quot;:&quot;25&quot;,&quot;maximum&quot;:&quot;100&quot;,&quot;tariffQuota&quot;:{&quot;available&quot;:&quot;75&quot;},&quot;until&quot;:&quot;2026-03-31T00:00:00Z&quot;}" />
    <option name="nextRefill" value="{&quot;type&quot;:&quot;Known&quot;,&quot;next&quot;:&quot;2026-04-01T00:00:00Z&quot;,&quot;amount&quot;:&quot;100&quot;,&quot;duration&quot;:&quot;PT720H&quot;}" />
  </component>
</application>
"""
        parsed = parse_jetbrains_xml(
            xml, detected_ide={"name": "PyCharm", "version": "2025.3"}
        )

        self.assertEqual(parsed["quota_type"], "Available")
        self.assertEqual(parsed["used_percent"], 25.0)
        self.assertEqual(parsed["ide_name"], "PyCharm 2025.3")
        self.assertEqual(parsed["refill_at"], "2026-04-01T00:00:00+00:00")


if __name__ == "__main__":
    unittest.main()
