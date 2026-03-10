from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from core.ai_usage_monitor.runtime_cache import read_ttl_cache, write_ttl_cache


_COOKIE_CACHE_FILE = "browser_cookie_cache.json"
_COOKIE_CACHE_TTL_SECONDS = 60
_COOKIE_MISS_SENTINEL = {"miss": True}
_MEM_COOKIE_CACHE: dict[tuple[str, str], "BrowserCookieResult"] = {}


@dataclass(frozen=True)
class BrowserCookieResult:
    header: str
    source: str


@dataclass(frozen=True)
class CookieBackend:
    table: str
    host_column: str
    drop_empty_values: bool = False


def _copy_db(path: Path) -> Path | None:
    if not path.exists():
        return None
    try:
        temp_dir = Path(tempfile.mkdtemp(prefix="ai-usage-monitor-cookies-"))
        copied = temp_dir / path.name
        shutil.copy2(path, copied)
        wal = path.with_name(path.name + "-wal")
        shm = path.with_name(path.name + "-shm")
        if wal.exists():
            shutil.copy2(wal, temp_dir / wal.name)
        if shm.exists():
            shutil.copy2(shm, temp_dir / shm.name)
        return copied
    except Exception:
        return None


def _cookie_header_from_rows(rows: Iterable[tuple[str, str | None]]) -> str | None:
    pairs: list[str] = []
    seen: set[str] = set()
    for name, value in rows:
        if not name or value is None:
            continue
        pair = f"{name}={value}"
        if pair in seen:
            continue
        seen.add(pair)
        pairs.append(pair)
    return "; ".join(pairs) if pairs else None


def _firefox_paths() -> list[tuple[str, Path]]:
    profiles_root = Path.home() / ".mozilla" / "firefox"
    if not profiles_root.exists():
        return []
    paths = []
    for profile in profiles_root.iterdir():
        db = profile / "cookies.sqlite"
        if db.exists():
            paths.append((f"Firefox ({profile.name})", db))
    return paths


def _chromium_paths() -> list[tuple[str, Path]]:
    candidates = [
        ("Chrome", Path.home() / ".config" / "google-chrome"),
        ("Chromium", Path.home() / ".config" / "chromium"),
        ("Brave", Path.home() / ".config" / "BraveSoftware" / "Brave-Browser"),
        ("Edge", Path.home() / ".config" / "microsoft-edge"),
    ]
    paths = []
    for label, root in candidates:
        if not root.exists():
            continue
        for profile_name in ("Default", "Profile 1", "Profile 2", "Profile 3"):
            db = root / profile_name / "Cookies"
            if db.exists():
                paths.append((f"{label} ({profile_name})", db))
    return paths


def _fingerprint_paths(paths: Iterable[tuple[str, Path]]) -> str:
    items: list[dict[str, str | int]] = []
    for source, path in paths:
        try:
            stat_result = path.stat()
            items.append(
                {
                    "source": source,
                    "path": str(path),
                    "mtimeNs": stat_result.st_mtime_ns,
                    "size": stat_result.st_size,
                }
            )
        except OSError:
            items.append(
                {"source": source, "path": str(path), "mtimeNs": -1, "size": -1}
            )
    encoded = json.dumps(items, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _cookie_cache_key(
    domains: list[str],
    cookie_names: set[str] | None,
    firefox_paths: list[tuple[str, Path]],
    chromium_paths: list[tuple[str, Path]],
) -> tuple[str, str]:
    key_payload = {
        "domains": sorted(domains),
        "cookieNames": sorted(cookie_names) if cookie_names else [],
    }
    key = hashlib.sha256(
        json.dumps(key_payload, sort_keys=True).encode("utf-8")
    ).hexdigest()
    fingerprint = hashlib.sha256(
        json.dumps(
            {
                "firefox": _fingerprint_paths(firefox_paths),
                "chromium": _fingerprint_paths(chromium_paths),
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    return key, fingerprint


def _query_cookie_backend(
    *,
    db_path: Path,
    backend: CookieBackend,
    domains: list[str],
    cookie_names: set[str] | None,
) -> str | None:
    copied = _copy_db(db_path)
    if not copied:
        return None
    try:
        conn = sqlite3.connect(f"file:{copied}?mode=ro", uri=True)
        try:
            rows: list[tuple[str, str | None]] = []
            for domain in domains:
                like = "%" + domain.lstrip(".")
                if cookie_names:
                    placeholders = ",".join("?" for _ in cookie_names)
                    query = (
                        f"SELECT name, value FROM {backend.table} "
                        f"WHERE {backend.host_column} LIKE ? AND name IN ({placeholders})"
                    )
                    params = [like, *sorted(cookie_names)]
                else:
                    query = (
                        f"SELECT name, value FROM {backend.table} "
                        f"WHERE {backend.host_column} LIKE ?"
                    )
                    params = [like]
                for name, value in conn.execute(query, params).fetchall():
                    value_text = str(value) if value is not None else None
                    if backend.drop_empty_values and not value_text:
                        continue
                    rows.append((str(name), value_text))
            return _cookie_header_from_rows(rows)
        finally:
            conn.close()
    except Exception:
        return None
    finally:
        shutil.rmtree(copied.parent, ignore_errors=True)


def _query_firefox(
    db_path: Path, domains: list[str], cookie_names: set[str] | None
) -> str | None:
    return _query_cookie_backend(
        db_path=db_path,
        backend=CookieBackend(table="moz_cookies", host_column="host"),
        domains=domains,
        cookie_names=cookie_names,
    )


def _query_chromium(
    db_path: Path, domains: list[str], cookie_names: set[str] | None
) -> str | None:
    return _query_cookie_backend(
        db_path=db_path,
        backend=CookieBackend(
            table="cookies",
            host_column="host_key",
            drop_empty_values=True,
        ),
        domains=domains,
        cookie_names=cookie_names,
    )


def import_cookie_header(
    domains: list[str],
    cookie_names: set[str] | None = None,
    firefox_paths: list[tuple[str, Path]] | None = None,
    chromium_paths: list[tuple[str, Path]] | None = None,
) -> BrowserCookieResult | None:
    firefox_paths = firefox_paths if firefox_paths is not None else _firefox_paths()
    chromium_paths = chromium_paths if chromium_paths is not None else _chromium_paths()
    cache_key, fingerprint = _cookie_cache_key(
        domains, cookie_names, firefox_paths, chromium_paths
    )
    mem_key = (cache_key, fingerprint)
    mem_cached = _MEM_COOKIE_CACHE.get(mem_key)
    if mem_cached is not None:
        return mem_cached
    cached = read_ttl_cache(
        _COOKIE_CACHE_FILE,
        cache_key,
        _COOKIE_CACHE_TTL_SECONDS,
        fingerprint=fingerprint,
    )
    if isinstance(cached, dict):
        if cached.get("miss") is True:
            return None

    for source, path in chromium_paths:
        header = _query_chromium(path, domains, cookie_names)
        if header:
            result = BrowserCookieResult(header=header, source=source)
            _MEM_COOKIE_CACHE[mem_key] = result
            return result

    for source, path in firefox_paths:
        header = _query_firefox(path, domains, cookie_names)
        if header:
            result = BrowserCookieResult(header=header, source=source)
            _MEM_COOKIE_CACHE[mem_key] = result
            return result

    write_ttl_cache(
        _COOKIE_CACHE_FILE,
        cache_key,
        _COOKIE_MISS_SENTINEL,
        fingerprint=fingerprint,
    )
    return None
