import unittest

from core.ai_usage_monitor.providers.minimax import parse_cookie_override, parse_minimax_payload


class MiniMaxProviderTests(unittest.TestCase):
    def test_parse_cookie_override_extracts_cookie_bearer_and_group(self):
        parsed = parse_cookie_override(
            "Cookie: foo=1; bar=2\nAuthorization: Bearer abc.def\nGroupId=12345"
        )

        self.assertEqual(parsed["cookieHeader"], "foo=1; bar=2")
        self.assertEqual(parsed["authorizationToken"], "abc.def")
        self.assertEqual(parsed["groupId"], "12345")

    def test_parse_minimax_payload_extracts_usage_window(self):
        payload = {
            "data": {
                "plan_name": "Pro",
                "model_remains": [
                    {
                        "current_interval_total_count": 200,
                        "current_interval_usage_count": 61,
                        "start_time": 1736200000,
                        "end_time": 1736218000,
                        "remains_time": 3600,
                    }
                ],
                "base_resp": {"status_code": 0, "status_msg": "ok"},
            }
        }

        parsed = parse_minimax_payload(payload)

        self.assertEqual(parsed["plan"], "Pro")
        self.assertEqual(parsed["total"], 200)
        self.assertEqual(parsed["used"], 139)
        self.assertEqual(round(parsed["used_pct"]), 70)


if __name__ == "__main__":
    unittest.main()
