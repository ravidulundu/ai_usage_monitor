from __future__ import annotations

import json
import os
import time
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any


def runtime_cache_dir() -> Path:
    state_dir = os.environ.get("AI_USAGE_MONITOR_STATE_DIR")
    if state_dir and state_dir.strip():
        return Path(state_dir).expanduser()
    return Path.home() / ".cache" / "ai-usage-monitor"


def runtime_cache_path(filename: str) -> Path:
    return runtime_cache_dir() / filename


def load_runtime_cache(filename: str) -> dict[str, Any]:
    path = runtime_cache_path(filename)
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text())
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def save_runtime_cache(filename: str, payload: dict[str, Any]) -> None:
    path = runtime_cache_path(filename)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=str(path.parent),
            delete=False,
        ) as handle:
            handle.write(json.dumps(payload))
            tmp_path = Path(handle.name)
        os.replace(tmp_path, path)
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
    except OSError:
        return


def read_ttl_cache(
    filename: str,
    key: str,
    ttl_seconds: int,
    *,
    fingerprint: str | None = None,
    now: float | None = None,
) -> Any:
    cache = load_runtime_cache(filename)
    entry = cache.get(key)
    if not isinstance(entry, dict):
        return None
    cached_at = entry.get("cachedAt")
    if not isinstance(cached_at, (int, float)):
        return None
    if fingerprint is not None and entry.get("fingerprint") != fingerprint:
        return None
    current_time = time.time() if now is None else now
    if current_time - float(cached_at) > ttl_seconds:
        return None
    return entry.get("value")


def write_ttl_cache(
    filename: str,
    key: str,
    value: Any,
    *,
    fingerprint: str | None = None,
    now: float | None = None,
) -> None:
    cache = load_runtime_cache(filename)
    cache[key] = {
        "cachedAt": time.time() if now is None else now,
        "value": value,
        **({"fingerprint": fingerprint} if fingerprint is not None else {}),
    }
    save_runtime_cache(filename, cache)
