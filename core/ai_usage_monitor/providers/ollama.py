from __future__ import annotations

import re
import urllib.error
import urllib.request

from core.ai_usage_monitor.browser_cookies import import_cookie_header
from core.ai_usage_monitor.cookies import cookie_header_from_settings, cookie_source_from_settings
from core.ai_usage_monitor.models import MetricWindow, ProviderState
from core.ai_usage_monitor.providers.base import ProviderBranding, ProviderConfigField, ProviderDescriptor
from core.ai_usage_monitor.util import classify_exception_failure, classify_http_failure, read_http_error_body


DESCRIPTOR = ProviderDescriptor(
    id="ollama",
    display_name="Ollama",
    default_enabled=True,
    source_modes=("web",),
    config_fields=(
        ProviderConfigField("cookieSource", "Cookie Source", kind="choice", options=("off", "manual", "auto")),
        ProviderConfigField("manualCookieHeader", "Manual Cookie Header", secret=True, placeholder="session=..."),
    ),
    branding=ProviderBranding(icon_key="ollama", asset_name="ollama.svg", color="#888888", badge_text="OL"),
)


def _first_capture(text: str, pattern: str, flags=0):
    match = re.search(pattern, text, flags)
    return match.group(1).strip() if match else None


def parse_ollama_html(html: str) -> dict:
    lower = html.lower()
    if "sign in to ollama" in lower or "log in to ollama" in lower:
        raise PermissionError("Not logged in to Ollama. Please log in via ollama.com/settings.")

    plan = _first_capture(html, r"Cloud Usage\s*</span>\s*<span[^>]*>([^<]+)</span>", re.DOTALL)
    email = _first_capture(html, r'id="header-email"[^>]*>([^<]+)<', re.DOTALL)

    def usage_block(labels):
        if isinstance(labels, str):
            labels = [labels]
        for label in labels:
            idx = html.find(label)
            if idx == -1:
                continue
            window = html[idx:idx + 900]
            used = _first_capture(window, r"([0-9]+(?:\.[0-9]+)?)\s*%\s*used", re.IGNORECASE)
            if used is None:
                used = _first_capture(window, r"width:\s*([0-9]+(?:\.[0-9]+)?)%", re.IGNORECASE)
            if used is None:
                continue
            reset = _first_capture(window, r'data-time="([^"]+)"')
            return {"used": float(used), "reset": reset}
        return None

    session = usage_block(["Session usage", "Hourly usage"])
    weekly = usage_block("Weekly usage")

    if session is None and weekly is None:
        raise ValueError("Missing Ollama usage data.")

    return {
        "plan": plan,
        "email": email if email and "@" in email else None,
        "session": session,
        "weekly": weekly,
    }


def collect_ollama(settings: dict | None = None) -> tuple[dict, ProviderState]:
    cookie_source = cookie_source_from_settings(settings, default="off")
    if cookie_source == "off":
        return {"installed": False}, ProviderState(id=DESCRIPTOR.id, display_name=DESCRIPTOR.display_name, installed=False, source="web")

    cookie_header = cookie_header_from_settings(settings, env_keys=("OLLAMA_COOKIE_HEADER",))
    source_label = "manual"
    if not cookie_header and cookie_source == "auto":
        result = import_cookie_header(
            domains=["ollama.com", "www.ollama.com"],
            cookie_names={
                "session",
                "ollama_session",
                "__Host-ollama_session",
                "__Secure-next-auth.session-token",
                "next-auth.session-token",
            },
        )
        if result:
            cookie_header = result.header
            source_label = result.source
    if not cookie_header:
        return {"installed": False}, ProviderState(id=DESCRIPTOR.id, display_name=DESCRIPTOR.display_name, installed=False, source="web")

    try:
        req = urllib.request.Request(
            "https://ollama.com/settings",
            headers={
                "Cookie": cookie_header,
                "Accept": "text/html,application/xhtml+xml",
                "User-Agent": "AIUsageMonitor/1.0",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        parsed = parse_ollama_html(html)
        session = parsed.get("session")
        weekly = parsed.get("weekly")
        legacy = {
            "installed": True,
            "plan": parsed.get("plan"),
            "session_used_pct": session.get("used") if session else None,
            "weekly_used_pct": weekly.get("used") if weekly else None,
            "cookie_source": source_label,
        }
        state = ProviderState(
            id=DESCRIPTOR.id,
            display_name=DESCRIPTOR.display_name,
            installed=True,
            authenticated=True,
            source="web",
            primary_metric=MetricWindow("Session", session["used"], session.get("reset")) if session else None,
            secondary_metric=MetricWindow("Weekly", weekly["used"], weekly.get("reset")) if weekly else None,
            extras={"plan": parsed.get("plan") or "", "model": parsed.get("email") or source_label},
        )
        return legacy, state
    except PermissionError as err:
        legacy = {"installed": True, "error": str(err), "fail_reason": "auth_required"}
    except urllib.error.HTTPError as err:
        legacy = {"installed": True, **classify_http_failure("ollama", err.code, read_http_error_body(err))}
    except Exception as err:
        legacy = {"installed": True, **classify_exception_failure(err)}

    state = ProviderState(
        id=DESCRIPTOR.id,
        display_name=DESCRIPTOR.display_name,
        installed=True,
        authenticated=legacy.get("fail_reason") != "auth_required",
        status="error",
        source="web",
        error=legacy.get("error"),
    )
    return legacy, state
