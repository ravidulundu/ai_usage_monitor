from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def refresh_gemini_token(
    creds_path: Path, creds: dict[str, Any]
) -> tuple[bool, dict[str, Any] | None, str | None]:
    """
    Refresh Gemini OAuth token using refresh_token.
    Returns: (success, new_creds, error_msg)
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

        new_creds = dict(creds)
        new_creds["access_token"] = token_data["access_token"]

        if "expires_in" in token_data:
            new_creds["expiry"] = (
                int(datetime.now(timezone.utc).timestamp()) + token_data["expires_in"]
            )

        creds_path.write_text(json.dumps(new_creds, indent=2))

        return True, new_creds, None

    except urllib.error.HTTPError as err:
        if err.code == 400:
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
