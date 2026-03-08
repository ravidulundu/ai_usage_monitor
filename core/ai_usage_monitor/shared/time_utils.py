from __future__ import annotations

from datetime import datetime, timezone


def unix_to_iso(ts: int | float | str | None) -> str | None:
    """Convert Unix timestamp to ISO 8601; returns raw string on parse failure."""
    if ts is None:
        return None
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat()
    except Exception:
        return str(ts)
