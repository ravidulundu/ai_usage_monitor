from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class MetricWindow:
    label: str
    used_pct: int | float
    reset_at: str | None
    kind: str = "window"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "label": self.label,
            "usedPct": round(self.used_pct),
            "resetAt": self.reset_at,
        }


@dataclass
class LocalUsageSnapshot:
    session_tokens: int | None = None
    last_30_days_tokens: int | None = None
    session_cost_usd: float | None = None
    last_30_days_cost_usd: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "sessionTokens": self.session_tokens,
            "last30DaysTokens": self.last_30_days_tokens,
            "sessionCostUSD": self.session_cost_usd,
            "last30DaysCostUSD": self.last_30_days_cost_usd,
        }


@dataclass
class ProviderState:
    id: str
    display_name: str
    enabled: bool = True
    installed: bool = False
    authenticated: bool = True
    status: str = "ok"
    source: str = "local"
    primary_metric: MetricWindow | None = None
    secondary_metric: MetricWindow | None = None
    local_usage: LocalUsageSnapshot | None = None
    source_model: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    extras: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    incident: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "displayName": self.display_name,
            "enabled": self.enabled,
            "installed": self.installed,
            "authenticated": self.authenticated,
            "status": self.status,
            "source": self.source,
            "primaryMetric": self.primary_metric.to_dict()
            if self.primary_metric
            else None,
            "secondaryMetric": self.secondary_metric.to_dict()
            if self.secondary_metric
            else None,
            "localUsage": self.local_usage.to_dict() if self.local_usage else None,
            "sourceModel": self.source_model,
            "metadata": self.metadata,
            "extras": self.extras,
            "error": self.error,
            "incident": self.incident,
        }


@dataclass
class AppState:
    providers: list[ProviderState]
    overview_provider_ids: list[str] = field(default_factory=list)
    version: int = 1
    updated_at: str = field(default_factory=iso_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "updatedAt": self.updated_at,
            "overviewProviderIds": list(self.overview_provider_ids),
            "providers": [provider.to_dict() for provider in self.providers],
        }
