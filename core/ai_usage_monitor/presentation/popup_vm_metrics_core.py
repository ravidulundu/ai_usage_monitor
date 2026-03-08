from __future__ import annotations

from typing import Any

from core.ai_usage_monitor.models import MetricWindow, ProviderState
from core.ai_usage_monitor.presentation.identity_vm import (
    provider_identity_refreshing as _provider_identity_refreshing,
    switching_state_vm as _switching_state_vm,
)
from core.ai_usage_monitor.presentation.pace_vm import pace_text as _pace_text
from core.ai_usage_monitor.presentation.popup_vm_common import (
    clamp_pct,
    error_summary,
    humanize_reset,
    metric_percent,
)


def provider_metrics_vm(
    provider: ProviderState,
    stale: bool,
    rate_limits_missing: bool,
    source_presentation: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    session_metric = metric_vm(
        provider=provider,
        metric=provider.primary_metric,
        kind="session",
        default_label="Session",
        stale=stale,
        provider_error=provider.error,
        rate_limits_missing=rate_limits_missing,
        source_presentation=source_presentation,
    )
    weekly_metric = metric_vm(
        provider=provider,
        metric=provider.secondary_metric,
        kind="weekly",
        default_label="Weekly",
        stale=stale,
        provider_error=provider.error,
        rate_limits_missing=rate_limits_missing,
        source_presentation=source_presentation,
    )
    _attach_metric_pace(
        session_metric, _pace_text(provider.primary_metric, kind="session")
    )
    _attach_metric_pace(
        weekly_metric, _pace_text(provider.secondary_metric, kind="weekly")
    )
    return finalize_metrics(
        [session_metric, weekly_metric]
        + bucket_metrics_vm(provider, stale=stale, provider_error=provider.error)
    )


def provider_error_state(
    provider: ProviderState, source_presentation: dict[str, Any] | None
) -> tuple[str | None, str | None]:
    error_message = None
    if not provider.installed:
        error_message = "Provider unavailable"
    elif provider.error:
        error_message = error_summary(provider.error)

    source_unavailable = (
        source_presentation.get("unavailableReason")
        if isinstance(source_presentation, dict)
        else None
    )
    source_unavailable_text = (
        source_unavailable.get("text") if isinstance(source_unavailable, dict) else None
    )
    return error_message, source_unavailable_text


def metric_vm(
    provider: ProviderState,
    metric: MetricWindow | None,
    kind: str,
    default_label: str,
    stale: bool,
    provider_error: str | None,
    rate_limits_missing: bool,
    source_presentation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    identity_refreshing = _provider_identity_refreshing(provider)
    switching_state = _switching_state_vm(provider)
    tone = metric_tone(stale=stale, provider_error=provider_error)
    source_reason = (
        source_presentation.get("unavailableReason")
        if isinstance(source_presentation, dict)
        else None
    )
    source_reason_text = (
        source_reason.get("text") if isinstance(source_reason, dict) else None
    )
    source_hint_text = (
        source_presentation.get("reasonText")
        if isinstance(source_presentation, dict)
        else None
    )

    if identity_refreshing and not provider_error and metric is None:
        return {
            "kind": kind,
            "label": default_label,
            "percent": None,
            "leftText": switching_state.get("title") or "Switching state",
            "rightText": "…",
            "secondaryText": switching_state.get("message") or "Refreshing usage",
            "visible": True,
            "available": False,
            "stale": False,
            "errorMessage": None,
            "tone": "warn",
        }

    if metric:
        percent = metric_percent(metric)
        secondary_text = metric_secondary_text(
            stale=stale, provider_error=provider_error
        )
        if percent is not None:
            return {
                "kind": kind,
                "label": default_label,
                "percent": percent,
                "leftText": f"{round(percent)}% used",
                "rightText": humanize_reset(metric.reset_at),
                "secondaryText": secondary_text,
                "visible": True,
                "available": True,
                "stale": stale,
                "errorMessage": error_summary(provider_error)
                if provider_error
                else None,
                "tone": tone,
            }
        return {
            "kind": kind,
            "label": default_label,
            "percent": None,
            "leftText": "Unable to refresh" if provider_error else "Data unavailable",
            "rightText": "—",
            "secondaryText": secondary_text,
            "visible": True,
            "available": False,
            "stale": stale,
            "errorMessage": error_summary(provider_error) if provider_error else None,
            "tone": tone,
        }

    if not provider.installed:
        left, secondary_text = (
            source_reason_text or "Provider unavailable",
            source_hint_text,
        )
    elif rate_limits_missing:
        left, secondary_text = (
            source_reason_text or "Usage limits unavailable",
            source_hint_text,
        )
    elif provider_error:
        left, secondary_text = "Unable to refresh", error_summary(provider_error)
    elif source_reason_text:
        left, secondary_text = source_reason_text, source_hint_text
    else:
        left, secondary_text = "Data unavailable", "Stale data" if stale else None

    if stale and secondary_text and secondary_text != "Stale data":
        secondary_text = f"Stale data · {secondary_text}"

    return {
        "kind": kind,
        "label": default_label,
        "percent": None,
        "leftText": left,
        "rightText": "—",
        "secondaryText": secondary_text,
        "visible": True,
        "available": False,
        "stale": stale,
        "errorMessage": error_summary(provider_error) if provider_error else None,
        "tone": tone,
    }


def bucket_metrics_vm(
    provider: ProviderState, stale: bool, provider_error: str | None
) -> list[dict[str, Any]]:
    if _provider_identity_refreshing(provider):
        return []

    buckets = (
        provider.extras.get("buckets") if isinstance(provider.extras, dict) else None
    )
    if not isinstance(buckets, list):
        return []

    rows: list[dict[str, Any]] = []
    for bucket in buckets:
        if not isinstance(bucket, dict):
            continue
        used_pct_raw = bucket.get("used_pct")
        try:
            percent_value = float(used_pct_raw) if used_pct_raw is not None else None
        except Exception:
            percent_value = None
        available = percent_value is not None and provider_error is None
        left_text = (
            "Unable to refresh"
            if provider_error
            else (
                "Data unavailable"
                if percent_value is None
                else f"{round(percent_value)}% used"
            )
        )
        rows.append(
            {
                "kind": "model",
                "label": str(bucket.get("model") or "Model"),
                "percent": clamp_pct(percent_value)
                if percent_value is not None
                else None,
                "leftText": left_text,
                "rightText": humanize_reset(bucket.get("reset_time"))
                if available
                else "—",
                "secondaryText": metric_secondary_text(
                    stale=stale, provider_error=provider_error
                ),
                "visible": True,
                "available": available,
                "stale": stale,
                "errorMessage": error_summary(provider_error)
                if provider_error
                else None,
                "tone": metric_tone(stale=stale, provider_error=provider_error),
            }
        )
    return rows


def metric_rank(kind: str | None) -> int:
    if kind == "session":
        return 0
    if kind == "weekly":
        return 1
    if kind == "model":
        return 2
    return 99


def finalize_metrics(metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    visible = [metric for metric in metrics if metric.get("visible", True)]
    visible.sort(key=lambda metric: metric_rank(str(metric.get("kind"))))
    return visible


def metric_tone(stale: bool, provider_error: str | None) -> str:
    if provider_error:
        return "error"
    return "warn" if stale else "accent"


def metric_secondary_text(stale: bool, provider_error: str | None) -> str | None:
    if provider_error:
        summary = error_summary(provider_error)
        return f"Stale data · {summary}" if stale else summary
    return "Stale data" if stale else None


def _attach_metric_pace(metric: dict[str, Any], pace_text: str | None) -> None:
    if metric.get("available") and not metric.get("secondaryText") and pace_text:
        metric["secondaryText"] = pace_text
