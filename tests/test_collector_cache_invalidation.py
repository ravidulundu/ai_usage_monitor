from __future__ import annotations

import unittest

from core.ai_usage_monitor.collector_helpers import (
    changed_provider_ids,
    refresh_changed_provider_records,
)
from core.ai_usage_monitor.models import MetricWindow, ProviderState
from core.ai_usage_monitor.providers.base import ProviderBranding, ProviderDescriptor


class CollectorCacheInvalidationTests(unittest.TestCase):
    def _record(
        self,
        *,
        provider_id: str,
        metric_pct: int,
        identity_changed: bool,
        identity_switched: bool,
        enabled: bool = True,
        installed: bool = True,
    ) -> tuple[dict, dict]:
        calls = {"count": 0}

        def collector(_settings: dict) -> tuple[dict, ProviderState]:
            calls["count"] += 1
            return (
                {"collectorCalls": calls["count"]},
                ProviderState(
                    id=provider_id,
                    display_name=provider_id.upper(),
                    enabled=enabled,
                    installed=installed,
                    source="cli",
                    primary_metric=MetricWindow("5h", metric_pct, None),
                    extras={"accountId": f"{provider_id}-acc"},
                ),
            )

        descriptor = ProviderDescriptor(
            id=provider_id,
            display_name=provider_id.upper(),
            source_modes=("auto",),
            branding=ProviderBranding(icon_key=provider_id),
        )

        record = {
            "provider_id": provider_id,
            "collector": collector,
            "settings": {"id": provider_id, "enabled": enabled, "source": "auto"},
            "descriptor": descriptor,
            "enabled": enabled,
            "configured_source": "auto",
            "legacy": {},
            "state": ProviderState(
                id=provider_id,
                display_name=provider_id.upper(),
                enabled=enabled,
                installed=installed,
                source="cli",
                primary_metric=MetricWindow("5h", 1, None),
                extras={"accountId": f"{provider_id}-acc"},
            ),
            "identity_changed": identity_changed,
            "identity_switched": identity_switched,
        }
        return record, calls

    def test_changed_provider_ids_filters_by_identity_enabled_and_installed(self):
        changed, _ = self._record(
            provider_id="codex",
            metric_pct=10,
            identity_changed=True,
            identity_switched=False,
            enabled=True,
            installed=True,
        )
        switched, _ = self._record(
            provider_id="kilo",
            metric_pct=20,
            identity_changed=False,
            identity_switched=True,
            enabled=True,
            installed=True,
        )
        disabled, _ = self._record(
            provider_id="claude",
            metric_pct=30,
            identity_changed=True,
            identity_switched=False,
            enabled=False,
            installed=True,
        )
        not_installed, _ = self._record(
            provider_id="opencode",
            metric_pct=40,
            identity_changed=True,
            identity_switched=False,
            enabled=True,
            installed=False,
        )

        ids = changed_provider_ids([changed, switched, disabled, not_installed])
        self.assertEqual(ids, {"codex", "kilo"})

    def test_refresh_changed_provider_records_refetches_only_changed_records(self):
        codex_record, codex_calls = self._record(
            provider_id="codex",
            metric_pct=88,
            identity_changed=True,
            identity_switched=False,
        )
        claude_record, claude_calls = self._record(
            provider_id="claude",
            metric_pct=45,
            identity_changed=False,
            identity_switched=False,
        )

        identity_store = {"version": 1, "providers": {}}
        records = [codex_record, claude_record]
        refresh_changed_provider_records(records, {"codex"}, identity_store)

        self.assertEqual(codex_calls["count"], 1)
        self.assertEqual(claude_calls["count"], 0)

        codex_metric = records[0]["state"].primary_metric
        claude_metric = records[1]["state"].primary_metric
        self.assertIsNotNone(codex_metric)
        self.assertIsNotNone(claude_metric)
        self.assertEqual(codex_metric.used_pct, 88)
        self.assertEqual(claude_metric.used_pct, 1)

        codex_identity = records[0]["state"].metadata.get("identity", {})
        self.assertTrue(codex_identity.get("refetchedAfterChange"))


if __name__ == "__main__":
    unittest.main()
