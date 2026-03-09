from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator

from core.ai_usage_monitor.models import LocalUsageSnapshot
from core.ai_usage_monitor.runtime_cache import read_ttl_cache, write_ttl_cache


_LOCAL_USAGE_CACHE_FILE = "local_usage_cache.json"
_LOCAL_USAGE_CACHE_TTL_SECONDS = 3600


def _parse_iso(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _parse_day(ts: str | None) -> str | None:
    dt = _parse_iso(ts)
    return dt.date().isoformat() if dt else None


def _iter_files(root: Path, pattern: str) -> Iterator[Path]:
    try:
        yield from root.rglob(pattern)
    except OSError:
        return


def _file_tree_fingerprint(roots: Iterable[Path], pattern: str) -> str:
    items: list[tuple[str, int, int]] = []
    for root in roots:
        if not root.exists():
            continue
        for path in _iter_files(root, pattern):
            try:
                stat_result = path.stat()
            except OSError:
                continue
            items.append((str(path), stat_result.st_mtime_ns, stat_result.st_size))
    encoded = json.dumps(items, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _cached_local_usage(
    cache_key: str,
    fingerprint: str,
) -> LocalUsageSnapshot | None:
    cached = read_ttl_cache(
        _LOCAL_USAGE_CACHE_FILE,
        cache_key,
        _LOCAL_USAGE_CACHE_TTL_SECONDS,
        fingerprint=fingerprint,
    )
    return LocalUsageSnapshot.from_dict(cached)


def _store_local_usage(
    cache_key: str,
    fingerprint: str,
    snapshot: LocalUsageSnapshot | None,
) -> None:
    if snapshot is None:
        return
    write_ttl_cache(
        _LOCAL_USAGE_CACHE_FILE,
        cache_key,
        snapshot.to_dict(),
        fingerprint=fingerprint,
    )


def _claude_usage_roots() -> list[Path]:
    return [
        Path.home() / ".claude" / "projects",
        Path.home() / ".config" / "claude" / "projects",
    ]


def _existing_roots(roots: Iterable[Path]) -> list[Path]:
    return [root for root in roots if root.exists()]


def _iter_jsonl_objects(roots: Iterable[Path]) -> Iterator[dict[str, Any]]:
    for root in roots:
        for path in _iter_files(root, "*.jsonl"):
            try:
                with open(path, errors="replace") as handle:
                    for line in handle:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            record = json.loads(line)
                        except Exception:
                            continue
                        if isinstance(record, dict):
                            yield record
            except OSError:
                continue


def _message_usage_tokens(record: dict[str, Any]) -> int | None:
    message = (
        record.get("message", {}) if isinstance(record.get("message"), dict) else {}
    )
    usage = message.get("usage", {}) if isinstance(message.get("usage"), dict) else {}
    if not usage:
        return None

    def _coerce_token_count(value: Any) -> int:
        try:
            parsed = int(value or 0)
        except (TypeError, ValueError):
            return 0
        return parsed if parsed > 0 else 0

    tokens = _coerce_token_count(usage.get("input_tokens"))
    tokens += _coerce_token_count(usage.get("cache_read_input_tokens"))
    tokens += _coerce_token_count(usage.get("cache_creation_input_tokens"))
    tokens += _coerce_token_count(usage.get("output_tokens"))
    return tokens if tokens > 0 else None


def _build_daily_snapshot(
    records: Iterable[dict[str, Any]],
    *,
    include_record: Callable[[dict[str, Any]], bool],
) -> LocalUsageSnapshot | None:
    since = (datetime.now(timezone.utc) - timedelta(days=29)).date()
    latest_ts = None
    latest_day_total = None
    day_totals: dict[str, int] = {}
    found = False

    for record in records:
        if not include_record(record):
            continue
        tokens = _message_usage_tokens(record)
        if tokens is None:
            continue
        found = True
        timestamp = record.get("timestamp")
        day_key = _parse_day(timestamp)
        dt = _parse_iso(timestamp)
        if day_key and dt:
            day_totals[day_key] = day_totals.get(day_key, 0) + tokens
            if latest_ts is None or dt > latest_ts:
                latest_ts = dt
                latest_day_total = day_totals[day_key]

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


def _scan_cached_message_usage(
    *,
    cache_key: str,
    roots: list[Path],
    include_record: Callable[[dict[str, Any]], bool],
) -> LocalUsageSnapshot | None:
    existing_roots = _existing_roots(roots)
    if not existing_roots:
        return None
    fingerprint = _file_tree_fingerprint(existing_roots, "*.jsonl")
    cached = _cached_local_usage(cache_key, fingerprint)
    if cached is not None:
        return cached
    snapshot = _build_daily_snapshot(
        _iter_jsonl_objects(existing_roots),
        include_record=include_record,
    )
    _store_local_usage(cache_key, fingerprint, snapshot)
    return snapshot


def _is_vertex_message(record: dict[str, Any]) -> bool:
    message = (
        record.get("message", {}) if isinstance(record.get("message"), dict) else {}
    )
    model = str(message.get("model") or "")
    blob = json.dumps(record).lower()
    return "@" in model or "vertex" in blob or "gcp" in blob


def scan_codex_local_usage(
    min_timestamp: str | datetime | None = None,
    files: Iterable[Path] | None = None,
) -> LocalUsageSnapshot | None:
    root = Path.home() / ".codex" / "sessions"
    if not root.exists():
        return None

    cutoff_dt = _parse_iso(
        min_timestamp.isoformat()
        if isinstance(min_timestamp, datetime)
        else min_timestamp
    )
    since = (datetime.now(timezone.utc) - timedelta(days=29)).date()
    latest_ts = None
    latest_tokens = None
    day_totals: dict[str, int] = {}

    file_iter = files if files is not None else _iter_files(root, "*.jsonl")
    for path in file_iter:
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
                    payload = (
                        obj.get("payload", {})
                        if isinstance(obj.get("payload"), dict)
                        else {}
                    )
                    if (
                        obj.get("type") != "event_msg"
                        or payload.get("type") != "token_count"
                    ):
                        continue
                    info = (
                        payload.get("info", {})
                        if isinstance(payload.get("info"), dict)
                        else {}
                    )
                    totals = (
                        info.get("total_token_usage", {})
                        if isinstance(info.get("total_token_usage"), dict)
                        else {}
                    )
                    total_tokens = totals.get("total_tokens")
                    timestamp = obj.get("timestamp")
                    if total_tokens is None:
                        continue
                    dt = _parse_iso(timestamp)
                    if dt is None:
                        continue
                    if cutoff_dt and dt < cutoff_dt:
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
    return _scan_cached_message_usage(
        cache_key="claude",
        roots=_claude_usage_roots(),
        include_record=lambda _record: True,
    )


def scan_vertex_local_usage() -> LocalUsageSnapshot | None:
    return _scan_cached_message_usage(
        cache_key="vertexai",
        roots=_claude_usage_roots(),
        include_record=_is_vertex_message,
    )


def scan_opencode_local_usage() -> LocalUsageSnapshot | None:
    roots = [
        Path.home() / ".local" / "share" / "opencode" / "storage" / "message",
        Path.home() / ".config" / "opencode" / "storage" / "message",
    ]
    existing_roots = [root for root in roots if root.exists()]
    if not existing_roots:
        return None
    fingerprint = _file_tree_fingerprint(existing_roots, "*.json")
    cached = _cached_local_usage("opencode", fingerprint)
    if cached is not None:
        return cached

    since = (datetime.now(timezone.utc) - timedelta(days=29)).date()
    latest_session_id = None
    latest_completed = None
    session_totals: dict[str, int] = {}
    day_totals: dict[str, int] = {}

    for root in existing_roots:
        for path in _iter_files(root, "*.json"):
            try:
                with open(path, errors="replace") as handle:
                    obj = json.load(handle)
            except Exception:
                continue

            if not isinstance(obj, dict):
                continue
            if obj.get("providerID") != "opencode":
                continue

            raw_tokens = obj.get("tokens")
            tokens: dict[str, Any] = raw_tokens if isinstance(raw_tokens, dict) else {}
            raw_cache = tokens.get("cache")
            cache: dict[str, Any] = raw_cache if isinstance(raw_cache, dict) else {}
            total_tokens = int(tokens.get("input") or 0)
            total_tokens += int(tokens.get("output") or 0)
            total_tokens += int(tokens.get("reasoning") or 0)
            total_tokens += int(cache.get("read") or 0)
            total_tokens += int(cache.get("write") or 0)
            if total_tokens <= 0:
                continue

            raw_time_info = obj.get("time")
            time_info: dict[str, Any] = (
                raw_time_info if isinstance(raw_time_info, dict) else {}
            )
            completed_raw = time_info.get("completed")
            if completed_raw is None:
                continue

            try:
                completed = datetime.fromtimestamp(
                    int(completed_raw) / 1000, tz=timezone.utc
                )
            except Exception:
                continue

            session_id = str(obj.get("sessionID") or "")
            if session_id:
                session_totals[session_id] = (
                    session_totals.get(session_id, 0) + total_tokens
                )

            day_key = completed.date().isoformat()
            if completed.date() >= since:
                day_totals[day_key] = day_totals.get(day_key, 0) + total_tokens

            if latest_completed is None or completed > latest_completed:
                latest_completed = completed
                latest_session_id = session_id

    if latest_session_id is None and not day_totals:
        return None

    snapshot = LocalUsageSnapshot(
        session_tokens=session_totals.get(latest_session_id)
        if latest_session_id
        else None,
        last_30_days_tokens=sum(day_totals.values()) if day_totals else None,
    )
    _store_local_usage("opencode", fingerprint, snapshot)
    return snapshot
