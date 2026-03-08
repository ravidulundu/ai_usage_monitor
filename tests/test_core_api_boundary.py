from __future__ import annotations

import core.ai_usage_monitor as core_api


def test_core_public_api_exports_expected_entrypoints():
    assert "collect_legacy_usage" in core_api.__all__
    assert "collect_state_payload" in core_api.__all__
    assert "collect_popup_vm_payload" in core_api.__all__
    assert callable(core_api.collect_legacy_usage)
    assert callable(core_api.collect_state_payload)
    assert callable(core_api.collect_popup_vm_payload)
