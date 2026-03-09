from __future__ import annotations

from urllib.parse import urlparse


def env_flag_enabled(value: str | None) -> bool:
    text = str(value or "").strip().lower()
    return text in {"1", "true", "yes", "on"}


def resolve_safe_url(
    raw_url: str | None,
    *,
    default_url: str,
    allowed_hosts: tuple[str, ...],
    allow_unsafe: bool,
) -> str:
    value = str(raw_url or "").strip()
    if not value:
        return default_url.rstrip("/")

    parsed = urlparse(value)
    host = str(parsed.hostname or "").strip().lower()
    if not host:
        return default_url.rstrip("/")

    scheme = str(parsed.scheme or "").strip().lower()
    if allow_unsafe:
        if scheme not in {"http", "https"}:
            return default_url.rstrip("/")
        return value.rstrip("/")

    if scheme != "https":
        return default_url.rstrip("/")

    normalized_hosts = tuple(
        str(item).strip().lower() for item in allowed_hosts if item
    )
    if not normalized_hosts:
        return default_url.rstrip("/")
    if host in normalized_hosts or any(
        host.endswith(f".{allowed}") for allowed in normalized_hosts
    ):
        return value.rstrip("/")
    return default_url.rstrip("/")
