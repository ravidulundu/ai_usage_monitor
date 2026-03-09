import unittest

from core.ai_usage_monitor.providers.base import ProviderDescriptor
from core.ai_usage_monitor.source_strategy import resolve_provider_source_plan


class SourceStrategyTests(unittest.TestCase):
    def test_auto_policy_builds_fallback_chain_for_hybrid_provider(self):
        descriptor = ProviderDescriptor(
            id="opencode",
            display_name="OpenCode",
            source_modes=("auto", "cli", "web"),
            preferred_source_policy="local_first",
        )

        plan = resolve_provider_source_plan(descriptor, settings={"source": "auto"})
        self.assertEqual(plan["preferredSource"], "auto")
        self.assertEqual(plan["resolvedSourceHint"], "cli")
        self.assertEqual(plan["fallbackChain"], ["web", "probe"])
        self.assertEqual(plan["supportsProbe"], True)
        self.assertEqual(plan["resolutionReason"], "policy_chain")

    def test_explicit_source_keeps_policy_fallback_chain(self):
        descriptor = ProviderDescriptor(
            id="kilo",
            display_name="Kilo",
            source_modes=("auto", "api", "cli"),
            preferred_source_policy="api_first",
        )

        plan = resolve_provider_source_plan(descriptor, settings={"source": "cli"})
        self.assertEqual(plan["preferredSource"], "cli")
        self.assertEqual(plan["resolvedSourceHint"], "cli")
        self.assertIn("api", plan["fallbackChain"])
        self.assertEqual(plan["resolutionReason"], "explicit_source")

    def test_explicit_local_cli_prefers_local_then_remote_fallback(self):
        descriptor = ProviderDescriptor(
            id="kilo",
            display_name="Kilo",
            source_modes=("auto", "api", "cli"),
            preferred_source_policy="local_first",
        )

        plan = resolve_provider_source_plan(
            descriptor, settings={"source": "local_cli"}
        )
        self.assertEqual(plan["preferredSource"], "local_cli")
        self.assertEqual(plan["resolvedSourceHint"], "cli")
        self.assertEqual(plan["fallbackChain"], ["api", "probe"])
        self.assertEqual(plan["resolutionReason"], "explicit_local_first")

    def test_single_source_provider_has_no_probe_or_fallback(self):
        descriptor = ProviderDescriptor(
            id="openrouter",
            display_name="OpenRouter",
            source_modes=("api",),
            preferred_source_policy="api_first",
        )

        plan = resolve_provider_source_plan(descriptor, settings={})
        self.assertEqual(plan["preferredSource"], "api")
        self.assertEqual(plan["resolvedSourceHint"], "api")
        self.assertEqual(plan["fallbackChain"], [])
        self.assertEqual(plan["supportsProbe"], False)

    def test_legacy_remote_source_normalizes_to_web(self):
        descriptor = ProviderDescriptor(
            id="amp",
            display_name="Amp",
            source_modes=("auto", "web"),
            preferred_source_policy="web_first",
        )

        plan = resolve_provider_source_plan(descriptor, settings={"source": "remote"})
        self.assertEqual(plan["preferredSource"], "web")
        self.assertEqual(plan["resolvedSourceHint"], "web")


if __name__ == "__main__":
    unittest.main()
