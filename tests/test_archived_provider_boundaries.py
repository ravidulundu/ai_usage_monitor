from __future__ import annotations

from pathlib import Path


def test_archived_provider_collectors_are_not_exported_from_active_package() -> None:
    package_text = Path("core/ai_usage_monitor/providers/__init__.py").read_text()

    assert "collect_kiro" not in package_text
    assert "collect_jetbrains" not in package_text
    assert "collect_warp" not in package_text
    assert "collect_kimik2" not in package_text


def test_archived_provider_ids_are_not_shipped_in_active_registry_surfaces() -> None:
    registry_text = Path("core/ai_usage_monitor/providers/registry.py").read_text()
    fetch_text = Path("core/ai_usage_monitor/providers/fetch_strategies.py").read_text()

    for provider_id in ("kiro", "jetbrains", "warp", "kimik2"):
        assert f'"{provider_id}"' not in registry_text
        assert f'"{provider_id}"' not in fetch_text
