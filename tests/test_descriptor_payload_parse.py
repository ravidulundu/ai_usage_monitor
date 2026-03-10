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


def _expected_capabilities(raw: dict, mode_set: set[str]) -> tuple[bool, bool, bool]:
    by_source = dict(raw.get("usageDashboardBySource") or {})
    dashboard_modes = {
        str(source).strip().lower()
        for source in by_source.keys()
        if str(source).strip()
    }
    signal_modes = mode_set | dashboard_modes
    supports_local = bool(signal_modes.intersection({"cli", "local", "local_cli"}))
    supports_api = bool(signal_modes.intersection({"api", "oauth"}))
    supports_web = bool(signal_modes.intersection({"web", "remote"}))

    if not (supports_local or supports_api or supports_web):
        policy = str(raw.get("preferredSourcePolicy") or "").strip().lower()
        if policy in {"local_first", "cli_first"}:
            supports_local = True
        elif policy == "api_first":
            supports_api = True
        elif policy in {"web_first", "remote_first"}:
            supports_web = True
        elif policy == "oauth_first":
            supports_api = True

    return supports_local, supports_api, supports_web


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
                (
                    expected_supports_local,
                    expected_supports_api,
                    expected_supports_web,
                ) = _expected_capabilities(raw, mode_set)
                self.assertEqual(
                    parsed["supports_local"],
                    expected_supports_local,
                )
                self.assertEqual(
                    parsed["supports_api"],
                    expected_supports_api,
                )
                self.assertEqual(
                    parsed["supports_web"],
                    expected_supports_web,
                )
                self.assertEqual(
                    parsed["supports_probe"],
                    ("auto" in mode_set or "probe" in mode_set),
                )

                for source in parsed["usage_dashboard_by_source"]:
                    self.assertTrue(source in mode_set or "auto" in mode_set)


if __name__ == "__main__":
    unittest.main()
