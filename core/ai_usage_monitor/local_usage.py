from __future__ import annotations

import glob
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from core.ai_usage_monitor.models import LocalUsageSnapshot


def _parse_iso(ts: str | None):
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None


def _parse_day(ts: str | None):
    dt = _parse_iso(ts)
    return dt.date().isoformat() if dt else None


def scan_codex_local_usage() -> LocalUsageSnapshot | None:
    root = Path.home() / ".codex" / "sessions"
    if not root.exists():
        return None

    since = (datetime.now(timezone.utc) - timedelta(days=29)).date()
    latest_ts = None
    latest_tokens = None
    day_totals: dict[str, int] = {}

    for path in glob.glob(str(root / "**" / "*.jsonl"), recursive=True):
        file_latest_ts = None
        file_latest_total = None
        try:
            with open(path, errors="replace") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except Exception:
                        continue
                    payload = obj.get("payload", {}) if isinstance(obj.get("payload"), dict) else {}
                    if obj.get("type") != "event_msg" or payload.get("type") != "token_count":
                        continue
                    info = payload.get("info", {}) if isinstance(payload.get("info"), dict) else {}
                    totals = info.get("total_token_usage", {}) if isinstance(info.get("total_token_usage"), dict) else {}
                    total_tokens = totals.get("total_tokens")
                    timestamp = obj.get("timestamp")
                    if total_tokens is None:
                        continue
                    dt = _parse_iso(timestamp)
                    if dt is None:
                        continue
                    if file_latest_ts is None or dt > file_latest_ts:
                        file_latest_ts = dt
                        file_latest_total = int(total_tokens)
        except OSError:
            continue

        if file_latest_ts is None or file_latest_total is None:
            continue

        if latest_ts is None or file_latest_ts > latest_ts:
            latest_ts = file_latest_ts
            latest_tokens = file_latest_total

        if file_latest_ts.date() >= since:
            day_key = file_latest_ts.date().isoformat()
            day_totals[day_key] = day_totals.get(day_key, 0) + file_latest_total

    if latest_tokens is None and not day_totals:
        return None

    return LocalUsageSnapshot(
        session_tokens=latest_tokens,
        last_30_days_tokens=sum(day_totals.values()) if day_totals else None,
    )


def scan_claude_local_usage() -> LocalUsageSnapshot | None:
    roots = [Path.home() / ".claude" / "projects", Path.home() / ".config" / "claude" / "projects"]
    since = (datetime.now(timezone.utc) - timedelta(days=29)).date()
    latest_ts = None
    latest_day_total = None
    day_totals: dict[str, int] = {}
    found = False

    for root in roots:
        if not root.exists():
            continue
        for path in glob.glob(str(root / "**" / "*.jsonl"), recursive=True):
            try:
                with open(path, errors="replace") as handle:
                    for line in handle:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            obj = json.loads(line)
                        except Exception:
                            continue
                        message = obj.get("message", {}) if isinstance(obj.get("message"), dict) else {}
                        usage = message.get("usage", {}) if isinstance(message.get("usage"), dict) else {}
                        if not usage:
                            continue
                        tokens = int(usage.get("input_tokens") or 0)
                        tokens += int(usage.get("cache_read_input_tokens") or 0)
                        tokens += int(usage.get("cache_creation_input_tokens") or 0)
                        tokens += int(usage.get("output_tokens") or 0)
                        if tokens <= 0:
                            continue
                        found = True
                        timestamp = obj.get("timestamp")
                        day_key = _parse_day(timestamp)
                        dt = _parse_iso(timestamp)
                        if day_key and dt:
                            day_totals[day_key] = day_totals.get(day_key, 0) + tokens
                            if latest_ts is None or dt > latest_ts:
                                latest_ts = dt
                                latest_day_total = day_totals[day_key]
            except OSError:
                continue

    if not found:
        return None

    rolling_total = 0
    for day_key, total in day_totals.items():
        try:
            if datetime.fromisoformat(day_key).date() >= since:
                rolling_total += total
        except Exception:
            continue

    return LocalUsageSnapshot(
        session_tokens=latest_day_total,
        last_30_days_tokens=rolling_total or None,
    )


