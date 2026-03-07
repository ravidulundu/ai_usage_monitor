from __future__ import annotations

import os
from typing import Iterable


def normalize_cookie_header(raw: str | None) -> str | None:
    if not isinstance(raw, str):
        return None
    value = raw.strip()
    if not value:
        return None
    lower = value.lower()
    if lower.startswith("cookie:"):
        value = value.split(":", 1)[1].strip()
    return value or None


def cookie_header_from_settings(settings: dict | None, env_keys: Iterable[str] = ()) -> str | None:
    if settings:
        header = normalize_cookie_header(settings.get("manualCookieHeader"))
        if header:
            return header
    for env_key in env_keys:
        header = normalize_cookie_header(os.environ.get(env_key))
        if header:
            return header
    return None


def cookie_source_from_settings(settings: dict | None, default: str = "off") -> str:
    source = (settings or {}).get("cookieSource")
    if isinstance(source, str) and source in {"off", "manual", "auto"}:
        return source
    return default
