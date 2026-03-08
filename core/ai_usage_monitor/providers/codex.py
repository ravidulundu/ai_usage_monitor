from __future__ import annotations

import glob
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.ai_usage_monitor.local_usage import scan_codex_local_usage
from core.ai_usage_monitor.models import LocalUsageSnapshot, MetricWindow, ProviderState
from core.ai_usage_monitor.providers.base import ProviderBranding, ProviderDescriptor
from core.ai_usage_monitor.shared.time_utils import unix_to_iso
from core.ai_usage_monitor.status import fetch_statuspage


DESCRIPTOR = ProviderDescriptor(
    id="codex",
    display_name="OpenAI Codex",
    short_name="Codex",
    branding=ProviderBranding(
        icon_key="codex", asset_name="codex.svg", color="#49A3B0", badge_text="OX"
    ),
    status_page_url="https://status.openai.com/",
    usage_dashboard_default_url="https://chatgpt.com/codex/settings/usage",
    usage_dashboard_by_source=(
        ("api", "https://platform.openai.com/usage"),
        ("cli", "https://chatgpt.com/codex/settings/usage"),
    ),
    preferred_source_policy="local_first",
)


def _parse_timestamp(raw: str | int | float | None) -> datetime | None:
    if raw is None:
        return None

    if isinstance(raw, (int, float)):
        try:
            return datetime.fromtimestamp(float(raw), tz=timezone.utc)
        except Exception:
            return None

    text = str(raw).strip()
    if not text:
        return None

    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        pass

    if text.isdigit():
        try:
            return datetime.fromtimestamp(float(text), tz=timezone.utc)
        except Exception:
            return None
    return None


def _to_iso(dt: datetime | None) -> str | None:
    return dt.astimezone(timezone.utc).isoformat() if dt else None


def _codex_identity_state_path() -> Path:
    return Path.home() / ".cache" / "ai-usage-monitor" / "codex_identity_state.json"


def _load_codex_identity_state() -> dict[str, Any]:
    path = _codex_identity_state_path()
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text())
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _save_codex_identity_state(
    identity_key: str, account_id: str, switch_detected_at: str | None
) -> None:
    path = _codex_identity_state_path()
    payload = {
        "version": 1,
        "identityKey": identity_key,
        "accountId": account_id,
        "switchDetectedAt": switch_detected_at,
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload))
    except OSError:
        return


def _load_codex_account_identity() -> dict[str, str]:
    auth_file = Path.home() / ".codex" / "auth.json"
    account_id = ""
    auth_mode = ""

    if auth_file.exists():
        try:
            payload = json.loads(auth_file.read_text())
        except Exception:
            payload = {}
        if isinstance(payload, dict):
            auth_mode = str(payload.get("auth_mode") or "").strip()
            tokens = payload.get("tokens")
            if isinstance(tokens, dict):
                account_id = str(tokens.get("account_id") or "").strip()

    identity_key = account_id if account_id else "__unknown__"
    return {
        "account_id": account_id,
        "auth_mode": auth_mode,
        "identity_key": identity_key,
    }


def _resolve_account_switch_cutoff(
    identity_key: str, account_id: str
) -> tuple[datetime | None, bool]:
    state = _load_codex_identity_state()
    previous_identity_key = str(state.get("identityKey") or "").strip()
    switch_detected_at = _parse_timestamp(state.get("switchDetectedAt"))
    now = datetime.now(timezone.utc)

    if not previous_identity_key:
        _save_codex_identity_state(
            identity_key, account_id, _to_iso(switch_detected_at)
        )
        return switch_detected_at, False

    if previous_identity_key != identity_key:
        _save_codex_identity_state(identity_key, account_id, _to_iso(now))
        return now, True

    return switch_detected_at, False


def _identity_extras(
    identity: dict[str, str], switched: bool, cutoff: datetime | None
) -> dict[str, str | bool]:
    extras: dict[str, str | bool] = {
        "accountSwitched": switched,
        "accountIdentityKey": identity.get("identity_key") or "__unknown__",
    }
    account_id = identity.get("account_id") or ""
    auth_mode = identity.get("auth_mode") or ""
    if account_id:
        extras["accountId"] = account_id
    if auth_mode:
        extras["authMode"] = auth_mode
    cutoff_iso = _to_iso(cutoff)
    if cutoff_iso:
        extras["accountSwitchCutoff"] = cutoff_iso
    return extras


