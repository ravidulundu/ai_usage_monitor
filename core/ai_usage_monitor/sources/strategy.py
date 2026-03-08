from __future__ import annotations

from typing import Any

_LOCAL_IDS = {"cli", "local"}
_API_IDS = {"api"}
_WEB_IDS = {"web", "remote"}
_OAUTH_IDS = {"oauth"}
_LOCAL_RUNTIME_IDS = _LOCAL_IDS | _OAUTH_IDS
_REMOTE_RUNTIME_IDS = _API_IDS | _WEB_IDS

_POLICY_ORDER: dict[str, tuple[str, ...]] = {
    "local_first": ("cli", "local", "oauth", "api", "web", "remote", "probe"),
    "api_first": ("api", "web", "remote", "oauth", "cli", "local", "probe"),
    "web_first": ("web", "remote", "api", "oauth", "cli", "local", "probe"),
    "oauth_first": ("oauth", "cli", "local", "api", "web", "remote", "probe"),
    "auto": ("cli", "local", "oauth", "api", "web", "remote", "probe"),
}


def _norm(value: Any) -> str:
    return str(value or "").strip().lower()


def _canonical_kind(source_id: str) -> str:
    if source_id in _LOCAL_IDS:
        return "local_cli"
    if source_id in _API_IDS:
        return "api"
    if source_id in _WEB_IDS:
        return "web"
    if source_id in _OAUTH_IDS:
        return "oauth"
    if source_id in {"probe", "auto"}:
        return "probe"
    return source_id or "probe"


def _preferred_policy(descriptor: Any) -> str:
    policy = _norm(getattr(descriptor, "preferred_source_policy", ""))
    return policy if policy in _POLICY_ORDER else "auto"


def _supported_sources(descriptor: Any) -> list[str]:
    supported = [
        _norm(item) for item in list(getattr(descriptor, "source_modes", ()) or [])
    ]
    deduped: list[str] = []
    for source in supported:
        if source and source not in deduped:
            deduped.append(source)
    return deduped or ["auto"]


def _dedupe(values: list[str]) -> list[str]:
    ordered: list[str] = []
    for value in values:
        if value and value not in ordered:
            ordered.append(value)
    return ordered


def _preferred_source_value(
    settings: dict[str, Any] | None,
    configured_source: str | None,
    supported_sources: list[str],
) -> str:
    configured = _norm(configured_source or (settings or {}).get("source"))
    preferred_source = configured or supported_sources[0]
    if preferred_source not in supported_sources and preferred_source not in {
        "probe",
        "local_cli",
    }:
        return supported_sources[0]
    return preferred_source


def _build_local_first_candidates(
    supported_sources: list[str], supports_probe: bool
) -> list[str]:
    local_candidates = [
        source
        for source in _POLICY_ORDER["local_first"]
        if source in supported_sources and source in _LOCAL_RUNTIME_IDS
    ]
    remote_candidates = [
        source
        for source in _POLICY_ORDER["api_first"]
        if source in supported_sources and source in _REMOTE_RUNTIME_IDS
    ]
    candidates = _dedupe(local_candidates + remote_candidates)
    if not candidates and supported_sources:
        candidates = [supported_sources[0]]
    if supports_probe and "probe" not in candidates:
        candidates.append("probe")
    return candidates


def _build_policy_candidates(
    policy: str, supported_sources: list[str], supports_probe: bool
) -> list[str]:
    candidates: list[str] = []
    for source in _POLICY_ORDER[policy]:
        if source in {"probe", "auto"}:
            if supports_probe and "probe" not in candidates:
                candidates.append("probe")
            continue
        if source in supported_sources and source not in candidates:
            candidates.append(source)
    if not candidates:
        return [supported_sources[0]]
    return candidates


def _build_explicit_candidates(
    preferred_source: str,
    policy: str,
    supported_sources: list[str],
    supports_probe: bool,
) -> list[str]:
    candidates = [preferred_source]
    for source in _POLICY_ORDER[policy]:
        if source in {"probe", "auto"}:
            continue
        if (
            source in supported_sources
            and source != preferred_source
            and source not in candidates
        ):
            candidates.append(source)
    if supports_probe:
        candidates.append("probe")
    return candidates


def _resolve_candidates(
    preferred_source: str,
    policy: str,
    supported_sources: list[str],
    supports_probe: bool,
) -> tuple[list[str], str]:
    if preferred_source == "local_cli":
        return (
            _build_local_first_candidates(supported_sources, supports_probe),
            "explicit_local_first",
        )
    if preferred_source in {"auto", "probe"}:
        return (
            _build_policy_candidates(policy, supported_sources, supports_probe),
            "policy_chain",
        )
    return (
        _build_explicit_candidates(
            preferred_source,
            policy,
            supported_sources,
            supports_probe,
        ),
        "explicit_source",
    )


def _candidate_payload(candidates: list[str]) -> list[dict[str, str]]:
    return [
        {
            "source": source,
            "kind": _canonical_kind(source),
        }
        for source in candidates
    ]


def resolve_provider_source_plan(
    descriptor: Any,
    settings: dict[str, Any] | None,
    configured_source: str | None = None,
) -> dict[str, Any]:
    supported_sources = _supported_sources(descriptor)
    supports_probe = "auto" in supported_sources or "probe" in supported_sources
    policy = _preferred_policy(descriptor)
    preferred_source = _preferred_source_value(
        settings, configured_source, supported_sources
    )
    candidates, resolution_reason = _resolve_candidates(
        preferred_source,
        policy,
        supported_sources,
        supports_probe,
    )

    resolved_hint = candidates[0] if candidates else preferred_source
    fallback_chain = candidates[1:] if len(candidates) > 1 else []

    return {
        "preferredSource": preferred_source,
        "resolvedSourceHint": resolved_hint,
        "supportedSources": supported_sources,
        "preferredSourcePolicy": policy,
        "supportsProbe": supports_probe,
        "fallbackChain": fallback_chain,
        "resolutionReason": resolution_reason,
        "candidates": _candidate_payload(candidates),
    }
