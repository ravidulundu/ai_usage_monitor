from __future__ import annotations

import json
import unittest
from pathlib import Path

from core.ai_usage_monitor.models import ProviderState
from core.ai_usage_monitor.providers.base import ProviderDescriptor
from core.ai_usage_monitor.sources.model import build_provider_source_model
from tools.project_health_contracts import SETTINGS_PRESENTATION_CANONICAL_FIELDS


FIXTURE_PATH = (
    Path(__file__).resolve().parent / "fixtures" / "settings_presentation_matrix.json"
)


def _descriptor(payload: dict) -> ProviderDescriptor:
    return ProviderDescriptor(
        id=str(payload.get("id") or ""),
        display_name=str(payload.get("displayName") or payload.get("id") or ""),
        source_modes=tuple(payload.get("sourceModes") or ("auto",)),
        preferred_source_policy=str(payload.get("preferredSourcePolicy") or "auto"),
    )


def _provider(payload: dict) -> ProviderState:
    return ProviderState(
        id=str(payload.get("id") or ""),
        display_name=str(payload.get("displayName") or payload.get("id") or ""),
        installed=bool(payload.get("installed", False)),
        authenticated=bool(payload.get("authenticated", True)),
        source=str(payload.get("source") or "auto"),
        error=payload.get("error"),
    )


class SettingsPresentationMatrixTests(unittest.TestCase):
    def test_settings_presentation_matrix_contract(self):
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        scenarios = list(fixture.get("scenarios") or [])
        self.assertGreaterEqual(len(scenarios), 3)

        for scenario in scenarios:
            with self.subTest(name=scenario.get("name")):
                descriptor = _descriptor(dict(scenario.get("descriptor") or {}))
                provider = _provider(dict(scenario.get("provider") or {}))
                settings = dict(scenario.get("settings") or {})
                expect = dict(scenario.get("expect") or {})

                source_model = build_provider_source_model(
                    provider=provider,
                    descriptor=descriptor,
                    settings=settings,
                )
                settings_presentation = dict(
                    source_model.get("settingsPresentation") or {}
                )

                for key in SETTINGS_PRESENTATION_CANONICAL_FIELDS:
                    self.assertIn(key, settings_presentation)
                    self.assertIsInstance(settings_presentation[key], str)

                self.assertEqual(source_model["canonicalMode"], expect["canonicalMode"])
                self.assertEqual(
                    settings_presentation["sourceModeLabel"], expect["sourceModeLabel"]
                )
                self.assertEqual(
                    settings_presentation["activeSourceLabel"],
                    expect["activeSourceLabel"],
                )
                self.assertEqual(
                    settings_presentation["sourceStatusLabel"],
                    expect["sourceStatusLabel"],
                )

                if "fallbackLabel" in expect:
                    self.assertEqual(
                        settings_presentation["fallbackLabel"], expect["fallbackLabel"]
                    )


if __name__ == "__main__":
    unittest.main()
