import unittest
from unittest import mock

from core.ai_usage_monitor.collector import collect_all
from core.ai_usage_monitor.models import ProviderState


class CollectorTests(unittest.TestCase):
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
            return {}, ProviderState(id="codex", display_name="OpenAI Codex", installed=True)

        with mock.patch("core.ai_usage_monitor.collector.load_config", return_value={"providers": [{"id": "codex", "enabled": False, "source": "auto"}]}):
            with mock.patch("core.ai_usage_monitor.collector.provider_settings_map", return_value={"codex": {"id": "codex", "enabled": False, "source": "auto"}}):
                with mock.patch("core.ai_usage_monitor.collector.ProviderRegistry") as registry_cls:
                    registry_cls.return_value.list_descriptors.return_value = [fake_descriptor]
                    with mock.patch.dict("core.ai_usage_monitor.collector.COLLECTORS", {"codex": fake_collector}, clear=True):
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
            return {}, ProviderState(id="minimax", display_name="MiniMax", installed=True, source="web")

        with mock.patch("core.ai_usage_monitor.collector.load_config", return_value={"providers": [{"id": "minimax", "enabled": True, "source": "auto"}]}):
            with mock.patch("core.ai_usage_monitor.collector.provider_settings_map", return_value={"minimax": {"id": "minimax", "enabled": True, "source": "auto"}}):
                with mock.patch("core.ai_usage_monitor.collector.ProviderRegistry") as registry_cls:
                    registry_cls.return_value.list_descriptors.return_value = [fake_descriptor]
                    with mock.patch.dict("core.ai_usage_monitor.collector.COLLECTORS", {"minimax": fake_collector}, clear=True):
                        _, app_state = collect_all()

        provider = app_state.providers[0]
        self.assertEqual(provider.source, "web")
        self.assertEqual(provider.metadata["configuredSource"], "auto")


if __name__ == "__main__":
    unittest.main()
