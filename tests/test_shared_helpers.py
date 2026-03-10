from __future__ import annotations

import base64
import json
import urllib.parse
from pathlib import Path
from unittest import mock

from core.ai_usage_monitor.shared.http_failures import (
    classify_exception_failure,
    classify_http_failure,
    extract_api_message,
)
from core.ai_usage_monitor.shared.oauth import refresh_gemini_token
from core.ai_usage_monitor.shared.time_utils import unix_to_iso


def test_extract_api_message_reads_json_error_body():
    body = '{"error":{"message":"quota exceeded"}}'
    assert extract_api_message(body) == "quota exceeded"


def test_classify_http_failure_maps_auth_error():
    failure = classify_http_failure("openrouter", 401, '{"message":"invalid token"}')
    assert failure["fail_reason"] == "auth_required"
    assert "Authentication required" in failure["error"]


def test_classify_exception_failure_maps_timeout():
    failure = classify_exception_failure(TimeoutError("boom"))
    assert failure["fail_reason"] == "timeout"
    assert failure["error"] == "Request timed out"


def test_unix_to_iso_handles_timestamp_and_none():
    assert unix_to_iso(None) is None
    assert unix_to_iso(0) == "1970-01-01T00:00:00+00:00"


def _jwt_with_payload(payload: dict[str, str]) -> str:
    header = base64.urlsafe_b64encode(json.dumps({"alg": "none"}).encode()).decode()
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    return f"{header.rstrip('=')}.{body.rstrip('=')}."


class _FakeUrlOpenResponse:
    def __init__(self, payload: dict[str, object]):
        self._payload = payload

    def __enter__(self) -> "_FakeUrlOpenResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


def test_refresh_gemini_token_uses_client_id_from_id_token_when_missing(
    tmp_path: Path,
) -> None:
    creds_path = tmp_path / "oauth_creds.json"
    captured: dict[str, str] = {}

    def fake_urlopen(request, timeout=10):  # noqa: ANN001
        assert timeout == 10
        captured["body"] = request.data.decode("utf-8")
        return _FakeUrlOpenResponse({"access_token": "fresh-token", "expires_in": 1200})

    with mock.patch(
        "core.ai_usage_monitor.shared.oauth._gemini_oauth2_js_candidates",
        return_value=[],
    ):
        with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
            ok, refreshed, error = refresh_gemini_token(
                creds_path,
                {
                    "refresh_token": "refresh-token",
                    "id_token": _jwt_with_payload({"aud": "gemini-client-id"}),
                },
            )

    assert ok is True
    assert error is None
    assert isinstance(refreshed, dict)
    params = urllib.parse.parse_qs(captured["body"])
    assert params["client_id"] == ["gemini-client-id"]
    assert params["refresh_token"] == ["refresh-token"]
    assert "client_secret" not in params
    saved = json.loads(creds_path.read_text())
    assert saved["client_id"] == "gemini-client-id"
    assert saved["access_token"] == "fresh-token"
    assert isinstance(saved.get("expiry_date"), int)


def test_refresh_gemini_token_fails_when_client_id_cannot_be_resolved(
    tmp_path: Path,
) -> None:
    with mock.patch(
        "core.ai_usage_monitor.shared.oauth._gemini_oauth2_js_candidates",
        return_value=[],
    ):
        ok, refreshed, error = refresh_gemini_token(
            tmp_path / "oauth_creds.json",
            {"refresh_token": "refresh-token"},
        )
    assert ok is False
    assert refreshed is None
    assert error == "Missing OAuth client id"


def test_refresh_gemini_token_loads_client_credentials_from_cli_oauth2_js(
    tmp_path: Path,
) -> None:
    creds_path = tmp_path / "oauth_creds.json"
    oauth_js = tmp_path / "oauth2.js"
    oauth_js.write_text(
        "\n".join(
            [
                "const OAUTH_CLIENT_ID = 'cli-client-id';",
                "const OAUTH_CLIENT_SECRET = 'cli-client-secret';",
            ]
        ),
        encoding="utf-8",
    )
    captured: dict[str, str] = {}

    def fake_urlopen(request, timeout=10):  # noqa: ANN001
        assert timeout == 10
        captured["body"] = request.data.decode("utf-8")
        return _FakeUrlOpenResponse({"access_token": "fresh-token", "expires_in": 1200})

    with mock.patch(
        "core.ai_usage_monitor.shared.oauth._gemini_oauth2_js_candidates",
        return_value=[oauth_js],
    ):
        with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
            ok, refreshed, error = refresh_gemini_token(
                creds_path,
                {"refresh_token": "refresh-token"},
            )

    assert ok is True
    assert error is None
    assert isinstance(refreshed, dict)
    params = urllib.parse.parse_qs(captured["body"])
    assert params["client_id"] == ["cli-client-id"]
    assert params["client_secret"] == ["cli-client-secret"]