def normalize_codex_rate_limits(
    payload: dict[str, Any],
    model: str = "",
    local_usage: LocalUsageSnapshot | None = None,
) -> ProviderState:
    rl = payload.get("rate_limits") if isinstance(payload, dict) else {}
    if not isinstance(rl, dict):
        rl = {}
    primary = rl.get("primary", {})
    if not isinstance(primary, dict):
        primary = {}
    secondary = rl.get("secondary", {})
    if not isinstance(secondary, dict):
        secondary = {}
    has_rate_limits = bool(primary or secondary)

    primary_metric = None
    secondary_metric = None
    if has_rate_limits:
        primary_metric = MetricWindow(
            "5h", primary.get("used_percent", 0), unix_to_iso(primary.get("resets_at"))
        )
        secondary_metric = MetricWindow(
            "7d",
            secondary.get("used_percent", 0),
            unix_to_iso(secondary.get("resets_at")),
        )

    return ProviderState(
        id=DESCRIPTOR.id,
        display_name=DESCRIPTOR.display_name,
        installed=True,
        authenticated=True,
        source="cli",
        local_usage=local_usage
        if local_usage is not None
        else scan_codex_local_usage(),
        primary_metric=primary_metric,
        secondary_metric=secondary_metric,
        extras={
            "plan": rl.get("plan_type") or "",
            "model": model,
            "hasRateLimits": has_rate_limits,
        },
        incident=fetch_statuspage(
            "https://status.openai.com", "https://status.openai.com/"
        ),
    )


def _latest_token_count_snapshot(
    sessions_dir: Path, min_timestamp: str | datetime | None = None
) -> tuple[dict | None, str]:
    latest_payload = None
    latest_model = ""
    latest_timestamp: datetime | None = None

    cutoff = (
        _parse_timestamp(min_timestamp)
        if not isinstance(min_timestamp, datetime)
        else min_timestamp
    )

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
                    if (
                        not isinstance(payload, dict)
                        or payload.get("type") != "token_count"
                    ):
                        continue

                    timestamp = str(
                        obj.get("timestamp")
                        or payload.get("timestamp")
                        or obj.get("created_at")
                        or ""
                    )
                    dt = _parse_timestamp(timestamp)
                    if cutoff and (dt is None or dt < cutoff):
                        continue

                    if latest_payload is None:
                        latest_payload = payload
                        latest_model = current_model or latest_model
                        latest_timestamp = dt
                        continue

                    if latest_timestamp is None and dt is not None:
                        latest_payload = payload
                        latest_model = current_model or latest_model
                        latest_timestamp = dt
                        continue

                    if (
                        latest_timestamp is not None
                        and dt is not None
                        and dt >= latest_timestamp
                    ):
                        latest_payload = payload
                        latest_model = current_model or latest_model
                        latest_timestamp = dt
        except OSError:
            continue

    return latest_payload, latest_model


def collect_codex(
    settings: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], ProviderState]:
    _ = settings
    sessions_dir = Path.home() / ".codex" / "sessions"
    identity = _load_codex_account_identity()
    switch_cutoff, account_switched = _resolve_account_switch_cutoff(
        identity["identity_key"], identity["account_id"]
    )
    identity_extras = _identity_extras(identity, account_switched, switch_cutoff)
    local_usage = scan_codex_local_usage(min_timestamp=switch_cutoff)

    legacy: dict[str, Any] = {"installed": False}
    state = ProviderState(
        id=DESCRIPTOR.id,
        display_name=DESCRIPTOR.display_name,
        installed=False,
        source="cli",
    )

    if not sessions_dir.exists():
        state.extras = identity_extras
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
            local_usage=local_usage,
            extras={"hasData": False, **identity_extras},
            incident=fetch_statuspage(
                "https://status.openai.com", "https://status.openai.com/"
            ),
        )

    last_token_payload, last_model = _latest_token_count_snapshot(
        sessions_dir, min_timestamp=switch_cutoff
    )

    if not last_token_payload:
        return {"installed": True, "has_data": False}, ProviderState(
            id=DESCRIPTOR.id,
            display_name=DESCRIPTOR.display_name,
            installed=True,
            authenticated=True,
            status="ok",
            source="cli",
            local_usage=local_usage,
            extras={"hasData": False, **identity_extras},
            incident=fetch_statuspage(
                "https://status.openai.com", "https://status.openai.com/"
            ),
        )

    state = normalize_codex_rate_limits(
        last_token_payload, model=last_model, local_usage=local_usage
    )
    state.extras = {**state.extras, **identity_extras}
    legacy = {
        "installed": True,
        "five_hour_pct": state.primary_metric.used_pct if state.primary_metric else 0,
        "seven_day_pct": state.secondary_metric.used_pct
        if state.secondary_metric
        else 0,
        "five_hour_reset": state.primary_metric.reset_at
        if state.primary_metric
        else None,
        "seven_day_reset": state.secondary_metric.reset_at
        if state.secondary_metric
        else None,
        "plan_type": state.extras.get("plan") or "",
        "model": state.extras.get("model") or "",
        "account_id": state.extras.get("accountId") or "",
        "account_switched": bool(state.extras.get("accountSwitched")),
    }
    return legacy, state
