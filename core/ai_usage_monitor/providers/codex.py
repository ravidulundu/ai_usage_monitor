from __future__ import annotations

import glob
import json
from pathlib import Path

from core.ai_usage_monitor.local_usage import scan_codex_local_usage
from core.ai_usage_monitor.models import MetricWindow, ProviderState
from core.ai_usage_monitor.providers.base import ProviderBranding, ProviderDescriptor
from core.ai_usage_monitor.status import fetch_statuspage
from core.ai_usage_monitor.util import unix_to_iso


DESCRIPTOR = ProviderDescriptor(
    id="codex",
    display_name="OpenAI Codex",
    short_name="Codex",
    branding=ProviderBranding(icon_key="codex", asset_name="codex.svg", color="#49A3B0", badge_text="OX"),
)


def normalize_codex_rate_limits(payload: dict, model: str = "") -> ProviderState:
    rl = payload.get("rate_limits", {})
    primary = rl.get("primary", {})
    secondary = rl.get("secondary", {})
    return ProviderState(
        id=DESCRIPTOR.id,
        display_name=DESCRIPTOR.display_name,
        installed=True,
        authenticated=True,
        source="cli",
        local_usage=scan_codex_local_usage(),
        primary_metric=MetricWindow("5h", primary.get("used_percent", 0), unix_to_iso(primary.get("resets_at"))),
        secondary_metric=MetricWindow("7d", secondary.get("used_percent", 0), unix_to_iso(secondary.get("resets_at"))),
        extras={
            "plan": rl.get("plan_type") or "",
            "model": model,
        },
        incident=fetch_statuspage("https://status.openai.com", "https://status.openai.com/"),
    )


def _latest_token_count_snapshot(sessions_dir: Path) -> tuple[dict | None, str]:
    latest_payload = None
    latest_model = ""
    latest_timestamp = ""

    files = sorted(glob.glob(str(sessions_dir / "**" / "*.jsonl"), recursive=True))
    for session_file in files:
        current_model = ""
        try:
            with open(session_file, errors="replace") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    if obj.get("type") == "turn_context":
                        payload = obj.get("payload") or {}
                        if isinstance(payload, dict):
                            model = payload.get("model", "")
                            if model:
                                current_model = model
                        continue

                    if obj.get("type") != "event_msg":
                        continue

                    payload = obj.get("payload") or {}
                    if not isinstance(payload, dict) or payload.get("type") != "token_count":
                        continue

                    timestamp = str(obj.get("timestamp") or payload.get("timestamp") or obj.get("created_at") or "")
                    if latest_payload is None or timestamp >= latest_timestamp:
                        latest_payload = payload
                        latest_model = current_model or latest_model
                        latest_timestamp = timestamp
        except OSError:
            continue

    return latest_payload, latest_model


def collect_codex(settings: dict | None = None) -> tuple[dict, ProviderState]:
    sessions_dir = Path.home() / ".codex" / "sessions"
    legacy = {"installed": False}
    state = ProviderState(id=DESCRIPTOR.id, display_name=DESCRIPTOR.display_name, installed=False, source="cli")

    if not sessions_dir.exists():
        return legacy, state

    files = sorted(glob.glob(str(sessions_dir / "**" / "*.jsonl"), recursive=True))
    if not files:
        return {"installed": True, "has_data": False}, ProviderState(
            id=DESCRIPTOR.id,
            display_name=DESCRIPTOR.display_name,
            installed=True,
            authenticated=True,
            status="ok",
            source="cli",
            local_usage=scan_codex_local_usage(),
            extras={"hasData": False},
            incident=fetch_statuspage("https://status.openai.com", "https://status.openai.com/"),
        )

    last_token_payload, last_model = _latest_token_count_snapshot(sessions_dir)

    if not last_token_payload:
        return {"installed": True, "has_data": False}, ProviderState(
            id=DESCRIPTOR.id,
            display_name=DESCRIPTOR.display_name,
            installed=True,
            authenticated=True,
            status="ok",
            source="cli",
            local_usage=scan_codex_local_usage(),
            extras={"hasData": False},
            incident=fetch_statuspage("https://status.openai.com", "https://status.openai.com/"),
        )

    state = normalize_codex_rate_limits(last_token_payload, model=last_model)
    legacy = {
        "installed": True,
        "five_hour_pct": state.primary_metric.used_pct if state.primary_metric else 0,
        "seven_day_pct": state.secondary_metric.used_pct if state.secondary_metric else 0,
        "five_hour_reset": state.primary_metric.reset_at if state.primary_metric else None,
        "seven_day_reset": state.secondary_metric.reset_at if state.secondary_metric else None,
        "plan_type": state.extras.get("plan") or "",
        "model": state.extras.get("model") or "",
    }
    return legacy, state
