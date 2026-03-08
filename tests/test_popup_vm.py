import unittest
from datetime import datetime, timedelta, timezone

from core.ai_usage_monitor.models import (
    AppState,
    LocalUsageSnapshot,
    MetricWindow,
    ProviderState,
)
from core.ai_usage_monitor.presentation.popup_vm import build_popup_view_model


class PopupViewModelTests(unittest.TestCase):
    def test_build_popup_vm_includes_tabs_metrics_actions_and_overview(self):
        state = AppState(
            providers=[
                ProviderState(
                    id="codex",
                    display_name="OpenAI Codex",
                    installed=True,
                    enabled=True,
                    source="cli",
                    primary_metric=MetricWindow("5h", 12, "2099-01-01T00:00:00+00:00"),
                    secondary_metric=MetricWindow(
                        "7d", 48, "2099-01-02T00:00:00+00:00"
                    ),
                    local_usage=LocalUsageSnapshot(
                        session_tokens=15000,
                        last_30_days_tokens=218000000,
                        session_cost_usd=0.04,
                        last_30_days_cost_usd=254.24,
                    ),
                    metadata={
                        "branding": {
                            "iconKey": "codex",
                            "color": "#49A3B0",
                            "badgeText": "OX",
                        }
                    },
                    extras={
                        "plan": "max",
                        "model": "gpt-5-codex",
                        "hasRateLimits": True,
                    },
                )
            ],
            overview_provider_ids=["codex"],
            updated_at="2099-01-01T00:00:01+00:00",
        )

        payload = build_popup_view_model(state, refresh_interval_seconds=60)
        popup = payload["popup"]

        self.assertTrue(popup["hasOverview"])
        self.assertEqual(popup["enabledProviderIds"], ["codex"])
        self.assertEqual(popup["overviewProviderIds"], ["codex"])
        self.assertEqual(popup["selectedProviderId"], "codex")
        self.assertEqual(popup["tabs"][0]["id"], "overview")
        self.assertEqual(popup["tabs"][0]["miniMetric"]["displayText"], "—")
        self.assertEqual(popup["tabs"][1]["miniMetric"]["displayText"], "12%")
        self.assertEqual(popup["overviewCards"][0]["metrics"][0]["displayText"], "12%")
        provider = popup["providers"][0]
        self.assertEqual(provider["id"], "codex")
        self.assertEqual(provider["metrics"][0]["kind"], "session")
        self.assertEqual(provider["metrics"][1]["kind"], "weekly")
        self.assertEqual(provider["actions"][0]["id"], "usage_dashboard")
        self.assertEqual(
            provider["actions"][0]["target"], "https://chatgpt.com/codex/settings/usage"
        )
        self.assertEqual(provider["actions"][1]["id"], "status_page")
        self.assertEqual(provider["links"]["statusUrl"], "https://status.openai.com/")
        self.assertEqual(popup["providerOrder"], ["codex"])

    def test_build_popup_vm_prefers_persisted_provider_when_available(self):
        state = AppState(
            providers=[
                ProviderState(
                    id="codex",
                    display_name="OpenAI Codex",
                    installed=True,
                    enabled=True,
                    source="cli",
                    primary_metric=MetricWindow("5h", 12, "2099-01-01T00:00:00+00:00"),
                ),
                ProviderState(
                    id="claude",
                    display_name="Claude Code",
                    installed=True,
                    enabled=True,
                    source="oauth",
                    primary_metric=MetricWindow("5h", 4, "2099-01-01T00:00:00+00:00"),
                ),
            ],
            overview_provider_ids=["codex", "claude"],
            updated_at="2099-01-01T00:00:01+00:00",
        )

        payload = build_popup_view_model(
            state,
            refresh_interval_seconds=60,
            preferred_provider_id="claude",
        )
        popup = payload["popup"]

        self.assertEqual(popup["selectedProviderId"], "claude")
        self.assertEqual(popup["providerOrder"], ["claude", "codex"])
        self.assertEqual(popup["tabs"][0]["id"], "overview")
        self.assertTrue(
            any(tab["id"] == "claude" and tab["selected"] for tab in popup["tabs"])
        )

    def test_enabled_provider_is_visible_even_if_not_installed(self):
        state = AppState(
            providers=[
                ProviderState(
                    id="openrouter",
                    display_name="OpenRouter",
                    installed=False,
                    enabled=True,
                    source="api",
                ),
                ProviderState(
                    id="codex",
                    display_name="OpenAI Codex",
                    installed=True,
                    enabled=True,
                    source="cli",
                    primary_metric=MetricWindow("5h", 12, "2099-01-01T00:00:00+00:00"),
                ),
            ],
            overview_provider_ids=["openrouter", "codex"],
            updated_at="2099-01-01T00:00:01+00:00",
        )

        payload = build_popup_view_model(state, refresh_interval_seconds=60)
        popup = payload["popup"]
        tab_ids = [tab["id"] for tab in popup["tabs"] if tab["kind"] == "provider"]
        provider_ids = [provider["id"] for provider in popup["providers"]]

        self.assertIn("openrouter", tab_ids)
        self.assertIn("openrouter", provider_ids)
        self.assertEqual(popup["providerOrder"][0], "codex")
        self.assertEqual(popup["enabledProviderIds"], ["codex", "openrouter"])
        self.assertEqual(popup["overviewProviderIds"], ["openrouter", "codex"])
        self.assertEqual(popup["overviewCards"][0]["providerId"], "openrouter")

    def test_popup_provider_includes_source_model_contract(self):
        source_model = {
            "canonicalMode": "hybrid",
            "providerCapabilities": {
                "supportsLocalCli": True,
                "supportsApi": False,
                "supportsWeb": True,
            },
            "sourceStrategy": {
                "preferredSource": "auto",
                "resolvedSource": "cli",
                "fallbackReason": "auto_selected",
                "resolutionReason": "auto_selected_best_source",
                "fallbackActive": True,
            },
            "availability": {
                "localToolInstalled": True,
                "apiKeyPresent": False,
                "apiConfigured": True,
                "authValid": True,
                "rateLimitState": "ok",
            },
            "preferredSource": "auto",
            "activeSource": "cli",
            "availableSources": ["auto", "cli", "web"],
            "fallbackState": {
                "active": True,
                "from": "auto",
                "to": "cli",
                "reason": "auto_selected",
                "label": "AUTO → CLI",
            },
            "sourceLabel": "Hybrid (local-first)",
            "sourceDetails": "Preferred AUTO · Active CLI · Fallback active",
            "authState": "authenticated",
            "localToolDetected": True,
            "apiConfigured": True,
            "localToolInstalled": True,
            "apiKeyPresent": False,
            "authValid": True,
            "rateLimitState": "ok",
            "resolvedSource": "cli",
            "fallbackReason": "auto_selected",
            "resolutionReason": "auto_selected_best_source",
        }
        state = AppState(
            providers=[
                ProviderState(
                    id="opencode",
                    display_name="OpenCode",
                    installed=True,
                    enabled=True,
                    source="cli",
                    source_model=source_model,
                    primary_metric=MetricWindow("5h", 8, "2099-01-01T00:00:00+00:00"),
                )
            ],
            overview_provider_ids=[],
            updated_at="2099-01-01T00:00:01+00:00",
        )

        payload = build_popup_view_model(state, refresh_interval_seconds=60)
        provider = payload["popup"]["providers"][0]
        self.assertEqual(provider["sourceModel"]["canonicalMode"], "hybrid")
        self.assertEqual(provider["sourceLabel"], "Hybrid (local-first)")
        self.assertEqual(
            provider["sourceDetails"], "Preferred AUTO · Active CLI · Fallback active"
        )
        self.assertEqual(provider["authState"], "authenticated")
        self.assertEqual(provider["fallbackState"]["active"], True)
        self.assertEqual(provider["preferredSource"], "auto")
        self.assertEqual(provider["resolvedSource"], "cli")
        self.assertEqual(provider["availableSources"], ["auto", "cli", "web"])
        self.assertEqual(provider["fallbackReason"], "auto_selected")
        self.assertTrue(provider["localToolInstalled"])
        self.assertTrue(provider["apiConfigured"])
        self.assertTrue(provider["authValid"])
        self.assertTrue(provider["providerCapabilities"]["supportsLocalCli"])
        self.assertEqual(provider["sourceStrategy"]["resolvedSource"], "cli")
        self.assertTrue(provider["availability"]["localToolInstalled"])
        self.assertTrue(provider["availability"]["apiConfigured"])

    def test_disabled_provider_is_hidden_even_if_installed(self):
        state = AppState(
            providers=[
                ProviderState(
                    id="codex",
                    display_name="OpenAI Codex",
                    installed=True,
                    enabled=False,
                    source="cli",
                    primary_metric=MetricWindow("5h", 12, "2099-01-01T00:00:00+00:00"),
                ),
                ProviderState(
                    id="claude",
                    display_name="Claude Code",
                    installed=True,
                    enabled=True,
                    source="oauth",
                    primary_metric=MetricWindow("5h", 4, "2099-01-01T00:00:00+00:00"),
                ),
            ],
            overview_provider_ids=["codex", "claude"],
            updated_at="2099-01-01T00:00:01+00:00",
        )

        payload = build_popup_view_model(state, refresh_interval_seconds=60)
        popup = payload["popup"]
        tab_ids = [tab["id"] for tab in popup["tabs"] if tab["kind"] == "provider"]

        self.assertNotIn("codex", tab_ids)
        self.assertEqual(popup["providerOrder"], ["claude"])

    def test_build_popup_vm_maps_rate_limits_null_to_unavailable_copy(self):
        state = AppState(
            providers=[
                ProviderState(
                    id="codex",
                    display_name="OpenAI Codex",
                    installed=True,
                    enabled=True,
                    source="cli",
                    primary_metric=None,
                    secondary_metric=None,
                    local_usage=LocalUsageSnapshot(
                        session_tokens=1234, last_30_days_tokens=5678
                    ),
                    metadata={"branding": {"iconKey": "codex"}},
                    extras={"hasRateLimits": False},
                )
            ],
            overview_provider_ids=[],
            updated_at="2099-01-01T00:00:00+00:00",
        )

        payload = build_popup_view_model(state, refresh_interval_seconds=60)
        provider = payload["popup"]["providers"][0]
        session = provider["metrics"][0]
        weekly = provider["metrics"][1]

        self.assertFalse(session["available"])
        self.assertIsNone(session["percent"])
        self.assertEqual(session["leftText"], "Local usage unavailable")
        self.assertEqual(session["rightText"], "—")
        self.assertEqual(session["tone"], "accent")
        self.assertFalse(weekly["available"])
        self.assertEqual(weekly["leftText"], "Local usage unavailable")
        self.assertEqual(weekly["tone"], "accent")

    def test_fetch_fail_uses_unable_to_refresh_and_error_summary(self):
        state = AppState(
            providers=[
                ProviderState(
                    id="claude",
                    display_name="Claude Code",
                    installed=True,
                    enabled=True,
                    source="oauth",
                    primary_metric=None,
                    secondary_metric=None,
                    error="Rate limited: Please try again later.",
                )
            ],
            overview_provider_ids=[],
            updated_at="2099-01-01T00:00:00+00:00",
        )

        payload = build_popup_view_model(state, refresh_interval_seconds=60)
        provider = payload["popup"]["providers"][0]
        session = provider["metrics"][0]

        self.assertFalse(session["available"])
        self.assertIsNone(session["percent"])
        self.assertEqual(session["leftText"], "Unable to refresh")
        self.assertEqual(session["rightText"], "—")
        self.assertEqual(session["secondaryText"], "Rate limited")
        self.assertEqual(session["errorMessage"], "Rate limited")
        self.assertEqual(session["tone"], "error")

    def test_bucket_missing_percent_does_not_fallback_to_zero(self):
        state = AppState(
            providers=[
                ProviderState(
                    id="codex",
                    display_name="OpenAI Codex",
                    installed=True,
                    enabled=True,
                    source="cli",
                    primary_metric=MetricWindow("5h", 42, "2099-01-01T00:00:00+00:00"),
                    secondary_metric=MetricWindow(
                        "7d", 60, "2099-01-02T00:00:00+00:00"
                    ),
                    extras={
                        "buckets": [
                            {
                                "model": "gpt-5",
                                "used_pct": None,
                                "reset_time": "2099-01-03T00:00:00+00:00",
                            }
                        ]
                    },
                )
            ],
            overview_provider_ids=[],
            updated_at="2099-01-01T00:00:00+00:00",
        )

        payload = build_popup_view_model(state, refresh_interval_seconds=60)
        provider = payload["popup"]["providers"][0]
        model_metric = provider["metrics"][2]

        self.assertEqual(model_metric["kind"], "model")
        self.assertFalse(model_metric["available"])
        self.assertIsNone(model_metric["percent"])
        self.assertEqual(model_metric["leftText"], "Data unavailable")
        self.assertEqual(model_metric["rightText"], "—")
        self.assertEqual(model_metric["tone"], "accent")

    def test_weekly_pace_secondary_text_includes_deficit_and_runout_projection(self):
        now = datetime.now(timezone.utc)
        state = AppState(
            providers=[
                ProviderState(
                    id="codex",
                    display_name="OpenAI Codex",
                    installed=True,
                    enabled=True,
                    source="cli",
                    primary_metric=MetricWindow(
                        "5h", 8, (now + timedelta(hours=4, minutes=58)).isoformat()
                    ),
                    secondary_metric=MetricWindow(
                        "7d", 70, (now + timedelta(days=3)).isoformat()
                    ),
                )
            ],
            overview_provider_ids=[],
            updated_at=now.isoformat(),
        )

        payload = build_popup_view_model(state, refresh_interval_seconds=60)
        provider = payload["popup"]["providers"][0]
        weekly = provider["metrics"][1]

        self.assertTrue(weekly["available"])
        self.assertIsNotNone(weekly["secondaryText"])
        self.assertIn("Pace:", weekly["secondaryText"])
        self.assertIn("deficit", weekly["secondaryText"])
        self.assertIn("Runs out", weekly["secondaryText"])

    def test_session_pace_secondary_text_can_show_reserve_and_lasts_until_reset(self):
        now = datetime.now(timezone.utc)
        state = AppState(
            providers=[
                ProviderState(
                    id="claude",
                    display_name="Claude Code",
                    installed=True,
                    enabled=True,
                    source="oauth",
                    primary_metric=MetricWindow(
                        "5h", 30, (now + timedelta(hours=2)).isoformat()
                    ),
                    secondary_metric=MetricWindow(
                        "7d", 2, (now + timedelta(days=6, hours=23)).isoformat()
                    ),
                )
            ],
            overview_provider_ids=[],
            updated_at=now.isoformat(),
        )

        payload = build_popup_view_model(state, refresh_interval_seconds=60)
        provider = payload["popup"]["providers"][0]
        session = provider["metrics"][0]

        self.assertTrue(session["available"])
        self.assertIsNotNone(session["secondaryText"])
        self.assertIn("Pace:", session["secondaryText"])
        self.assertIn("reserve", session["secondaryText"])
        self.assertIn("Lasts until reset", session["secondaryText"])

    def test_pace_secondary_text_is_hidden_at_window_start(self):
        now = datetime.now(timezone.utc)
        state = AppState(
            providers=[
                ProviderState(
                    id="copilot",
                    display_name="GitHub Copilot",
                    installed=True,
                    enabled=True,
                    source="api",
                    primary_metric=MetricWindow(
                        "5h", 84, (now + timedelta(hours=4, minutes=57)).isoformat()
                    ),
                )
            ],
            overview_provider_ids=[],
            updated_at=now.isoformat(),
        )

        payload = build_popup_view_model(state, refresh_interval_seconds=60)
        provider = payload["popup"]["providers"][0]
        session = provider["metrics"][0]

        self.assertTrue(session["available"])
        self.assertIsNone(session["secondaryText"])

    def test_actions_are_canonical_with_full_contract_fields(self):
        state = AppState(
            providers=[
                ProviderState(
                    id="unknown_provider",
                    display_name="Unknown Provider",
                    installed=True,
                    enabled=True,
                )
            ],
            overview_provider_ids=[],
            updated_at="2099-01-01T00:00:00+00:00",
        )

        payload = build_popup_view_model(state, refresh_interval_seconds=60)
        provider = payload["popup"]["providers"][0]
        actions = provider["actions"]
        expected_ids = ["usage_dashboard", "status_page", "settings", "about", "quit"]

        self.assertEqual([action["id"] for action in actions], expected_ids)
        for action in actions:
            self.assertIn("label", action)
            self.assertIn("enabled", action)
            self.assertIn("visible", action)
            self.assertIn("intent", action)
            self.assertIn("target", action)

        usage = actions[0]
        status = actions[1]
        settings = actions[2]
        about = actions[3]
        quit_action = actions[4]

        self.assertEqual(usage["intent"], "open_url")
        self.assertFalse(usage["enabled"])
        self.assertIsNone(usage["target"])

        self.assertEqual(status["intent"], "open_url")
        self.assertFalse(status["enabled"])
        self.assertIsNone(status["target"])

        self.assertEqual(settings["intent"], "open_settings")
        self.assertTrue(settings["enabled"])
        self.assertIsNone(settings["target"])

        self.assertEqual(about["intent"], "about")
        self.assertTrue(about["enabled"])
        self.assertEqual(
            about["target"], "https://github.com/KodyMike/ai_usage_monitor"
        )

        self.assertEqual(quit_action["intent"], "quit")
        self.assertTrue(quit_action["enabled"])
        self.assertIsNone(quit_action["target"])

    def test_identity_change_marks_refresh_pending_and_uses_refreshing_copy(self):
        state = AppState(
            providers=[
                ProviderState(
                    id="codex",
                    display_name="OpenAI Codex",
                    installed=True,
                    enabled=True,
                    source="cli",
                    primary_metric=None,
                    secondary_metric=None,
                    metadata={"identity": {"changed": True}},
                    extras={"identityChanged": True},
                )
            ],
            overview_provider_ids=[],
            updated_at="2099-01-01T00:00:00+00:00",
        )

        payload = build_popup_view_model(state, refresh_interval_seconds=60)
        popup = payload["popup"]
        provider = popup["providers"][0]
        session = provider["metrics"][0]
        weekly = provider["metrics"][1]

        self.assertTrue(popup["identityRefreshPending"])
        self.assertEqual(provider["identity"]["changed"], True)
        self.assertEqual(session["leftText"], "Switching account/source")
        self.assertEqual(
            session["secondaryText"], "Refreshing usage for active identity"
        )
        self.assertEqual(session["tone"], "warn")
        self.assertEqual(weekly["leftText"], "Switching account/source")
        self.assertTrue(provider["switchingState"]["active"])
        self.assertEqual(
            provider["switchingState"]["title"], "Switching account/source"
        )
        self.assertEqual(
            provider["switchingState"]["message"],
            "Refreshing usage for active identity",
        )

    def test_popup_active_identity_is_exposed_for_selected_provider(self):
        state = AppState(
            providers=[
                ProviderState(
                    id="claude",
                    display_name="Claude Code",
                    installed=True,
                    enabled=True,
                    source="oauth",
                    primary_metric=MetricWindow("5h", 22, "2099-01-01T00:00:00+00:00"),
                    metadata={
                        "identity": {
                            "providerId": "claude",
                            "sourceId": "oauth",
                            "sourceMode": "local_cli",
                            "accountId": "team-123",
                            "sessionId": "sess-1",
                            "accountFingerprint": "accfp-1",
                            "stateKey": "claude:accfp-1:local_cli",
                            "stateFingerprint": "abc123fingerprint",
                            "fingerprint": "abc123fingerprint",
                            "changed": False,
                        }
                    },
                    extras={
                        "identityFingerprint": "abc123fingerprint",
                        "accountFingerprint": "accfp-1",
                        "stateIdentityKey": "claude:accfp-1:local_cli",
                        "sourceMode": "local_cli",
                    },
                )
            ],
            overview_provider_ids=[],
            updated_at="2099-01-01T00:00:00+00:00",
        )

        payload = build_popup_view_model(
            state, refresh_interval_seconds=60, preferred_provider_id="claude"
        )
        popup = payload["popup"]
        provider = popup["providers"][0]

        self.assertEqual(popup["activeIdentityFingerprint"], "abc123fingerprint")
        self.assertEqual(popup["activeIdentity"]["accountId"], "team-123")
        self.assertEqual(provider["identityFingerprint"], "abc123fingerprint")
        self.assertEqual(provider["accountFingerprint"], "accfp-1")
        self.assertEqual(provider["sourceMode"], "local_cli")
        self.assertEqual(provider["stateIdentityKey"], "claude:accfp-1:local_cli")
        self.assertFalse(provider["switchingState"]["active"])

    def test_switching_state_does_not_fallback_to_zero_usage(self):
        state = AppState(
            providers=[
                ProviderState(
                    id="codex",
                    display_name="OpenAI Codex",
                    installed=True,
                    enabled=True,
                    source="cli",
                    primary_metric=None,
                    secondary_metric=None,
                    metadata={"identity": {"changed": True, "fingerprint": "new-fp"}},
                    extras={"identityChanged": True, "identityFingerprint": "new-fp"},
                )
            ],
            overview_provider_ids=[],
            updated_at="2099-01-01T00:00:00+00:00",
        )

        payload = build_popup_view_model(state, refresh_interval_seconds=60)
        provider = payload["popup"]["providers"][0]
        session = provider["metrics"][0]
        weekly = provider["metrics"][1]

        self.assertEqual(provider["switchingState"]["active"], True)
        self.assertIsNone(session["percent"])
        self.assertEqual(session["leftText"], "Switching account/source")
        self.assertEqual(session["rightText"], "…")
        self.assertEqual(weekly["leftText"], "Switching account/source")
        self.assertNotEqual(session["leftText"], "0% used")

    def test_switching_state_uses_account_specific_copy_when_account_changes(self):
        state = AppState(
            providers=[
                ProviderState(
                    id="codex",
                    display_name="OpenAI Codex",
                    installed=True,
                    enabled=True,
                    source="cli",
                    primary_metric=None,
                    secondary_metric=None,
                    metadata={"identity": {"changed": True, "accountChanged": True}},
                    extras={"identityChanged": True, "accountSwitched": True},
                )
            ],
            overview_provider_ids=[],
            updated_at="2099-01-01T00:00:00+00:00",
        )

        payload = build_popup_view_model(state, refresh_interval_seconds=60)
        provider = payload["popup"]["providers"][0]
        session = provider["metrics"][0]

        self.assertEqual(provider["switchingState"]["kind"], "account")
        self.assertEqual(provider["switchingState"]["title"], "Account switched")
        self.assertEqual(
            provider["switchingState"]["message"], "Refreshing usage for active account"
        )
        self.assertEqual(session["leftText"], "Account switched")
        self.assertEqual(
            session["secondaryText"], "Refreshing usage for active account"
        )

    def test_popup_provider_exposes_source_presentation_fields(self):
        source_model = {
            "canonicalMode": "hybrid",
            "providerCapabilities": {
                "supportsLocalCli": True,
                "supportsApi": True,
                "supportsWeb": False,
            },
            "sourceStrategy": {
                "preferredSource": "cli",
                "resolvedSource": "api",
                "fallbackReason": "unavailable",
                "resolutionReason": "preferred_source_unavailable",
                "fallbackActive": True,
            },
            "availability": {
                "localToolInstalled": False,
                "apiKeyPresent": True,
                "authValid": True,
                "rateLimitState": "ok",
            },
            "sourceLabel": "Hybrid",
            "activeSource": "api",
            "fallbackState": {"active": True},
            "sourceDetails": "Preferred CLI · Active API · Fallback active",
        }
        state = AppState(
            providers=[
                ProviderState(
                    id="opencode",
                    display_name="OpenCode",
                    installed=True,
                    enabled=True,
                    source="api",
                    source_model=source_model,
                )
            ],
            overview_provider_ids=[],
            updated_at="2099-01-01T00:00:00+00:00",
        )
        payload = build_popup_view_model(state, refresh_interval_seconds=60)
        provider = payload["popup"]["providers"][0]
        source_presentation = provider["sourcePresentation"]

        self.assertEqual(source_presentation["modeLabel"], "Hybrid")
        self.assertEqual(source_presentation["activeSourceLabel"], "Fallback")
        self.assertIn("Fallback active", source_presentation["statusTags"])
        self.assertEqual(
            source_presentation["unavailableReason"]["code"], "source_switched"
        )

    def test_source_presentation_active_source_label_is_canonical(self):
        state = AppState(
            providers=[
                ProviderState(
                    id="codex",
                    display_name="OpenAI Codex",
                    installed=True,
                    enabled=True,
                    source="cli",
                    source_model={
                        "canonicalMode": "local_cli",
                        "sourceLabel": "Local CLI",
                        "sourceStrategy": {
                            "resolvedSource": "cli",
                            "fallbackActive": False,
                        },
                        "providerCapabilities": {
                            "supportsLocalCli": True,
                            "supportsApi": True,
                            "supportsWeb": False,
                        },
                        "availability": {
                            "localToolInstalled": True,
                            "apiConfigured": True,
                            "authValid": True,
                        },
                    },
                ),
                ProviderState(
                    id="openrouter",
                    display_name="OpenRouter",
                    installed=False,
                    enabled=True,
                    source="api",
                    source_model={
                        "canonicalMode": "unavailable",
                        "sourceLabel": "Unavailable",
                        "sourceStrategy": {
                            "resolvedSource": "api",
                            "fallbackActive": False,
                        },
                        "providerCapabilities": {
                            "supportsLocalCli": False,
                            "supportsApi": True,
                            "supportsWeb": False,
                        },
                        "availability": {"apiConfigured": False, "authValid": False},
                    },
                ),
            ],
            overview_provider_ids=[],
            updated_at="2099-01-01T00:00:00+00:00",
        )

        payload = build_popup_view_model(state, refresh_interval_seconds=60)
        by_id = {provider["id"]: provider for provider in payload["popup"]["providers"]}

        self.assertEqual(
            by_id["codex"]["sourcePresentation"]["activeSourceLabel"], "Local CLI"
        )
        self.assertEqual(
            by_id["openrouter"]["sourcePresentation"]["activeSourceLabel"],
            "Unavailable",
        )

    def test_popup_provider_exposes_incident_status_separately_from_refresh_failure(
        self,
    ):
        state = AppState(
            providers=[
                ProviderState(
                    id="codex",
                    display_name="OpenAI Codex",
                    installed=True,
                    enabled=True,
                    source="cli",
                    primary_metric=MetricWindow("5h", 22, "2099-01-01T00:00:00+00:00"),
                    incident={
                        "indicator": "major",
                        "description": "API latency elevated in multiple regions.",
                        "url": "https://status.openai.com/",
                    },
                )
            ],
            overview_provider_ids=[],
            updated_at="2099-01-01T00:00:00+00:00",
        )

        payload = build_popup_view_model(state, refresh_interval_seconds=60)
        provider = payload["popup"]["providers"][0]
        status_state = provider["statusState"]
        status_presentation = provider["statusPresentation"]

        self.assertTrue(status_state["incidentActive"])
        self.assertEqual(status_state["summary"], "Service disruption")
        self.assertEqual(status_state["tone"], "warn")
        self.assertEqual(provider["errorState"]["hasError"], False)
        self.assertEqual(status_presentation["visible"], True)
        self.assertEqual(status_presentation["badgeLabel"], "Service disruption")
        self.assertIn("latency", status_presentation["details"].lower())
        self.assertEqual(provider["links"]["statusUrl"], "https://status.openai.com/")
        self.assertEqual(provider["actions"][1]["id"], "status_page")
        self.assertEqual(provider["actions"][1]["target"], "https://status.openai.com/")

    def test_popup_status_state_keeps_source_issue_separate(self):
        state = AppState(
            providers=[
                ProviderState(
                    id="openrouter",
                    display_name="OpenRouter",
                    installed=True,
                    enabled=True,
                    source="api",
                    source_model={
                        "canonicalMode": "api",
                        "sourceLabel": "API",
                        "sourceStrategy": {
                            "resolvedSource": "api",
                            "fallbackActive": False,
                        },
                        "providerCapabilities": {
                            "supportsLocalCli": False,
                            "supportsApi": True,
                            "supportsWeb": False,
                        },
                        "availability": {
                            "apiConfigured": False,
                            "apiKeyPresent": False,
                            "authValid": True,
                        },
                    },
                )
            ],
            overview_provider_ids=[],
            updated_at="2099-01-01T00:00:00+00:00",
        )

        payload = build_popup_view_model(state, refresh_interval_seconds=60)
        provider = payload["popup"]["providers"][0]
        status_state = provider["statusState"]

        self.assertFalse(status_state["incidentActive"])
        self.assertTrue(status_state["sourceIssue"])
        self.assertFalse(provider["statusPresentation"]["visible"])
        self.assertTrue(provider["errorState"]["hasError"])

    def test_overview_selection_is_independent_from_enabled_provider_tabs(self):
        state = AppState(
            providers=[
                ProviderState(
                    id="codex",
                    display_name="OpenAI Codex",
                    installed=True,
                    enabled=True,
                    source="cli",
                    primary_metric=MetricWindow("5h", 12, "2099-01-01T00:00:00+00:00"),
                ),
                ProviderState(
                    id="claude",
                    display_name="Claude Code",
                    installed=True,
                    enabled=False,
                    source="oauth",
                    primary_metric=MetricWindow("5h", 55, "2099-01-01T00:00:00+00:00"),
                ),
            ],
            overview_provider_ids=["claude"],
            updated_at="2099-01-01T00:00:01+00:00",
        )

        payload = build_popup_view_model(state, refresh_interval_seconds=60)
        popup = payload["popup"]
        provider_tab_ids = [
            tab["id"] for tab in popup["tabs"] if tab["kind"] == "provider"
        ]
        overview_card_ids = [card["providerId"] for card in popup["overviewCards"]]

        self.assertEqual(provider_tab_ids, ["codex"])
        self.assertEqual(popup["enabledProviderIds"], ["codex"])
        self.assertEqual(popup["overviewProviderIds"], ["claude"])
        self.assertEqual(overview_card_ids, ["claude"])

    def test_popup_vm_exposes_switcher_tabs_from_core(self):
        state = AppState(
            providers=[
                ProviderState(
                    id="codex",
                    display_name="OpenAI Codex",
                    installed=True,
                    enabled=True,
                    source="cli",
                    primary_metric=MetricWindow("5h", 12, "2099-01-01T00:00:00+00:00"),
                ),
                ProviderState(
                    id="claude",
                    display_name="Claude Code",
                    installed=True,
                    enabled=True,
                    source="oauth",
                    primary_metric=MetricWindow("5h", 33, "2099-01-01T00:00:00+00:00"),
                ),
            ],
            overview_provider_ids=["codex", "claude"],
            updated_at="2099-01-01T00:00:01+00:00",
        )

        payload = build_popup_view_model(state, refresh_interval_seconds=60)
        popup = payload["popup"]
        tab_ids = [tab["id"] for tab in popup["tabs"]]
        switcher_ids = [tab["id"] for tab in popup["switcherTabs"]]

        self.assertEqual(switcher_ids, tab_ids)
        self.assertEqual(popup["selectableProviderIds"], popup["providerOrder"])

    def test_popup_vm_exposes_panel_indicator_contract(self):
        state = AppState(
            providers=[
                ProviderState(
                    id="codex",
                    display_name="OpenAI Codex",
                    installed=True,
                    enabled=True,
                    source="cli",
                    primary_metric=MetricWindow("5h", 91, "2099-01-01T00:00:00+00:00"),
                    incident={
                        "indicator": "major",
                        "description": "Service disruption",
                        "url": "https://status.openai.com/",
                    },
                )
            ],
            overview_provider_ids=[],
            updated_at="2099-01-01T00:00:01+00:00",
        )

        payload = build_popup_view_model(state, refresh_interval_seconds=60)
        panel = payload["popup"]["panel"]

        self.assertEqual(panel["providerId"], "codex")
        self.assertEqual(panel["displayText"], "91%")
        self.assertEqual(panel["tone"], "warn")
        self.assertIsInstance(panel["tooltipLines"], list)
        self.assertTrue(any("Resets in" in line for line in panel["tooltipLines"]))


if __name__ == "__main__":
    unittest.main()
