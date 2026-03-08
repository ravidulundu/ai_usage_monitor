from __future__ import annotations

"""
Compatibility shim for legacy imports.

New code should import from:
- core.ai_usage_monitor.shared.http_failures
- core.ai_usage_monitor.shared.oauth
- core.ai_usage_monitor.shared.time_utils
"""

from core.ai_usage_monitor.shared.http_failures import (
    classify_exception_failure,
    classify_http_failure,
    extract_api_message,
    read_http_error_body,
)
from core.ai_usage_monitor.shared.oauth import refresh_gemini_token
from core.ai_usage_monitor.shared.time_utils import unix_to_iso

__all__ = [
    "unix_to_iso",
    "read_http_error_body",
    "extract_api_message",
    "classify_http_failure",
    "classify_exception_failure",
    "refresh_gemini_token",
]
