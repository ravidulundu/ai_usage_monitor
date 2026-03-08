from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from core.ai_usage_monitor.identity_fingerprint import normalize
from core.ai_usage_monitor.models import LocalUsageSnapshot, MetricWindow, ProviderState


_IDENTITY_STATE_VERSION = 1


def identity_state_path() -> Path:
    state_dir = os.environ.get("AI_USAGE_MONITOR_STATE_DIR")
    if state_dir and state_dir.strip():
        return Path(state_dir).expanduser() / "provider_identity_state.json"
    return Path.home() / ".cache" / "ai-usage-monitor" / "provider_identity_state.json"


def metric_to_payload(metric: MetricWindow | None) -> dict[str, Any] | None:
    if metric is None:
        return None
    return {
        "label": str(metric.label),
        "usedPct": float(metric.used_pct),
        "resetAt": metric.reset_at,
        "kind": str(metric.kind),
    }


def metric_from_payload(payload: Any) -> MetricWindow | None:
    if not isinstance(payload, dict):
        return None
    used_pct = _coerce_float(payload.get("usedPct"))
    if used_pct is None:
        return None
    return MetricWindow(
        str(payload.get("label") or ""),
        used_pct,
        payload.get("resetAt"),
        kind=str(payload.get("kind") or "window"),
    )


def local_usage_to_payload(
    local_usage: LocalUsageSnapshot | None,
) -> dict[str, Any] | None:
    if local_usage is None:
        return None
    return {
        "sessionTokens": local_usage.session_tokens,
        "last30DaysTokens": local_usage.last_30_days_tokens,
        "sessionCostUSD": local_usage.session_cost_usd,
        "last30DaysCostUSD": local_usage.last_30_days_cost_usd,
    }


def local_usage_from_payload(payload: Any) -> LocalUsageSnapshot | None:
    if not isinstance(payload, dict):
        return None
    return LocalUsageSnapshot(
        session_tokens=payload.get("sessionTokens"),
        last_30_days_tokens=payload.get("last30DaysTokens"),
        session_cost_usd=payload.get("sessionCostUSD"),
        last_30_days_cost_usd=payload.get("last30DaysCostUSD"),
    )


def _coerce_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def provider_has_usage_snapshot(provider: ProviderState) -> bool:
    extras = provider.extras if isinstance(provider.extras, dict) else {}
    buckets = extras.get("buckets")
    return (
        provider.primary_metric is not None
        or provider.secondary_metric is not None
        or provider.local_usage is not None
        or (isinstance(buckets, list) and len(buckets) > 0)
    )


def provider_snapshot_payload(
    provider: ProviderState, captured_at: str
) -> dict[str, Any]:
    extras = provider.extras if isinstance(provider.extras, dict) else {}
    snapshot: dict[str, Any] = {
        "capturedAt": captured_at,
        "primaryMetric": metric_to_payload(provider.primary_metric),
        "secondaryMetric": metric_to_payload(provider.secondary_metric),
        "localUsage": local_usage_to_payload(provider.local_usage),
    }

    buckets = extras.get("buckets")
    if isinstance(buckets, list):
        compact_buckets: list[Any] = []
        for bucket in buckets[:8]:
            compact_buckets.append(dict(bucket) if isinstance(bucket, dict) else bucket)
        snapshot["buckets"] = compact_buckets

    for key in ("plan", "model", "hasData"):
        if key in extras:
            snapshot[key] = extras.get(key)
    return snapshot


def apply_provider_snapshot(provider: ProviderState, snapshot: dict[str, Any]) -> bool:
    primary_metric = metric_from_payload(snapshot.get("primaryMetric"))
    secondary_metric = metric_from_payload(snapshot.get("secondaryMetric"))
    local_usage = local_usage_from_payload(snapshot.get("localUsage"))
    has_usage = (
        primary_metric is not None
        or secondary_metric is not None
        or local_usage is not None
    )

    provider.primary_metric = primary_metric
    provider.secondary_metric = secondary_metric
    provider.local_usage = local_usage

    provider.extras = dict(provider.extras or {})
    for key in ("plan", "model", "hasData"):
        if key in snapshot:
            provider.extras[key] = snapshot.get(key)
    buckets = snapshot.get("buckets")
    if isinstance(buckets, list):
        provider.extras["buckets"] = [
            dict(bucket) if isinstance(bucket, dict) else bucket for bucket in buckets
        ]

    return has_usage


def snapshot_store(mapping: Any) -> dict[str, Any]:
    return mapping if isinstance(mapping, dict) else {}


def prune_snapshots(snapshots: dict[str, Any], limit: int = 8) -> dict[str, Any]:
    if len(snapshots) <= limit:
        return snapshots
    ordered = sorted(
        snapshots.items(),
        key=lambda item: normalize(
            item[1].get("capturedAt") if isinstance(item[1], dict) else ""
        ),
        reverse=True,
    )
    return {fingerprint: payload for fingerprint, payload in ordered[:limit]}


def load_identity_store() -> dict[str, Any]:
    path = identity_state_path()
    if not path.exists():
        return {"version": _IDENTITY_STATE_VERSION, "providers": {}}
    try:
        payload = json.loads(path.read_text())
    except Exception:
        return {"version": _IDENTITY_STATE_VERSION, "providers": {}}
    if not isinstance(payload, dict):
        return {"version": _IDENTITY_STATE_VERSION, "providers": {}}
    providers = payload.get("providers")
    return {
        "version": _IDENTITY_STATE_VERSION,
        "providers": providers if isinstance(providers, dict) else {},
    }


def save_identity_store(store: dict[str, Any]) -> None:
    path = identity_state_path()
    payload = {
        "version": _IDENTITY_STATE_VERSION,
        "providers": dict(store.get("providers") or {}),
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload))
    except OSError:
        return
