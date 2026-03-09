from __future__ import annotations

import base64
import json
import re
import shutil
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_OAUTH_CLIENT_ID_RE = re.compile(r"OAUTH_CLIENT_ID\s*=\s*['\"]([^'\"]+)['\"]")
_OAUTH_CLIENT_SECRET_RE = re.compile(r"OAUTH_CLIENT_SECRET\s*=\s*['\"]([^'\"]+)['\"]")


def _decode_jwt_payload(token: str) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) < 2:
        return {}
    payload_segment = parts[1]
    # JWT uses URL-safe base64 without padding.
    padded = payload_segment + "=" * (-len(payload_segment) % 4)
    try:
        decoded = base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8")
        payload = json.loads(decoded)
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _resolve_gemini_client_id_from_creds(creds: dict[str, Any]) -> str:
    for key in ("client_id", "clientId"):
        value = str(creds.get(key) or "").strip()
        if value:
            return value

    id_token = str(creds.get("id_token") or "").strip()
    if id_token:
        claims = _decode_jwt_payload(id_token)
        for key in ("aud", "azp"):
            value = str(claims.get(key) or "").strip()
            if value:
                return value
    return ""


def _gemini_oauth2_js_candidates() -> list[Path]:
    binary = shutil.which("gemini")
    if not binary:
        return []
    resolved = Path(binary).resolve()
    roots: list[Path] = []
    if resolved.suffix == ".js" and resolved.parent.name == "dist":
        roots.append(resolved.parent.parent)
    roots.extend(resolved.parents)

    candidates: list[Path] = []
    seen: set[str] = set()
    suffixes = (
        "node_modules/@google/gemini-cli-core/dist/src/code_assist/oauth2.js",
        "node_modules/@google/gemini-cli/node_modules/@google/gemini-cli-core/dist/src/code_assist/oauth2.js",
        "lib/node_modules/@google/gemini-cli/node_modules/@google/gemini-cli-core/dist/src/code_assist/oauth2.js",
        "libexec/lib/node_modules/@google/gemini-cli/node_modules/@google/gemini-cli-core/dist/src/code_assist/oauth2.js",
    )
    for root in roots:
        for suffix in suffixes:
            path = root / suffix
            key = str(path)
            if key in seen:
                continue
            seen.add(key)
            candidates.append(path)
    return candidates


def _extract_oauth_credentials_from_js_file(path: Path) -> tuple[str, str]:
    try:
        source = path.read_text(encoding="utf-8")
    except Exception:
        return "", ""
    client_id_match = _OAUTH_CLIENT_ID_RE.search(source)
    client_secret_match = _OAUTH_CLIENT_SECRET_RE.search(source)
    client_id = client_id_match.group(1).strip() if client_id_match else ""
    client_secret = client_secret_match.group(1).strip() if client_secret_match else ""
    return client_id, client_secret


def _resolve_gemini_client_credentials(creds: dict[str, Any]) -> tuple[str, str]:
    client_id = _resolve_gemini_client_id_from_creds(creds)
    client_secret = str(
        creds.get("client_secret") or creds.get("clientSecret") or ""
    ).strip()
    if client_id and client_secret:
        return client_id, client_secret

    for candidate in _gemini_oauth2_js_candidates():
        if not candidate.exists():
            continue
        parsed_id, parsed_secret = _extract_oauth_credentials_from_js_file(candidate)
        if not client_id and parsed_id:
            client_id = parsed_id
        if not client_secret and parsed_secret:
            client_secret = parsed_secret
        if client_id and client_secret:
            break

    return client_id, client_secret


def _oauth_error_description(err: urllib.error.HTTPError) -> str:
    try:
        body = err.read().decode("utf-8")
    except Exception:
        return ""
    try:
        payload = json.loads(body)
    except Exception:
        return body
    if not isinstance(payload, dict):
        return body
    return str(payload.get("error_description") or payload.get("error") or body)


def refresh_gemini_token(
    creds_path: Path, creds: dict[str, Any]
) -> tuple[bool, dict[str, Any] | None, str | None]:
    """
    Refresh Gemini OAuth token using refresh_token.
    Returns: (success, new_creds, error_msg)
    """
    try:
        refresh_token = creds.get("refresh_token")
        client_id, client_secret = _resolve_gemini_client_credentials(creds)

        if not refresh_token:
            return False, None, "No refresh token found"
        if not client_id:
            return False, None, "Missing OAuth client id"

        token_url = "https://oauth2.googleapis.com/token"
        payload = {
            "client_id": client_id,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        # Google token endpoint currently requires client secret for Gemini CLI OAuth.
        if client_secret:
            payload["client_secret"] = client_secret
        data = urllib.parse.urlencode(payload).encode()

        req = urllib.request.Request(
            token_url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            token_data = json.loads(resp.read())

        new_creds = dict(creds)
        new_creds["access_token"] = token_data["access_token"]
        new_creds["client_id"] = client_id
        if client_secret:
            new_creds["client_secret"] = client_secret

        if "expires_in" in token_data:
            expires_at_seconds = int(datetime.now(timezone.utc).timestamp()) + int(
                token_data["expires_in"]
            )
            new_creds["expiry"] = expires_at_seconds
            # Gemini CLI credential file uses epoch milliseconds.
            new_creds["expiry_date"] = expires_at_seconds * 1000

        creds_path.write_text(json.dumps(new_creds, indent=2))

        return True, new_creds, None

    except urllib.error.HTTPError as err:
        description = _oauth_error_description(err).lower()
        if err.code == 400:
            if "client_secret" in description and "missing" in description:
                return (
                    False,
                    None,
                    "Missing OAuth client secret",
                )
            return (
                False,
                None,
                "Refresh token expired - please re-authenticate Gemini CLI",
            )
        if err.code == 401:
            return (
                False,
                None,
                "Authentication failed - please re-authenticate Gemini CLI",
            )
        return False, None, f"Token refresh failed (HTTP {err.code})"
    except Exception as err:
        return False, None, f"Token refresh error: {type(err).__name__}"
