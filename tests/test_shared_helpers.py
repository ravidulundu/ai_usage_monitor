from __future__ import annotations

from core.ai_usage_monitor.shared.http_failures import (
    classify_exception_failure,
    classify_http_failure,
    extract_api_message,
)
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
