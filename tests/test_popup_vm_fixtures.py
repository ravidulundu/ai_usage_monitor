from __future__ import annotations

import json
import unittest
from pathlib import Path

from core.ai_usage_monitor.models import AppState, MetricWindow, ProviderState
from core.ai_usage_monitor.presentation.popup_vm import build_popup_view_model


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


def _project_popup_contract(payload: dict) -> dict:
    popup = payload["popup"]
    return {
        "selectedProviderId": popup["selectedProviderId"],
        "enabledProviderIds": popup["enabledProviderIds"],
        "selectableProviderIds": popup["selectableProviderIds"],
        "overviewProviderIds": popup["overviewProviderIds"],
        "hasOverview": popup["hasOverview"],
        "identityRefreshPending": popup["identityRefreshPending"],
        "tabs": [
            {
                "id": tab["id"],
                "kind": tab["kind"],
                "selected": bool(tab["selected"]),
            }
            for tab in popup["tabs"]
        ],
        "switcherTabs": [
            {
                "id": tab["id"],
                "kind": tab["kind"],
            }
            for tab in popup["switcherTabs"]
        ],
        "panel": {
            "providerId": popup["panel"]["providerId"],
            "tone": popup["panel"]["tone"],
            "displayText": popup["panel"]["displayText"],
        },
        "providers": [
            {
                "id": provider["id"],
                "sourceMode": provider["sourceMode"],
                "metricsKinds": [metric["kind"] for metric in provider["metrics"]],
                "switchingState": {
                    "active": bool(provider["switchingState"]["active"]),
                    "kind": provider["switchingState"]["kind"],
                },
                "actions": [action["id"] for action in provider["actions"]],
            }
            for provider in popup["providers"]
        ],
    }


class PopupViewModelFixtureTests(unittest.TestCase):
    def test_popup_vm_contract_projection_fixture(self):
        state = AppState(
            providers=[
                ProviderState(
                    id="codex",
                    display_name="OpenAI Codex",
                    installed=True,
                    enabled=True,
                    source="cli",
                    primary_metric=MetricWindow("5h", 21, "2099-01-01T00:00:00+00:00"),
                    secondary_metric=MetricWindow(
                        "7d", 45, "2099-01-02T00:00:00+00:00"
                    ),
                    metadata={
                        "identity": {"changed": False, "fingerprint": "codex-fp"}
                    },
                    extras={"identityFingerprint": "codex-fp"},
                ),
                ProviderState(
                    id="openrouter",
                    display_name="OpenRouter",
                    installed=False,
                    enabled=True,
                    source="api",
                    metadata={
                        "identity": {
                            "changed": True,
                            "sourceChanged": True,
                            "fingerprint": "openrouter-fp",
                        }
                    },
                    extras={
                        "identityChanged": True,
                        "sourceSwitched": True,
                        "identityFingerprint": "openrouter-fp",
                    },
                ),
            ],
            overview_provider_ids=["codex", "openrouter"],
            updated_at="2099-01-01T00:00:00+00:00",
        )

        payload = build_popup_view_model(state, refresh_interval_seconds=60)
        contract_projection = _project_popup_contract(payload)
        fixture = json.loads(
            (FIXTURE_DIR / "popup_vm_contract_projection.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(contract_projection, fixture)


if __name__ == "__main__":
    unittest.main()
