from __future__ import annotations

import json
import socket
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def unix_to_iso(ts):
    """Convert Unix timestamp (int) to ISO 8601 string."""
    if ts is None:
        return None
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat()
    except Exception:
        return str(ts)


def read_http_error_body(err):
    """Read and decode HTTP error body safely."""
    try:
        body = err.read()
        if isinstance(body, bytes):
            return body.decode("utf-8", errors="replace")
        return str(body or "")
    except Exception:
        return ""


def extract_api_message(body):
    """Extract a useful API message from JSON/text error bodies."""
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


def classify_http_failure(provider, code, body="", context=None):
    """
    Normalize HTTP failures into user-facing messages.
    SECURITY: Never exposes full error bodies that might contain sensitive data.
    """
    context = context or {}
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


def classify_exception_failure(err):
    """Normalize non-HTTP failures."""
    if isinstance(err, urllib.error.URLError):
        reason = getattr(err, "reason", None)
        if isinstance(reason, (TimeoutError, socket.timeout)):
            return {"fail_reason": "timeout", "error": "Request timed out"}
        return {"fail_reason": "network_error", "error": f"Network error: {reason}"}
    if isinstance(err, TimeoutError):
        return {"fail_reason": "timeout", "error": "Request timed out"}
    if isinstance(err, KeyError):
        return {"fail_reason": "invalid_credentials", "error": f"Missing credential field: {err}"}
    return {"fail_reason": "unknown_error", "error": str(err)}


def refresh_gemini_token(creds_path: Path, creds: dict):
    """
    Refresh Gemini OAuth token using refresh_token.
    Returns (success: bool, new_creds: dict | None, error_msg: str | None)
    """
    try:
        refresh_token = creds.get("refresh_token")
        client_id = creds.get("client_id")
        client_secret = creds.get("client_secret")

        if not refresh_token:
            return False, None, "No refresh token found"
        if not client_id or not client_secret:
            return False, None, "Missing OAuth client credentials"

        token_url = "https://oauth2.googleapis.com/token"
        data = urllib.parse.urlencode(
            {
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            }
        ).encode()

        req = urllib.request.Request(
            token_url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            token_data = json.loads(resp.read())

        new_creds = creds.copy()
        new_creds["access_token"] = token_data["access_token"]

        if "expires_in" in token_data:
            new_creds["expiry"] = int(datetime.now(timezone.utc).timestamp()) + token_data["expires_in"]

        creds_path.write_text(json.dumps(new_creds, indent=2))

        return True, new_creds, None

    except urllib.error.HTTPError as err:
        if err.code == 400:
            return False, None, "Refresh token expired - please re-authenticate Gemini CLI"
        if err.code == 401:
            return False, None, "Authentication failed - please re-authenticate Gemini CLI"
        return False, None, f"Token refresh failed (HTTP {err.code})"
    except Exception as err:
        return False, None, f"Token refresh error: {type(err).__name__}"
