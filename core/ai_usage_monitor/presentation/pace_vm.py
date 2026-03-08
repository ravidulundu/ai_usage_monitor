from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from core.ai_usage_monitor.models import MetricWindow


def pace_text(metric: MetricWindow | None, kind: str) -> str | None:
    if not metric:
        return None
    reset = _parse_iso(metric.reset_at)
    if not reset:
        return None

    window_seconds = _metric_window_seconds(metric, kind)
    if window_seconds is None or window_seconds <= 0:
        return None

    now = datetime.now(timezone.utc)
    remaining_seconds = int((reset - now).total_seconds())
    if remaining_seconds <= 0:
        return None

    window_start = reset - timedelta(seconds=window_seconds)
    elapsed_seconds = int((now - window_start).total_seconds())
    if elapsed_seconds <= 0:
        return None
    elapsed_seconds = min(elapsed_seconds, window_seconds)

    if _pace_hidden_at_window_start(kind, elapsed_seconds, window_seconds):
        return None

    percent = _metric_percent(metric)
    if percent is None:
        return None

    elapsed_pct = max(0.0, min(100.0, (elapsed_seconds / window_seconds) * 100.0))
    delta = percent - elapsed_pct

    left = "Pace: On pace"
    if delta >= 1.5:
        left = f"Pace: {round(abs(delta))}% in deficit"
    elif delta <= -1.5:
        left = f"Pace: {round(abs(delta))}% in reserve"

    right = "Lasts until reset"
    if percent >= 100:
        right = "Runs out soon"
    elif percent > 0:
        rate_per_second = percent / elapsed_seconds
        if rate_per_second > 0:
            seconds_to_full = int((100 - percent) / rate_per_second)
            if 0 < seconds_to_full < remaining_seconds:
                right = f"Runs out in {_humanize_duration_seconds(seconds_to_full)}"

    return f"{left} · {right}"


def _metric_window_seconds(metric: MetricWindow, kind: str) -> int | None:
    label = str(metric.label or "").strip().lower()
    parsed_from_label = _duration_seconds_from_label(label)
    if parsed_from_label is not None:
        return parsed_from_label

    if kind == "weekly":
        return 7 * 24 * 60 * 60
    if kind == "session":
        return 5 * 60 * 60
    return None


def _duration_seconds_from_label(label: str) -> int | None:
    if not label:
        return None

    aliases: dict[str, int] = {
        "weekly": 7 * 24 * 60 * 60,
        "daily": 24 * 60 * 60,
        "hourly": 60 * 60,
        "monthly": 30 * 24 * 60 * 60,
    }
    if label in aliases:
        return aliases[label]

    match = re.match(r"^\s*(\d+)\s*([mhdw])\s*$", label)
    if not match:
        return None

    value = int(match.group(1))
    unit = match.group(2)
    if unit == "m":
        return value * 60
    if unit == "h":
        return value * 60 * 60
    if unit == "d":
        return value * 24 * 60 * 60
    if unit == "w":
        return value * 7 * 24 * 60 * 60
    return None


def _pace_hidden_at_window_start(
    kind: str, elapsed_seconds: int, window_seconds: int
) -> bool:
    if kind == "session":
        minimum_elapsed = max(10 * 60, int(window_seconds * 0.08))
    elif kind == "weekly":
        minimum_elapsed = max(30 * 60, int(window_seconds * 0.03))
    else:
        minimum_elapsed = max(15 * 60, int(window_seconds * 0.05))
    return elapsed_seconds < minimum_elapsed


def _humanize_duration_seconds(seconds: int) -> str:
    if seconds <= 0:
        return "soon"
    total_minutes = seconds // 60
    days = total_minutes // (60 * 24)
    hours = (total_minutes % (60 * 24)) // 60
    minutes = total_minutes % 60
    if days > 0:
        return f"{days}d {hours}h"
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def _metric_percent(metric: MetricWindow | None) -> float | None:
    if metric is None:
        return None
    value = metric.used_pct
    try:
        parsed = float(value)
    except Exception:
        return None
    if parsed != parsed:
        return None
    return _clamp_pct(parsed)


def _clamp_pct(value: int | float | None) -> float:
    if value is None:
        return 0.0
    try:
        number = float(value)
    except Exception:
        return 0.0
    if number != number:
        return 0.0
    return max(0.0, min(100.0, number))


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except Exception:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