def scan_vertex_local_usage() -> LocalUsageSnapshot | None:
    roots = [Path.home() / ".claude" / "projects", Path.home() / ".config" / "claude" / "projects"]
    since = (datetime.now(timezone.utc) - timedelta(days=29)).date()
    latest_ts = None
    latest_day_total = None
    day_totals: dict[str, int] = {}
    found = False

    for root in roots:
        if not root.exists():
            continue
        for path in glob.glob(str(root / "**" / "*.jsonl"), recursive=True):
            try:
                with open(path, errors="replace") as handle:
                    for line in handle:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            obj = json.loads(line)
                        except Exception:
                            continue
                        message = obj.get("message", {}) if isinstance(obj.get("message"), dict) else {}
                        usage = message.get("usage", {}) if isinstance(message.get("usage"), dict) else {}
                        if not usage:
                            continue
                        model = str(message.get("model") or "")
                        blob = json.dumps(obj).lower()
                        is_vertex = "@" in model or "vertex" in blob or "gcp" in blob
                        if not is_vertex:
                            continue
                        tokens = int(usage.get("input_tokens") or 0)
                        tokens += int(usage.get("cache_read_input_tokens") or 0)
                        tokens += int(usage.get("cache_creation_input_tokens") or 0)
                        tokens += int(usage.get("output_tokens") or 0)
                        if tokens <= 0:
                            continue
                        found = True
                        timestamp = obj.get("timestamp")
                        day_key = _parse_day(timestamp)
                        dt = _parse_iso(timestamp)
                        if day_key and dt:
                            day_totals[day_key] = day_totals.get(day_key, 0) + tokens
                            if latest_ts is None or dt > latest_ts:
                                latest_ts = dt
                                latest_day_total = day_totals[day_key]
            except OSError:
                continue

    if not found:
        return None

    rolling_total = 0
    for day_key, total in day_totals.items():
        try:
            if datetime.fromisoformat(day_key).date() >= since:
                rolling_total += total
        except Exception:
            continue

    return LocalUsageSnapshot(
        session_tokens=latest_day_total,
        last_30_days_tokens=rolling_total or None,
    )


def scan_opencode_local_usage() -> LocalUsageSnapshot | None:
    root = Path.home() / ".local" / "share" / "opencode" / "storage" / "message"
    if not root.exists():
        return None

    since = (datetime.now(timezone.utc) - timedelta(days=29)).date()
    latest_session_id = None
    latest_completed = None
    session_totals: dict[str, int] = {}
    day_totals: dict[str, int] = {}

    for path in glob.glob(str(root / "**" / "*.json"), recursive=True):
        try:
            obj = json.loads(Path(path).read_text(errors="replace"))
        except Exception:
            continue

        if not isinstance(obj, dict):
            continue
        if obj.get("providerID") != "opencode":
            continue

        tokens = obj.get("tokens") if isinstance(obj.get("tokens"), dict) else {}
        cache = tokens.get("cache") if isinstance(tokens.get("cache"), dict) else {}
        total_tokens = int(tokens.get("input") or 0)
        total_tokens += int(tokens.get("output") or 0)
        total_tokens += int(tokens.get("reasoning") or 0)
        total_tokens += int(cache.get("read") or 0)
        total_tokens += int(cache.get("write") or 0)
        if total_tokens <= 0:
            continue

        time_info = obj.get("time") if isinstance(obj.get("time"), dict) else {}
        completed_raw = time_info.get("completed")
        if completed_raw is None:
            continue

        try:
            completed = datetime.fromtimestamp(int(completed_raw) / 1000, tz=timezone.utc)
        except Exception:
            continue

        session_id = str(obj.get("sessionID") or "")
        if session_id:
            session_totals[session_id] = session_totals.get(session_id, 0) + total_tokens

        day_key = completed.date().isoformat()
        if completed.date() >= since:
            day_totals[day_key] = day_totals.get(day_key, 0) + total_tokens

        if latest_completed is None or completed > latest_completed:
            latest_completed = completed
            latest_session_id = session_id

    if latest_session_id is None and not day_totals:
        return None

    return LocalUsageSnapshot(
        session_tokens=session_totals.get(latest_session_id) if latest_session_id else None,
        last_30_days_tokens=sum(day_totals.values()) if day_totals else None,
    )
