import unittest
import tempfile
import os
from unittest import mock

from core.ai_usage_monitor.collector import collect_all
from core.ai_usage_monitor.identity import load_identity_store
from core.ai_usage_monitor.models import MetricWindow, ProviderState


class CollectorTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._env_patch = mock.patch.dict(
            os.environ,
            {"AI_USAGE_MONITOR_STATE_DIR": self._tmp.name},
            clear=False,
        )
        self._env_patch.start()

    def tearDown(self):
        self._env_patch.stop()
        self._tmp.cleanup()

    def test_disabled_provider_is_not_collected(self):
        fake_descriptor = mock.Mock()
        fake_descriptor.id = "codex"
        fake_descriptor.display_name = "OpenAI Codex"
        fake_descriptor.default_enabled = True
        fake_descriptor.source_modes = ("auto",)
        fake_descriptor.branding.to_dict.return_value = {"iconKey": "codex"}

        collector_called = False

        def fake_collector(_settings):
            nonlocal collector_called
            collector_called = True
            return {}, ProviderState(
                id="codex", display_name="OpenAI Codex", installed=True
            )

        with mock.patch(
            "core.ai_usage_monitor.collector.load_config",
            return_value={
                "providers": [{"id": "codex", "enabled": False, "source": "auto"}]
            },
        ):
            with mock.patch(
                "core.ai_usage_monitor.collector.provider_settings_map",
                return_value={
                    "codex": {"id": "codex", "enabled": False, "source": "auto"}
                },
            ):
                with mock.patch(
                    "core.ai_usage_monitor.collector.ProviderRegistry"
                ) as registry_cls:
                    registry_cls.return_value.list_descriptors.return_value = [
                        fake_descriptor
                    ]
                    with mock.patch.dict(
                        "core.ai_usage_monitor.collector.COLLECTORS",
                        {"codex": fake_collector},
                        clear=True,
                    ):
                        legacy, app_state = collect_all()

        self.assertFalse(collector_called)
        self.assertEqual(legacy["codex"]["enabled"], False)
        self.assertEqual(len(app_state.providers), 1)
        provider = app_state.providers[0]
        self.assertFalse(provider.enabled)
        self.assertEqual(provider.status, "disabled")
        self.assertEqual(provider.metadata["configuredSource"], "auto")

    def test_effective_source_is_preserved_and_configured_source_goes_to_metadata(self):
        fake_descriptor = mock.Mock()
        fake_descriptor.id = "minimax"
        fake_descriptor.display_name = "MiniMax"
        fake_descriptor.default_enabled = True
        fake_descriptor.source_modes = ("auto", "web", "api")
        fake_descriptor.branding.to_dict.return_value = {"iconKey": "minimax"}

        def fake_collector(_settings):
            return {}, ProviderState(
                id="minimax", display_name="MiniMax", installed=True, source="web"
            )

        with mock.patch(
            "core.ai_usage_monitor.collector.load_config",
            return_value={
                "providers": [{"id": "minimax", "enabled": True, "source": "auto"}]
            },
        ):
            with mock.patch(
                "core.ai_usage_monitor.collector.provider_settings_map",
                return_value={
                    "minimax": {"id": "minimax", "enabled": True, "source": "auto"}
                },
            ):
                with mock.patch(
                    "core.ai_usage_monitor.collector.ProviderRegistry"
                ) as registry_cls:
                    registry_cls.return_value.list_descriptors.return_value = [
                        fake_descriptor
                    ]
                    with mock.patch.dict(
                        "core.ai_usage_monitor.collector.COLLECTORS",
                        {"minimax": fake_collector},
                        clear=True,
                    ):
                        _, app_state = collect_all()

        provider = app_state.providers[0]
        self.assertEqual(provider.source, "web")
        self.assertEqual(provider.metadata["configuredSource"], "auto")

    def test_provider_source_model_is_populated(self):
        fake_descriptor = mock.Mock()
        fake_descriptor.id = "opencode"
        fake_descriptor.display_name = "OpenCode"
        fake_descriptor.default_enabled = True
        fake_descriptor.source_modes = ("auto", "cli", "web")
        fake_descriptor.config_fields = ()
        fake_descriptor.branding.to_dict.return_value = {"iconKey": "opencode"}

        def fake_collector(_settings):
            return (
                {},
                ProviderState(
                    id="opencode",
                    display_name="OpenCode",
                    installed=True,
                    authenticated=True,
                    source="cli",
                ),
            )

        with mock.patch(
            "core.ai_usage_monitor.collector.load_config",
            return_value={
                "providers": [{"id": "opencode", "enabled": True, "source": "auto"}]
            },
        ):
            with mock.patch(
                "core.ai_usage_monitor.collector.provider_settings_map",
                return_value={
                    "opencode": {"id": "opencode", "enabled": True, "source": "auto"}
                },
            ):
                with mock.patch(
                    "core.ai_usage_monitor.collector.ProviderRegistry"
                ) as registry_cls:
                    registry_cls.return_value.list_descriptors.return_value = [
                        fake_descriptor
                    ]
                    with mock.patch.dict(
                        "core.ai_usage_monitor.collector.COLLECTORS",
                        {"opencode": fake_collector},
                        clear=True,
                    ):
                        _, app_state = collect_all()

        provider = app_state.providers[0]
        source_model = provider.source_model
        self.assertEqual(source_model["preferredSource"], "auto")
        self.assertEqual(source_model["activeSource"], "cli")
        self.assertEqual(source_model["canonicalMode"], "hybrid")
        self.assertEqual(source_model["authState"], "authenticated")
        self.assertIn("cli", source_model["availableSources"])
        self.assertTrue(source_model["providerCapabilities"]["supportsLocalCli"])
        self.assertFalse(source_model["providerCapabilities"]["supportsApi"])
        self.assertTrue(source_model["providerCapabilities"]["supportsWeb"])
        self.assertEqual(source_model["sourceStrategy"]["preferredSource"], "auto")
        self.assertEqual(source_model["sourceStrategy"]["resolvedSource"], "cli")
        self.assertEqual(
            source_model["sourceStrategy"]["fallbackReason"], "auto_selected"
        )
        self.assertTrue(source_model["availability"]["localToolInstalled"])
        self.assertTrue(source_model["availability"]["authValid"])
        settings_presentation = source_model["settingsPresentation"]
        self.assertIn("sourceModeLabel", settings_presentation)
        self.assertIn("activeSourceLabel", settings_presentation)
        self.assertIn("sourceStatusLabel", settings_presentation)
        self.assertIn("fallbackLabel", settings_presentation)
        self.assertIn("availabilityLabel", settings_presentation)
        self.assertIn("subtitle", settings_presentation)

    def test_local_cli_preferred_source_falls_back_to_remote_when_local_unavailable(
        self,
    ):
        fake_descriptor = mock.Mock()
        fake_descriptor.id = "kilo"
        fake_descriptor.display_name = "Kilo"
        fake_descriptor.default_enabled = True
        fake_descriptor.source_modes = ("auto", "api", "cli")
        fake_descriptor.preferred_source_policy = "local_first"
        fake_descriptor.config_fields = ()
        fake_descriptor.branding.to_dict.return_value = {"iconKey": "kilo"}

        attempted_sources = []

        def fake_collector(settings):
            source = settings.get("source")
            attempted_sources.append(source)
            if source == "cli":
                return {}, ProviderState(
                    id="kilo", display_name="Kilo", installed=False, source="cli"
                )
            return {}, ProviderState(
                id="kilo",
                display_name="Kilo",
                installed=True,
                authenticated=True,
                source="api",
            )

        with mock.patch(
            "core.ai_usage_monitor.collector.load_config",
            return_value={
                "providers": [{"id": "kilo", "enabled": True, "source": "local_cli"}]
            },
        ):
            with mock.patch(
                "core.ai_usage_monitor.collector.provider_settings_map",
                return_value={
                    "kilo": {"id": "kilo", "enabled": True, "source": "local_cli"}
                },
            ):
                with mock.patch(
                    "core.ai_usage_monitor.collector.ProviderRegistry"
                ) as registry_cls:
                    registry_cls.return_value.list_descriptors.return_value = [
                        fake_descriptor
                    ]
                    with mock.patch.dict(
                        "core.ai_usage_monitor.collector.COLLECTORS",
                        {"kilo": fake_collector},
                        clear=True,
                    ):
                        _, app_state = collect_all()

        provider = app_state.providers[0]
        source_model = provider.source_model
        self.assertEqual(attempted_sources[:2], ["cli", "api"])
        self.assertEqual(provider.metadata["configuredSource"], "local_cli")
        self.assertEqual(source_model["preferredSource"], "local_cli")
        self.assertEqual(source_model["resolvedSource"], "api")
        self.assertEqual(source_model["fallbackReason"], "local_unavailable")
        self.assertTrue(source_model["fallbackState"]["active"])

    def test_overview_provider_ids_flow_into_app_state(self):
        fake_descriptor = mock.Mock()
        fake_descriptor.id = "codex"
        fake_descriptor.display_name = "OpenAI Codex"
        fake_descriptor.default_enabled = True
        fake_descriptor.source_modes = ("auto",)
        fake_descriptor.branding.to_dict.return_value = {"iconKey": "codex"}

        def fake_collector(_settings):
            return {}, ProviderState(
                id="codex", display_name="OpenAI Codex", installed=True, source="cli"
            )

        config = {
            "overviewProviderIds": ["codex"],
            "providers": [{"id": "codex", "enabled": True, "source": "auto"}],
        }

        with mock.patch(
            "core.ai_usage_monitor.collector.load_config", return_value=config
        ):
            with mock.patch(
                "core.ai_usage_monitor.collector.provider_settings_map",
                return_value={
                    "codex": {"id": "codex", "enabled": True, "source": "auto"}
                },
            ):
                with mock.patch(
                    "core.ai_usage_monitor.collector.ProviderRegistry"
                ) as registry_cls:
                    registry_cls.return_value.list_descriptors.return_value = [
                        fake_descriptor
                    ]
                    with mock.patch.dict(
                        "core.ai_usage_monitor.collector.COLLECTORS",
                        {"codex": fake_collector},
                        clear=True,
                    ):
                        _, app_state = collect_all()

        self.assertEqual(app_state.overview_provider_ids, ["codex"])

    def test_provider_identity_contains_account_and_fingerprint(self):
        fake_descriptor = mock.Mock()
        fake_descriptor.id = "codex"
        fake_descriptor.display_name = "OpenAI Codex"
        fake_descriptor.default_enabled = True
        fake_descriptor.source_modes = ("auto",)
        fake_descriptor.branding.to_dict.return_value = {"iconKey": "codex"}

        def fake_collector(_settings):
            return (
                {},
                ProviderState(
                    id="codex",
                    display_name="OpenAI Codex",
                    installed=True,
                    source="cli",
                    extras={"accountId": "acc-1"},
                ),
            )

        config = {"providers": [{"id": "codex", "enabled": True, "source": "auto"}]}
        with mock.patch(
            "core.ai_usage_monitor.collector.load_config", return_value=config
        ):
            with mock.patch(
                "core.ai_usage_monitor.collector.provider_settings_map",
                return_value={
                    "codex": {"id": "codex", "enabled": True, "source": "auto"}
                },
            ):
                with mock.patch(
                    "core.ai_usage_monitor.collector.ProviderRegistry"
                ) as registry_cls:
                    registry_cls.return_value.list_descriptors.return_value = [
                        fake_descriptor
                    ]
                    with mock.patch.dict(
                        "core.ai_usage_monitor.collector.COLLECTORS",
                        {"codex": fake_collector},
                        clear=True,
                    ):
                        _, app_state = collect_all()

        provider = app_state.providers[0]
        identity = provider.metadata.get("identity")
        self.assertEqual(identity["providerId"], "codex")
        self.assertEqual(identity["accountId"], "acc-1")
        self.assertTrue(identity["fingerprint"])

    def test_identity_change_forces_same_cycle_refetch(self):
        fake_descriptor = mock.Mock()
        fake_descriptor.id = "codex"
        fake_descriptor.display_name = "OpenAI Codex"
        fake_descriptor.default_enabled = True
        fake_descriptor.source_modes = ("auto",)
        fake_descriptor.branding.to_dict.return_value = {"iconKey": "codex"}

        account = {"id": "acc-1"}
        calls = {"count": 0}

        def fake_collector(_settings):
            calls["count"] += 1
            used = 10 if account["id"] == "acc-1" else 20
            return (
                {},
                ProviderState(
                    id="codex",
                    display_name="OpenAI Codex",
                    installed=True,
                    source="cli",
                    primary_metric=MetricWindow("5h", used, None),
                    extras={"accountId": account["id"]},
                ),
            )

        config = {"providers": [{"id": "codex", "enabled": True, "source": "auto"}]}
        with mock.patch(
            "core.ai_usage_monitor.collector.load_config", return_value=config
        ):
            with mock.patch(
                "core.ai_usage_monitor.collector.provider_settings_map",
                return_value={
                    "codex": {"id": "codex", "enabled": True, "source": "auto"}
                },
            ):
                with mock.patch(
                    "core.ai_usage_monitor.collector.ProviderRegistry"
                ) as registry_cls:
                    registry_cls.return_value.list_descriptors.return_value = [
                        fake_descriptor
                    ]
                    with mock.patch.dict(
                        "core.ai_usage_monitor.collector.COLLECTORS",
                        {"codex": fake_collector},
                        clear=True,
                    ):
                        _, app_state_first = collect_all()
                        account["id"] = "acc-2"
                        _, app_state_second = collect_all()

        first = app_state_first.providers[0]
        second = app_state_second.providers[0]

        self.assertIsNotNone(first.primary_metric)
        self.assertEqual(first.primary_metric.used_pct, 10)
        self.assertIsNotNone(second.primary_metric)
        self.assertEqual(second.primary_metric.used_pct, 20)
        self.assertEqual(calls["count"], 3)
        self.assertEqual(second.metadata.get("identity", {}).get("changed"), False)
        self.assertEqual(
            second.metadata.get("identity", {}).get("refetchedAfterChange"), True
        )

    def test_multi_account_switch_restores_account_snapshot_with_forced_refetch(self):
        fake_descriptor = mock.Mock()
        fake_descriptor.id = "codex"
        fake_descriptor.display_name = "OpenAI Codex"
        fake_descriptor.default_enabled = True
        fake_descriptor.source_modes = ("auto",)
        fake_descriptor.branding.to_dict.return_value = {"iconKey": "codex"}

        account = {"id": "acc-1"}
        calls = {"count": 0}

        def fake_collector(_settings):
            calls["count"] += 1
            used = 10 if account["id"] == "acc-1" else 20
            return (
                {},
                ProviderState(
                    id="codex",
                    display_name="OpenAI Codex",
                    installed=True,
                    source="cli",
                    primary_metric=MetricWindow("5h", used, None),
                    extras={"accountId": account["id"]},
                ),
            )

        config = {"providers": [{"id": "codex", "enabled": True, "source": "auto"}]}
        with mock.patch(
            "core.ai_usage_monitor.collector.load_config", return_value=config
        ):
            with mock.patch(
                "core.ai_usage_monitor.collector.provider_settings_map",
                return_value={
                    "codex": {"id": "codex", "enabled": True, "source": "auto"}
                },
            ):
                with mock.patch(
                    "core.ai_usage_monitor.collector.ProviderRegistry"
                ) as registry_cls:
                    registry_cls.return_value.list_descriptors.return_value = [
                        fake_descriptor
                    ]
                    with mock.patch.dict(
                        "core.ai_usage_monitor.collector.COLLECTORS",
                        {"codex": fake_collector},
                        clear=True,
                    ):
                        _, app_state_first = collect_all()
                        account["id"] = "acc-2"
                        _, app_state_second = collect_all()
                        account["id"] = "acc-1"
                        _, app_state_third = collect_all()

        first = app_state_first.providers[0]
        second = app_state_second.providers[0]
        third = app_state_third.providers[0]
        third_identity = third.metadata.get("identity", {})

        self.assertEqual(first.primary_metric.used_pct, 10)
        self.assertEqual(second.primary_metric.used_pct, 20)
        self.assertEqual(third.primary_metric.used_pct, 10)
        self.assertEqual(calls["count"], 5)
        self.assertEqual(third_identity.get("switched"), False)
        self.assertEqual(third_identity.get("restoredFromSnapshot"), False)
        self.assertEqual(third_identity.get("changed"), False)
        self.assertEqual(third_identity.get("refetchedAfterChange"), True)

    def test_identity_missing_state_is_explicit(self):
        fake_descriptor = mock.Mock()
        fake_descriptor.id = "copilot"
        fake_descriptor.display_name = "GitHub Copilot"
        fake_descriptor.default_enabled = True
        fake_descriptor.source_modes = ("auto", "api")
        fake_descriptor.branding.to_dict.return_value = {"iconKey": "copilot"}

        def fake_collector(_settings):
            return (
                {},
                ProviderState(
                    id="copilot",
                    display_name="GitHub Copilot",
                    installed=True,
                    source="api",
                    primary_metric=MetricWindow("monthly", 30, None),
                ),
            )

        config = {"providers": [{"id": "copilot", "enabled": True, "source": "api"}]}
        with mock.patch(
            "core.ai_usage_monitor.collector.load_config", return_value=config
        ):
            with mock.patch(
                "core.ai_usage_monitor.collector.provider_settings_map",
                return_value={
                    "copilot": {"id": "copilot", "enabled": True, "source": "api"}
                },
            ):
                with mock.patch(
                    "core.ai_usage_monitor.collector.ProviderRegistry"
                ) as registry_cls:
                    registry_cls.return_value.list_descriptors.return_value = [
                        fake_descriptor
                    ]
                    with mock.patch.dict(
                        "core.ai_usage_monitor.collector.COLLECTORS",
                        {"copilot": fake_collector},
                        clear=True,
                    ):
                        _, app_state = collect_all()

        provider = app_state.providers[0]
        identity = provider.metadata.get("identity", {})
        store = load_identity_store()
        provider_store = store.get("providers", {}).get("copilot", {})

        self.assertEqual(identity.get("known"), False)
        self.assertEqual(identity.get("scope"), "provider")
        self.assertEqual(identity.get("confidence"), "low")
        self.assertEqual(provider.extras.get("identityMissing"), True)
        self.assertEqual(provider_store.get("identityKnown"), False)
        self.assertEqual(provider_store.get("snapshots"), {})

    def test_refresh_pipeline_handles_rapid_account_switches(self):
        fake_descriptor = mock.Mock()
        fake_descriptor.id = "codex"
        fake_descriptor.display_name = "OpenAI Codex"
        fake_descriptor.default_enabled = True
        fake_descriptor.source_modes = ("auto",)
        fake_descriptor.branding.to_dict.return_value = {"iconKey": "codex"}

        account = {"id": "acc-1", "pct": 95}
        calls = {"count": 0}

        def fake_collector(_settings):
            calls["count"] += 1
            return (
                {},
                ProviderState(
                    id="codex",
                    display_name="OpenAI Codex",
                    installed=True,
                    source="cli",
                    primary_metric=MetricWindow("5h", account["pct"], None),
                    extras={"accountId": account["id"]},
                ),
            )

        config = {"providers": [{"id": "codex", "enabled": True, "source": "auto"}]}
        with mock.patch(
            "core.ai_usage_monitor.collector.load_config", return_value=config
        ):
            with mock.patch(
                "core.ai_usage_monitor.collector.provider_settings_map",
                return_value={
                    "codex": {"id": "codex", "enabled": True, "source": "auto"}
                },
            ):
                with mock.patch(
                    "core.ai_usage_monitor.collector.ProviderRegistry"
                ) as registry_cls:
                    registry_cls.return_value.list_descriptors.return_value = [
                        fake_descriptor
                    ]
                    with mock.patch.dict(
                        "core.ai_usage_monitor.collector.COLLECTORS",
                        {"codex": fake_collector},
                        clear=True,
                    ):
                        _, s1 = collect_all()
                        account.update({"id": "acc-2", "pct": 12})
                        _, s2 = collect_all()
                        account.update({"id": "acc-3", "pct": 27})
                        _, s3 = collect_all()

        p1 = s1.providers[0]
        p2 = s2.providers[0]
        p3 = s3.providers[0]
        self.assertEqual(p1.primary_metric.used_pct, 95)
        self.assertEqual(p2.primary_metric.used_pct, 12)
        self.assertEqual(p3.primary_metric.used_pct, 27)
        self.assertEqual(calls["count"], 5)
        self.assertEqual(p2.metadata["identity"]["changed"], False)
        self.assertEqual(p3.metadata["identity"]["changed"], False)
        self.assertEqual(p2.metadata["identity"]["refetchedAfterChange"], True)
        self.assertEqual(p3.metadata["identity"]["refetchedAfterChange"], True)


if __name__ == "__main__":
    unittest.main()
