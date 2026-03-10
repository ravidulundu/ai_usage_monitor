from __future__ import annotations

from typing import Any


LOCAL_SOURCE_IDS = {"cli", "local", "oauth", "local_cli"}
API_SOURCE_IDS = {"api"}
WEB_SOURCE_IDS = {"web"}


def norm_source(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text == "remote":
        return "web"
    return text or ""


def source_family(source_id: str) -> str:
    source = norm_source(source_id)
    if source in LOCAL_SOURCE_IDS:
        return "local_cli"
    if source in API_SOURCE_IDS:
        return "api"
    if source in WEB_SOURCE_IDS:
        return "web"
    return source


def source_token(source_id: str) -> str:
    source = norm_source(source_id)
    if source == "local_cli":
        return "LOCAL CLI"
    return source.upper()


def unique_strings(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item in seen or not item:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered
