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

    @classmethod
    def from_dict(cls, payload: Any) -> MetricWindow | None:
        if not isinstance(payload, dict):
            return None
        used_pct = payload.get("usedPct")
        if used_pct is None:
            return None
        try:
            coerced_pct = float(used_pct)
        except (TypeError, ValueError):
            return None
        return cls(
            label=str(payload.get("label") or ""),
            used_pct=coerced_pct,
            reset_at=payload.get("resetAt"),
            kind=str(payload.get("kind") or "window"),
        )


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

    @classmethod
    def from_dict(cls, payload: Any) -> LocalUsageSnapshot | None:
        if not isinstance(payload, dict):
            return None
        return cls(
            session_tokens=payload.get("sessionTokens"),
            last_30_days_tokens=payload.get("last30DaysTokens"),
            session_cost_usd=payload.get("sessionCostUSD"),
            last_30_days_cost_usd=payload.get("last30DaysCostUSD"),
        )


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

    @classmethod
    def from_dict(cls, payload: Any) -> ProviderState:
        data: dict[str, Any] = payload if isinstance(payload, dict) else {}
        return cls(
            id=str(data.get("id") or ""),
            display_name=str(data.get("displayName") or data.get("id") or ""),
            enabled=bool(data.get("enabled", True)),
            installed=bool(data.get("installed", False)),
            authenticated=bool(data.get("authenticated", True)),
            status=str(data.get("status") or "ok"),
            source=str(data.get("source") or "local"),
            primary_metric=MetricWindow.from_dict(data.get("primaryMetric")),
            secondary_metric=MetricWindow.from_dict(data.get("secondaryMetric")),
            local_usage=LocalUsageSnapshot.from_dict(data.get("localUsage")),
            source_model=dict(data.get("sourceModel") or {}),
            metadata=dict(data.get("metadata") or {}),
            extras=dict(data.get("extras") or {}),
            error=str(data.get("error")) if data.get("error") is not None else None,
            incident=dict(data.get("incident") or {})
            if isinstance(data.get("incident"), dict)
            else None,
        )


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
