from __future__ import annotations

import json
import socket
import urllib.error
from typing import Any


def read_http_error_body(err: Any) -> str:
    """Read and decode HTTP error body safely."""
    try:
        body = err.read()
        if isinstance(body, bytes):
            return body.decode("utf-8", errors="replace")
        return str(body or "")
    except Exception:
        return ""


def extract_api_message(body: str | None) -> str:
    """Extract a compact API message from JSON/text error bodies."""
    if not body:
        return ""
    try:
        obj = json.loads(body)
        if isinstance(obj, dict):
            if isinstance(obj.get("error"), dict):
                err = obj["error"]
                return str(err.get("message") or err.get("status") or "").strip()
            return str(obj.get("message") or "").strip()
    except Exception:
        pass
    return body.strip().splitlines()[0][:180]


def classify_http_failure(
    provider: str,
    code: int,
    body: str = "",
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Normalize HTTP failures into user-facing messages.
    SECURITY: never exposes full bodies that might contain sensitive data.
    """
    _ = provider
    _ = context or {}
    api_msg = extract_api_message(body)
    fail_reason = "http_error"
    error = f"HTTP {code}"

    if code == 401:
        fail_reason = "auth_required"
        error = "Authentication required"
    elif code == 403:
        fail_reason = "forbidden"
        error = "Permission denied"
    elif code == 404:
        fail_reason = "not_found"
        error = "API endpoint not found"
    elif code == 429:
        fail_reason = "rate_limited"
        error = "Rate limited"
    elif 500 <= code <= 599:
        fail_reason = "server_error"
        error = "Provider service error"

    if api_msg:
        error = f"{error}: {api_msg}"

    return {
        "fail_reason": fail_reason,
        "http_code": code,
        "error": error,
    }


def classify_exception_failure(err: Exception) -> dict[str, Any]:
    """Normalize non-HTTP network/runtime failures."""
    if isinstance(err, urllib.error.URLError):
        reason = getattr(err, "reason", None)
        if isinstance(reason, (TimeoutError, socket.timeout)):
            return {"fail_reason": "timeout", "error": "Request timed out"}
        return {"fail_reason": "network_error", "error": f"Network error: {reason}"}
    if isinstance(err, TimeoutError):
        return {"fail_reason": "timeout", "error": "Request timed out"}
    if isinstance(err, KeyError):
        return {
            "fail_reason": "invalid_credentials",
            "error": f"Missing credential field: {err}",
        }
    return {"fail_reason": "unknown_error", "error": str(err)}
