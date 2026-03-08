from __future__ import annotations

import json
import unittest
from pathlib import Path

from core.ai_usage_monitor.models import (
    AppState,
    LocalUsageSnapshot,
    MetricWindow,
    ProviderState,
)
from core.ai_usage_monitor.presentation.popup_vm import build_popup_view_model


FIXTURE_PATH = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "popup_vm_states"
    / "state_matrix.json"
)
CANONICAL_ACTION_IDS = ["usage_dashboard", "status_page", "settings", "about", "quit"]


def _metric(payload: dict | None) -> MetricWindow | None:
    if not isinstance(payload, dict):
        return None
    return MetricWindow(
        str(payload.get("label") or ""),
        float(payload.get("usedPct")),
        payload.get("resetAt"),
        kind=str(payload.get("kind") or "window"),
    )


def _local_usage(payload: dict | None) -> LocalUsageSnapshot | None:
    if not isinstance(payload, dict):
        return None
    return LocalUsageSnapshot(
        session_tokens=payload.get("sessionTokens"),
        last_30_days_tokens=payload.get("last30DaysTokens"),
        session_cost_usd=payload.get("sessionCostUSD"),
        last_30_days_cost_usd=payload.get("last30DaysCostUSD"),
    )


def _provider(payload: dict) -> ProviderState:
    return ProviderState(
        id=str(payload.get("id") or ""),
        display_name=str(payload.get("displayName") or payload.get("id") or ""),
        enabled=bool(payload.get("enabled", True)),
        installed=bool(payload.get("installed", False)),
        authenticated=bool(payload.get("authenticated", True)),
        status=str(payload.get("status") or "ok"),
        source=str(payload.get("source") or "local"),
        primary_metric=_metric(payload.get("primaryMetric")),
        secondary_metric=_metric(payload.get("secondaryMetric")),
        local_usage=_local_usage(payload.get("localUsage")),
        source_model=dict(payload.get("sourceModel") or {}),
        metadata=dict(payload.get("metadata") or {}),
        extras=dict(payload.get("extras") or {}),
        error=payload.get("error"),
        incident=payload.get("incident"),
    )


def _scenario_app_state(scenario: dict) -> AppState:
    state = dict(scenario.get("state") or {})
    providers = [_provider(item) for item in list(state.get("providers") or [])]
    return AppState(
        providers=providers,
        overview_provider_ids=list(state.get("overviewProviderIds") or []),
        updated_at=str(state.get("updatedAt") or ""),
    )


class PopupVmStateMatrixTests(unittest.TestCase):
    def test_fixture_includes_required_regression_scenarios(self):
        payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        scenario_names = {
            str(item.get("name") or "").strip()
            for item in list(payload.get("scenarios") or [])
        }
        self.assertTrue(
            {
                "normal_state",
                "no_data",
                "stale",
                "error",
                "fallback_active",
                "account_switched",
                "source_switched",
                "provider_unavailable",
            }.issubset(scenario_names)
        )

    def test_fixture_state_matrix_smoke_and_regression(self):
        payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        scenarios = list(payload.get("scenarios") or [])
        self.assertGreaterEqual(len(scenarios), 8)

        for scenario in scenarios:
            with self.subTest(name=scenario.get("name")):
                vm = build_popup_view_model(
                    _scenario_app_state(scenario),
                    refresh_interval_seconds=int(
                        scenario.get("refreshIntervalSeconds") or 60
                    ),
                    preferred_provider_id=scenario.get("preferredProviderId"),
                )
                popup = vm["popup"]
                expect = dict(scenario.get("expect") or {})

                self.assertEqual(
                    popup["selectedProviderId"], expect["selectedProviderId"]
                )

                if "enabledProviderIds" in expect:
                    self.assertEqual(
                        popup["enabledProviderIds"], expect["enabledProviderIds"]
                    )
                if "overviewProviderIds" in expect:
                    self.assertEqual(
                        popup["overviewProviderIds"], expect["overviewProviderIds"]
                    )
                if "overviewCardProviderIds" in expect:
                    overview_ids = [
                        str(card.get("providerId") or "")
                        for card in popup["overviewCards"]
                        if card.get("providerId")
                    ]
                    self.assertEqual(overview_ids, expect["overviewCardProviderIds"])

                provider_id = expect.get("providerId") or popup["selectedProviderId"]
                provider = next(
                    item for item in popup["providers"] if item["id"] == provider_id
                )
                session_metric = next(
                    item for item in provider["metrics"] if item["kind"] == "session"
                )

                self.assertEqual(
                    provider["errorState"]["hasError"], expect["errorHasError"]
                )
                self.assertEqual(
                    provider["switchingState"]["active"], expect["switching"]["active"]
                )
                self.assertEqual(
                    provider["switchingState"]["kind"], expect["switching"]["kind"]
                )
                self.assertEqual(popup["panel"]["tone"], expect["panelTone"])

                unavailable = provider["sourcePresentation"].get("unavailableReason")
                unavailable_code = (
                    unavailable.get("code") if isinstance(unavailable, dict) else None
                )
                self.assertEqual(unavailable_code, expect.get("sourceUnavailableCode"))

                for tag in expect.get("sourceStatusTagIncludes", []):
                    self.assertIn(
                        tag, provider["sourcePresentation"].get("statusTags", [])
                    )

                metric_expect = dict(expect.get("metric") or {})
                self.assertEqual(
                    session_metric["available"], metric_expect.get("available")
                )
                self.assertEqual(session_metric["stale"], metric_expect.get("stale"))

                left_text = str(session_metric.get("leftText") or "")
                if "leftTextEquals" in metric_expect:
                    self.assertEqual(left_text, metric_expect["leftTextEquals"])
                if "leftTextContains" in metric_expect:
                    self.assertIn(metric_expect["leftTextContains"], left_text)

                secondary_text = str(session_metric.get("secondaryText") or "")
                if "secondaryTextContains" in metric_expect:
                    self.assertIn(
                        metric_expect["secondaryTextContains"], secondary_text
                    )

                actions = provider["actions"]
                self.assertEqual(
                    [action["id"] for action in actions], CANONICAL_ACTION_IDS
                )
                for action in actions:
                    self.assertIn("label", action)
                    self.assertIn("enabled", action)
                    self.assertIn("visible", action)
                    self.assertIn("intent", action)
                    self.assertIn("target", action)


if __name__ == "__main__":
    unittest.main()
