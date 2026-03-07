import unittest

from core.ai_usage_monitor.providers.kiro import parse_kiro_output


class KiroProviderTests(unittest.TestCase):
    def test_parse_kiro_output_extracts_primary_and_bonus_usage(self):
        output = """
Plan: Kiro Pro
Monthly credits:
██████████████████████ 42% (resets on 01/15)
(21.00 of 50 covered in plan)
Bonus credits:
10.00/100 credits used, expires in 88 days
"""
        parsed = parse_kiro_output(output)

        self.assertEqual(parsed["plan_name"], "Kiro Pro")
        self.assertEqual(parsed["credits_percent"], 42.0)
        self.assertEqual(parsed["bonus_used"], 10.0)
        self.assertEqual(parsed["bonus_total"], 100.0)
        self.assertEqual(parsed["bonus_days"], 88)


if __name__ == "__main__":
    unittest.main()
