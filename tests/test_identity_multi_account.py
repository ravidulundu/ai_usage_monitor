import unittest

from core.ai_usage_monitor.identity import apply_identity_to_provider
from core.ai_usage_monitor.models import MetricWindow, ProviderState


class IdentityMultiAccountTests(unittest.TestCase):
    def _provider(
        self,
        *,
        account_id: str | None = None,
        session_id: str | None = None,
        used_pct: int = 50,
        source: str = "cli",
    ) -> ProviderState:
        extras = {}
        if account_id is not None:
            extras["accountId"] = account_id
        if session_id is not None:
            extras["sessionId"] = session_id
        return ProviderState(
            id="codex",
            display_name="OpenAI Codex",
            installed=True,
            enabled=True,
            source=source,
            primary_metric=MetricWindow("5h", used_pct, None),
            extras=extras,
        )

    def test_account_switch_without_snapshot_invalidates_previous_account_metrics(self):
        store = {"version": 1, "providers": {}}

        provider_a = self._provider(account_id="acc-a", used_pct=91)
        changed_a = apply_identity_to_provider(
            provider_a, {}, configured_source="auto", store=store
        )
        self.assertFalse(changed_a)
        self.assertEqual(provider_a.primary_metric.used_pct, 91)

        provider_b = self._provider(account_id="acc-b", used_pct=12)
        changed_b = apply_identity_to_provider(
            provider_b, {}, configured_source="auto", store=store
        )

        self.assertTrue(changed_b)
        self.assertIsNone(provider_b.primary_metric)
        self.assertTrue(provider_b.metadata["identity"]["switched"])
        self.assertTrue(provider_b.metadata["identity"]["accountChanged"])
        self.assertEqual(provider_b.metadata["identity"]["sourceChanged"], False)
        self.assertFalse(provider_b.metadata["identity"]["restoredFromSnapshot"])
        self.assertEqual(provider_b.extras["identityChanged"], True)
        self.assertEqual(provider_b.extras["sourceMode"], "local_cli")
        self.assertEqual(
            provider_b.extras["stateIdentityKey"],
            provider_b.metadata["identity"]["stateKey"],
        )

    def test_switch_back_restores_cached_snapshot_for_previous_account(self):
        store = {"version": 1, "providers": {}}

        provider_a = self._provider(account_id="acc-a", used_pct=88)
        apply_identity_to_provider(
            provider_a, {}, configured_source="auto", store=store
        )

        provider_b = self._provider(account_id="acc-b", used_pct=20)
        apply_identity_to_provider(
            provider_b, {}, configured_source="auto", store=store
        )
        provider_b_refetch = self._provider(account_id="acc-b", used_pct=20)
        apply_identity_to_provider(
            provider_b_refetch, {}, configured_source="auto", store=store
        )

        provider_a_back = self._provider(account_id="acc-a", used_pct=33)
        changed = apply_identity_to_provider(
            provider_a_back, {}, configured_source="auto", store=store
        )

        self.assertFalse(changed)
        self.assertEqual(provider_a_back.primary_metric.used_pct, 88)
        self.assertTrue(provider_a_back.metadata["identity"]["switched"])
        self.assertTrue(provider_a_back.metadata["identity"]["restoredFromSnapshot"])
        self.assertEqual(provider_a_back.extras["accountSnapshotRestored"], True)

    def test_identity_temporarily_unavailable_is_explicit_and_invalidates(self):
        store = {"version": 1, "providers": {}}

        provider_known = self._provider(account_id="acc-a", used_pct=40)
        apply_identity_to_provider(
            provider_known, {}, configured_source="auto", store=store
        )

        provider_unknown = self._provider(account_id=None, used_pct=17)
        changed = apply_identity_to_provider(
            provider_unknown, {}, configured_source="auto", store=store
        )
        identity = provider_unknown.metadata["identity"]

        self.assertTrue(changed)
        self.assertFalse(identity["known"])
        self.assertEqual(identity["scope"], "provider")
        self.assertEqual(identity["confidence"], "low")
        self.assertEqual(provider_unknown.extras["identityMissing"], True)
        self.assertIsNone(provider_unknown.primary_metric)

    def test_session_change_under_same_account_produces_distinct_account_state_keys(
        self,
    ):
        store = {"version": 1, "providers": {}}

        provider_s1 = self._provider(
            account_id="acc-a", session_id="session-1", used_pct=55
        )
        apply_identity_to_provider(
            provider_s1, {}, configured_source="auto", store=store
        )
        key_s1 = provider_s1.extras["accountStateKey"]

        provider_s2 = self._provider(
            account_id="acc-a", session_id="session-2", used_pct=10
        )
        changed = apply_identity_to_provider(
            provider_s2, {}, configured_source="auto", store=store
        )
        key_s2 = provider_s2.extras["accountStateKey"]

        self.assertTrue(changed)
        self.assertNotEqual(key_s1, key_s2)
        self.assertTrue(provider_s2.metadata["identity"]["switched"])
        self.assertTrue(provider_s2.metadata["identity"]["accountChanged"])
        self.assertIsNone(provider_s2.primary_metric)

    def test_source_change_under_same_account_uses_distinct_state_key_and_invalidates(
        self,
    ):
        store = {"version": 1, "providers": {}}

        provider_cli = self._provider(account_id="acc-a", source="cli", used_pct=55)
        apply_identity_to_provider(
            provider_cli, {}, configured_source="cli", store=store
        )
        key_cli = provider_cli.extras["stateIdentityKey"]

        provider_api = self._provider(account_id="acc-a", source="api", used_pct=20)
        changed = apply_identity_to_provider(
            provider_api, {}, configured_source="api", store=store
        )
        key_api = provider_api.extras["stateIdentityKey"]

        self.assertTrue(changed)
        self.assertNotEqual(key_cli, key_api)
        self.assertTrue(provider_api.metadata["identity"]["switched"])
        self.assertFalse(provider_api.metadata["identity"]["accountChanged"])
        self.assertTrue(provider_api.metadata["identity"]["sourceChanged"])
        self.assertEqual(provider_api.extras["sourceSwitched"], True)
        self.assertIsNone(provider_api.primary_metric)


if __name__ == "__main__":
    unittest.main()
