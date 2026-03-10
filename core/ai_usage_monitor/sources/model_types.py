from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SourceModelInputs:
    available_sources: tuple[str, ...]
    preferred_policy: str
    resolution_data: dict[str, Any]
    preferred_source: str
    active_source: str


@dataclass(frozen=True)
class SourceModelRuntime:
    has_local_capability: bool
    has_api_capability: bool
    has_web_capability: bool
    local_tool_detected: bool
    api_configured: bool
    api_key_present: bool
    auth_state: str
    auth_valid: bool | None
    rate_limit_state: str
    fallback_active: bool
    fallback_reason: str
    canonical_mode: str
    source_label: str
    resolution_reason: str
    supports_probe: bool
    fallback_chain: tuple[str, ...]
    candidates: tuple[dict[str, str], ...]
    source_details: str
    fallback_label: str
