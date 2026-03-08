from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from core.ai_usage_monitor.models import MetricWindow, ProviderState


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def clamp_pct(value: int | float | None) -> float:
    if value is None:
        return 0.0
    try:
        number = float(value)
    except Exception:
        number = 0.0
    return max(0.0, min(100.0, number))


def metric_percent(metric: MetricWindow | None) -> float | None:
    if metric is None or metric.used_pct is None:
        return None
    try:
        parsed = float(metric.used_pct)
    except Exception:
        return None
    if parsed != parsed:
        return None
    return clamp_pct(parsed)


def is_stale(
    updated_at: str | None, now: datetime, refresh_interval_seconds: int
) -> bool:
    parsed = parse_iso(updated_at)
    if not parsed:
        return True
    threshold = max(180, refresh_interval_seconds * 3)
    return (now - parsed).total_seconds() > threshold


def updated_text(updated_at: str | None, now: datetime) -> str:
    parsed = parse_iso(updated_at)
    if not parsed:
        return "Updated just now"
    age_seconds = max(0, (now - parsed).total_seconds())
    if age_seconds <= 5:
        return "Updated just now"
    return "Updated " + parsed.astimezone().strftime("%H:%M:%S")


def humanize_reset(reset_at: str | None) -> str:
    reset = parse_iso(reset_at)
    if not reset:
        return "—" if not reset_at else "Resets soon"
    now = datetime.now(timezone.utc)
    diff_seconds = int((reset - now).total_seconds())
    if diff_seconds <= 0:
        return "Resets soon"

    hours, rem = divmod(diff_seconds, 3600)
    minutes = rem // 60
    if hours >= 24:
        return f"Resets in {hours // 24}d {hours % 24}h"
    if hours > 0:
        return f"Resets in {hours}h {minutes}m"
    return f"Resets in {minutes}m"


def format_usd(value: float | None) -> str:
    if value is None:
        return "—"
    return f"$ {value:,.2f}"


def format_tokens(value: int | None) -> str:
    if value is None:
        return "—"
    abs_value = abs(value)
    if abs_value >= 1_000_000:
        scaled = value / 1_000_000
        text = f"{scaled:.0f}" if abs(scaled) >= 100 else f"{scaled:.1f}"
        return f"{text.rstrip('0').rstrip('.')}M tokens"
    if abs_value >= 1_000:
        scaled = value / 1_000
        text = f"{scaled:.0f}" if abs(scaled) >= 100 else f"{scaled:.1f}"
        return f"{text.rstrip('0').rstrip('.')}K tokens"
    return f"{value:,} tokens"


def error_summary(error_text: str | None) -> str | None:
    if not error_text:
        return None
    text = str(error_text).strip()
    if not text:
        return None

    lowered = text.lower()
    if "rate limited" in lowered:
        return "Rate limited"
    if (
        "auth" in lowered
        or "invalid authentication" in lowered
        or "credentials" in lowered
    ):
        return "Authentication required"
    if "timeout" in lowered:
        return "Request timed out"
    if "network" in lowered or "connection" in lowered:
        return "Network error"

    first_sentence = text.split(".")[0].strip()
    if len(first_sentence) > 64:
        return first_sentence[:61].rstrip() + "..."
    return first_sentence or text


def mini_metric_display_text(mode: str, percent: float | None) -> str:
    if mode == "percent" and percent is not None:
        return f"{round(percent)}%"
    if mode == "tick":
        return "OK"
    return "—"


def plan_label(provider: ProviderState) -> str | None:
    plan = provider.extras.get("plan") if isinstance(provider.extras, dict) else None
    if plan is None:
        return None
    text = str(plan).strip()
    return text or None


def provider_short_name(
    provider_id: str, display_name: str, descriptor_short_name: str | None = None
) -> str:
    if descriptor_short_name:
        return descriptor_short_name
    words = [word for word in display_name.split() if word]
    if words:
        return words[0]
    return provider_id.upper()


def provider_badge_text(
    provider_id: str, display_name: str, explicit_badge: str | None = None
) -> str:
    if explicit_badge:
        return explicit_badge
    words = [word for word in display_name.split() if word]
    if len(words) >= 2:
        return f"{words[0][0]}{words[1][0]}".upper()
    if display_name:
        return display_name[:2].upper()
    return provider_id[:2].upper()


def branding(provider: ProviderState) -> dict[str, Any]:
    metadata = provider.metadata if isinstance(provider.metadata, dict) else {}
    value = metadata.get("branding")
    return value if isinstance(value, dict) else {}
