from __future__ import annotations

import unittest

from core.ai_usage_monitor.cli import config_ui_payload


REQUIRED_KEYS = {
    "id",
    "displayName",
    "shortName",
    "sourceModes",
    "supportedSources",
    "providerCapabilities",
    "fetchStrategy",
    "branding",
}


def _parse_descriptor(raw: dict) -> dict:
    provider_id = str(raw.get("id") or "").strip()
    display_name = str(raw.get("displayName") or provider_id).strip()
    short_name = str(raw.get("shortName") or display_name).strip()

    source_modes = [
        str(mode).strip().lower()
        for mode in list(raw.get("sourceModes") or [])
        if str(mode).strip()
    ]
    supported_sources = [
        str(mode).strip().lower()
        for mode in list(raw.get("supportedSources") or source_modes)
        if str(mode).strip()
    ]

    capabilities = dict(raw.get("providerCapabilities") or {})
    fetch_strategy = dict(raw.get("fetchStrategy") or {})
    by_source = dict(raw.get("usageDashboardBySource") or {})

    return {
        "id": provider_id,
        "display_name": display_name,
        "short_name": short_name,
        "source_modes": source_modes,
        "supported_sources": supported_sources,
        "supports_local": bool(capabilities.get("supportsLocalCli")),
        "supports_api": bool(capabilities.get("supportsApi")),
        "supports_web": bool(capabilities.get("supportsWeb")),
        "supports_probe": bool(fetch_strategy.get("supportsProbe")),
        "usage_dashboard_by_source": {
            str(key).strip().lower(): str(value).strip()
            for key, value in by_source.items()
            if str(key).strip() and str(value).strip()
        },
    }


class DescriptorPayloadParseTests(unittest.TestCase):
    def test_config_ui_descriptors_follow_parse_contract(self):
        payload = config_ui_payload()
        descriptors = list(payload.get("descriptors") or [])

        self.assertGreaterEqual(len(descriptors), 10)

        for raw in descriptors:
            with self.subTest(provider_id=raw.get("id")):
                self.assertTrue(REQUIRED_KEYS.issubset(raw.keys()))

                parsed = _parse_descriptor(raw)
                self.assertTrue(parsed["id"])
                self.assertTrue(parsed["display_name"])
                self.assertTrue(parsed["short_name"])
                self.assertGreaterEqual(len(parsed["source_modes"]), 1)
                self.assertEqual(parsed["source_modes"], parsed["supported_sources"])

                mode_set = set(parsed["source_modes"])
                self.assertEqual(
                    parsed["supports_local"],
                    bool(mode_set.intersection({"cli", "local", "oauth"})),
                )
                self.assertEqual(parsed["supports_api"], "api" in mode_set)
                self.assertEqual(
                    parsed["supports_web"],
                    bool(mode_set.intersection({"web", "remote"})),
                )
                self.assertEqual(
                    parsed["supports_probe"],
                    ("auto" in mode_set or "probe" in mode_set),
                )

                for source in parsed["usage_dashboard_by_source"]:
                    self.assertTrue(source in mode_set or "auto" in mode_set)


if __name__ == "__main__":
    unittest.main()
