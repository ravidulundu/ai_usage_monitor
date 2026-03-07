from __future__ import annotations

from core.ai_usage_monitor.config import load_config, provider_settings_map
from core.ai_usage_monitor.models import AppState, ProviderState
from core.ai_usage_monitor.providers.registry import ProviderRegistry
from core.ai_usage_monitor.providers import (
    collect_amp,
    collect_claude,
    collect_copilot,
    collect_codex,
    collect_gemini,
    collect_kilo,
    collect_minimax,
    collect_openrouter,
    collect_ollama,
    collect_opencode,
    collect_vertexai,
    collect_zai,
)


COLLECTORS = {
    "amp": collect_amp,
    "claude": collect_claude,
    "codex": collect_codex,
    "gemini": collect_gemini,
    "copilot": collect_copilot,
    "vertexai": collect_vertexai,
    "openrouter": collect_openrouter,
    "ollama": collect_ollama,
    "opencode": collect_opencode,
    "zai": collect_zai,
    "kilo": collect_kilo,
    "minimax": collect_minimax,
}


def _disabled_provider_state(provider_id, descriptor, settings) -> ProviderState:
    return ProviderState(
        id=provider_id,
        display_name=descriptor.display_name if descriptor else provider_id,
        enabled=False,
        installed=False,
        authenticated=False,
        status="disabled",
        source=str(settings.get("source", descriptor.source_modes[0] if descriptor else "auto")),
        metadata={},
    )


def collect_all():
    config = load_config()
    settings_map = provider_settings_map(config)
    descriptors = {descriptor.id: descriptor for descriptor in ProviderRegistry().list_descriptors()}
    legacy = {}
    state = []
    for provider_id, collector in COLLECTORS.items():
        settings = settings_map.get(provider_id, {})
        descriptor = descriptors.get(provider_id)
        enabled = bool(settings.get("enabled", descriptor.default_enabled if descriptor else True))

        if enabled:
            provider_legacy, provider_state = collector(settings)
        else:
            provider_legacy = {"installed": False, "enabled": False}
            provider_state = _disabled_provider_state(provider_id, descriptor, settings)

        provider_state.enabled = enabled
        provider_state.metadata = dict(provider_state.metadata or {})
        provider_state.metadata["configuredSource"] = str(
            settings.get("source", descriptor.source_modes[0] if descriptor else provider_state.source or "auto")
        )
        if descriptor:
            provider_state.metadata["branding"] = descriptor.branding.to_dict()
        legacy[provider_id] = provider_legacy
        state.append(provider_state)
    return legacy, AppState(providers=state)


def collect_legacy_usage() -> dict:
    legacy, _ = collect_all()
    return legacy


def collect_state_payload() -> dict:
    _, app_state = collect_all()
    return app_state.to_dict()
