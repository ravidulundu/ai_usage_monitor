from __future__ import annotations

import shutil
import sqlite3
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class BrowserCookieResult:
    header: str
    source: str


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


def _query_firefox(
    db_path: Path, domains: list[str], cookie_names: set[str] | None
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
                        "SELECT name, value FROM moz_cookies "
                        f"WHERE host LIKE ? AND name IN ({placeholders})"
                    )
                    params = [like, *sorted(cookie_names)]
                else:
                    query = "SELECT name, value FROM moz_cookies WHERE host LIKE ?"
                    params = [like]
                fetched = conn.execute(query, params).fetchall()
                for name, value in fetched:
                    rows.append(
                        (
                            str(name),
                            str(value) if value is not None else None,
                        )
                    )
            return _cookie_header_from_rows(rows)
        finally:
            conn.close()
    except Exception:
        return None
    finally:
        shutil.rmtree(copied.parent, ignore_errors=True)


def _query_chromium(
    db_path: Path, domains: list[str], cookie_names: set[str] | None
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
                        "SELECT name, value FROM cookies "
                        f"WHERE host_key LIKE ? AND name IN ({placeholders})"
                    )
                    params = [like, *sorted(cookie_names)]
                else:
                    query = "SELECT name, value FROM cookies WHERE host_key LIKE ?"
                    params = [like]
                fetched = conn.execute(query, params).fetchall()
                for name, value in fetched:
                    value_text = str(value) if value is not None else None
                    if value_text:
                        rows.append((str(name), value_text))
            return _cookie_header_from_rows(rows)
        finally:
            conn.close()
    except Exception:
        return None
    finally:
        shutil.rmtree(copied.parent, ignore_errors=True)


def import_cookie_header(
    domains: list[str],
    cookie_names: set[str] | None = None,
    firefox_paths: list[tuple[str, Path]] | None = None,
    chromium_paths: list[tuple[str, Path]] | None = None,
) -> BrowserCookieResult | None:
    firefox_paths = firefox_paths if firefox_paths is not None else _firefox_paths()
    chromium_paths = chromium_paths if chromium_paths is not None else _chromium_paths()

    for source, path in chromium_paths:
        header = _query_chromium(path, domains, cookie_names)
        if header:
            return BrowserCookieResult(header=header, source=source)

    for source, path in firefox_paths:
        header = _query_firefox(path, domains, cookie_names)
        if header:
            return BrowserCookieResult(header=header, source=source)

    return None
