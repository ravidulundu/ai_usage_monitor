from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

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

FetchStrategy = Callable[[dict], tuple[dict, object]]


@dataclass(frozen=True)
class ProviderFetchStrategy:
    provider_id: str
    fetch: FetchStrategy
    supports_probe: bool = False


FETCH_STRATEGIES: dict[str, ProviderFetchStrategy] = {
    "amp": ProviderFetchStrategy("amp", collect_amp, supports_probe=False),
    "claude": ProviderFetchStrategy("claude", collect_claude, supports_probe=False),
    "codex": ProviderFetchStrategy("codex", collect_codex, supports_probe=False),
    "gemini": ProviderFetchStrategy("gemini", collect_gemini, supports_probe=False),
    "copilot": ProviderFetchStrategy("copilot", collect_copilot, supports_probe=False),
    "vertexai": ProviderFetchStrategy(
        "vertexai", collect_vertexai, supports_probe=False
    ),
    "openrouter": ProviderFetchStrategy(
        "openrouter", collect_openrouter, supports_probe=False
    ),
    "ollama": ProviderFetchStrategy("ollama", collect_ollama, supports_probe=False),
    "opencode": ProviderFetchStrategy(
        "opencode", collect_opencode, supports_probe=True
    ),
    "zai": ProviderFetchStrategy("zai", collect_zai, supports_probe=False),
    "kilo": ProviderFetchStrategy("kilo", collect_kilo, supports_probe=True),
    "minimax": ProviderFetchStrategy("minimax", collect_minimax, supports_probe=True),
}


def fetch_strategy_for(provider_id: str) -> ProviderFetchStrategy | None:
    return FETCH_STRATEGIES.get(provider_id)


def fetcher_map() -> dict[str, FetchStrategy]:
    return {
        provider_id: strategy.fetch
        for provider_id, strategy in FETCH_STRATEGIES.items()
    }
