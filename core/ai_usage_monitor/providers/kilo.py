from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from core.ai_usage_monitor.models import MetricWindow, ProviderState
from core.ai_usage_monitor.providers.base import ProviderBranding, ProviderConfigField, ProviderDescriptor
from core.ai_usage_monitor.util import classify_exception_failure, classify_http_failure, read_http_error_body


DESCRIPTOR = ProviderDescriptor(
    id="kilo",
    display_name="Kilo Code",
    short_name="Kilo",
    default_enabled=True,
    source_modes=("auto", "api", "cli"),
    config_fields=(
        ProviderConfigField("apiKey", "API Key", secret=True, placeholder="kilo_..."),
    ),
    branding=ProviderBranding(icon_key="kilo", asset_name="kilo.svg", color="#F27027", badge_text="KL"),
)


PROCEDURES = [
    "user.getCreditBlocks",
    "kiloPass.getState",
    "user.getAutoTopUpPaymentMethod",
]


def _clean(raw):
    if not isinstance(raw, str):
        return None
    value = raw.strip()
    if not value:
        return None
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        value = value[1:-1].strip()
    return value or None


def _api_key(settings: dict | None):
    return _clean((settings or {}).get("apiKey")) or _clean(os.environ.get("KILO_API_KEY"))


def _auth_file() -> Path:
    return Path.home() / ".local" / "share" / "kilo" / "auth.json"


def _cli_token():
    path = _auth_file()
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text())
    except Exception:
        return None
    kilo = payload.get("kilo") or {}
    return _clean(kilo.get("access"))


def _make_batch_url() -> str:
    joined = ",".join(PROCEDURES)
    input_map = {str(idx): {"json": None} for idx, _ in enumerate(PROCEDURES)}
    encoded = urllib.parse.quote(json.dumps(input_map, separators=(",", ":")))
    return f"https://app.kilo.ai/api/trpc/{joined}?batch=1&input={encoded}"


def _status_error(status_code: int):
    if status_code in (401, 403):
        return "unauthorized"
    if status_code == 404:
        return "endpoint_not_found"
    if 500 <= status_code <= 599:
        return "service_unavailable"
    return None


def _result_payload(entry: dict):
    result = entry.get("result") if isinstance(entry, dict) else None
    if not isinstance(result, dict):
        return None
    data = result.get("data")
    if isinstance(data, dict):
        return data.get("json", data)
    return result.get("json")


def _walk_dicts(payload):
    if not isinstance(payload, dict):
        return []
    contexts = []
    queue = [payload]
    while queue:
        current = queue.pop(0)
        contexts.append(current)
        for value in current.values():
            if isinstance(value, dict):
                queue.append(value)
            elif isinstance(value, list):
                queue.extend(item for item in value if isinstance(item, dict))
    return contexts


def _first_value(keys, contexts):
    for context in contexts:
        for key in keys:
            if key in context and context[key] is not None:
                return context[key]
    return None


def _to_float(value):
    if value is None:
        return None
    try:
        return float(value)
    except Exception:
        return None


def _to_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        low = value.lower()
        if low in ("true", "yes", "on", "enabled"):
            return True
        if low in ("false", "no", "off", "disabled"):
            return False
    return None


def _to_iso(value):
    if not isinstance(value, str):
        return None
    try:
        return value.replace("Z", "+00:00")
    except Exception:
        return None


def parse_kilo_snapshot(data: bytes):
    root = json.loads(data)
    if isinstance(root, dict):
        entries = [root]
    else:
        entries = root

    payloads = {}
    for idx, procedure in enumerate(PROCEDURES):
        if idx >= len(entries):
            continue
        entry = entries[idx]
        if isinstance(entry, dict) and isinstance(entry.get("error"), dict):
            code = str(entry["error"])
            low = code.lower()
            if "unauthorized" in low or "forbidden" in low:
                raise PermissionError("Kilo authentication failed.")
            raise ValueError("Kilo tRPC error payload.")
        payloads[procedure] = _result_payload(entry)

    credit_contexts = _walk_dicts(payloads.get("user.getCreditBlocks") or {})
    pass_contexts = _walk_dicts(payloads.get("kiloPass.getState") or {})
    auto_contexts = _walk_dicts(payloads.get("user.getAutoTopUpPaymentMethod") or {})

    credit_payload = payloads.get("user.getCreditBlocks") or {}
    credit_blocks = credit_payload.get("creditBlocks") if isinstance(credit_payload, dict) else None
    used = total = remaining = None
    if isinstance(credit_blocks, list):
        total_sum = 0.0
        remaining_sum = 0.0
        saw_total = False
        saw_remaining = False
        for block in credit_blocks:
            if not isinstance(block, dict):
                continue
            amount = _to_float(block.get("amount_mUsd"))
            balance = _to_float(block.get("balance_mUsd"))
            if amount is not None:
                total_sum += amount / 1_000_000
                saw_total = True
            if balance is not None:
                remaining_sum += balance / 1_000_000
                saw_remaining = True
        if saw_total or saw_remaining:
            total = total_sum if saw_total else None
            remaining = remaining_sum if saw_remaining else None
            if total is not None and remaining is not None:
                used = max(0.0, total - remaining)

    if total is None:
        used = _to_float(_first_value(["used", "usedCredits", "creditsUsed", "spent", "consumed"], credit_contexts))
        total = _to_float(_first_value(["total", "totalCredits", "creditsTotal", "limit"], credit_contexts))
        remaining = _to_float(_first_value(["remaining", "creditsRemaining", "balance"], credit_contexts))
    if total is None and used is not None and remaining is not None:
        total = used + remaining
    if used is None and total is not None and remaining is not None:
        used = max(0.0, total - remaining)

    plan_name = _first_value(["planName", "tier", "tierName", "subscriptionName"], pass_contexts)
    if plan_name == "tier_19":
        plan_name = "Starter"
    elif plan_name == "tier_49":
        plan_name = "Pro"
    elif plan_name == "tier_199":
        plan_name = "Expert"
    reset_at = _to_iso(_first_value(["nextBillingAt", "nextRenewalAt", "renewsAt", "renewAt"], pass_contexts))
    pass_used = _to_float(_first_value(["currentPeriodUsageUsd", "used", "spent"], pass_contexts))
    pass_total = _to_float(_first_value(["currentPeriodBaseCreditsUsd", "total", "limit"], pass_contexts))
    pass_bonus = _to_float(_first_value(["currentPeriodBonusCreditsUsd", "bonus"], pass_contexts))
    if pass_total is not None and pass_bonus:
        pass_total += pass_bonus
    auto_enabled = _to_bool(_first_value(["enabled", "isEnabled", "active", "autoTopUpEnabled"], auto_contexts + credit_contexts))
    auto_method = _first_value(["paymentMethod", "paymentMethodType", "method", "cardBrand"], auto_contexts)

    return {
        "credits_used": used,
        "credits_total": total,
        "credits_remaining": remaining,
        "pass_used": pass_used,
        "pass_total": pass_total,
        "pass_bonus": pass_bonus,
        "pass_resets_at": reset_at,
        "plan_name": plan_name,
        "auto_top_up_enabled": auto_enabled,
        "auto_top_up_method": auto_method,
    }


def _fetch_kilo(api_key: str):
    req = urllib.request.Request(
        _make_batch_url(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return parse_kilo_snapshot(resp.read())


def _metric_from_values(label, used, total, reset_at, detail=None):
    if total is None:
        return None
    if total > 0:
        used_pct = min(100.0, max(0.0, ((used or 0.0) / total) * 100.0))
    else:
        used_pct = 100.0
    return MetricWindow(label, used_pct, reset_at or detail)


def collect_kilo(settings: dict | None = None) -> tuple[dict, ProviderState]:
    source = (settings or {}).get("source") or "auto"
    api_key = _api_key(settings)
    cli_token = _cli_token()

    if not api_key and not cli_token:
        return {"installed": False}, ProviderState(id=DESCRIPTOR.id, display_name=DESCRIPTOR.display_name, installed=False, source=source)

    attempts = []
    selected_token = None
    selected_source = source

    if source == "api":
        selected_token = api_key
        selected_source = "api"
    elif source == "cli":
        selected_token = cli_token
        selected_source = "cli"
    else:
        if api_key:
            selected_token = api_key
            selected_source = "api"
        elif cli_token:
            selected_token = cli_token
            selected_source = "cli"

    if not selected_token:
        error_message = "Kilo credentials missing for selected source."
        return (
            {"installed": True, "error": error_message, "fail_reason": "missing_credentials"},
            ProviderState(
                id=DESCRIPTOR.id,
                display_name=DESCRIPTOR.display_name,
                installed=True,
                authenticated=False,
                status="error",
                source=selected_source,
                error=error_message,
            ),
        )

    try:
        snapshot = _fetch_kilo(selected_token)
    except urllib.error.HTTPError as err:
        mapped = _status_error(err.code)
        body = read_http_error_body(err)
        if source == "auto" and mapped == "unauthorized" and selected_source == "api" and cli_token:
            attempts.append("api_failed_unauthorized")
            selected_source = "cli"
            try:
                snapshot = _fetch_kilo(cli_token)
            except urllib.error.HTTPError as cli_err:
                legacy = {"installed": True, **classify_http_failure("kilo", cli_err.code, read_http_error_body(cli_err))}
                state = ProviderState(
                    id=DESCRIPTOR.id,
                    display_name=DESCRIPTOR.display_name,
                    installed=True,
                    authenticated=legacy.get("fail_reason") != "auth_required",
                    status="error",
                    source="cli",
                    error=legacy.get("error"),
                )
                return legacy, state
            except Exception as cli_err:
                legacy = {"installed": True, **classify_exception_failure(cli_err)}
                state = ProviderState(
                    id=DESCRIPTOR.id,
                    display_name=DESCRIPTOR.display_name,
                    installed=True,
                    authenticated=True,
                    status="error",
                    source="cli",
                    error=legacy.get("error"),
                )
                return legacy, state
        else:
            legacy = {"installed": True, **classify_http_failure("kilo", err.code, body)}
            state = ProviderState(
                id=DESCRIPTOR.id,
                display_name=DESCRIPTOR.display_name,
                installed=True,
                authenticated=legacy.get("fail_reason") != "auth_required",
                status="error",
                source=selected_source,
                error=legacy.get("error"),
            )
            return legacy, state
    except Exception as err:
        legacy = {"installed": True, **classify_exception_failure(err)}
        state = ProviderState(
            id=DESCRIPTOR.id,
            display_name=DESCRIPTOR.display_name,
            installed=True,
            authenticated=True,
            status="error",
            source=selected_source,
            error=legacy.get("error"),
        )
        return legacy, state

    primary = None
    if snapshot["credits_total"] is not None:
        total = snapshot["credits_total"]
        used = snapshot["credits_used"] if snapshot["credits_used"] is not None else max(0.0, total - (snapshot["credits_remaining"] or 0.0))
        primary = _metric_from_values("Credits", used, total, None)

    secondary = None
    if snapshot["pass_total"] is not None:
        secondary = _metric_from_values("Kilo Pass", snapshot["pass_used"], snapshot["pass_total"], snapshot["pass_resets_at"])

    login_parts = []
    if snapshot["plan_name"]:
        login_parts.append(str(snapshot["plan_name"]))
    if snapshot["auto_top_up_enabled"] is True:
        login_parts.append("Auto top-up: " + (str(snapshot["auto_top_up_method"]) if snapshot["auto_top_up_method"] else "enabled"))
    elif snapshot["auto_top_up_enabled"] is False:
        login_parts.append("Auto top-up: off")

    legacy = {
        "installed": True,
        "source": selected_source,
        "used_pct": round(primary.used_pct) if primary else None,
        "reset_time": snapshot["pass_resets_at"],
        "plan": snapshot["plan_name"],
        "auto_top_up": snapshot["auto_top_up_enabled"],
        "fallback_attempts": attempts,
    }
    state = ProviderState(
        id=DESCRIPTOR.id,
        display_name=DESCRIPTOR.display_name,
        installed=True,
        authenticated=True,
        source=selected_source,
        primary_metric=primary,
        secondary_metric=secondary,
        extras={"plan": " · ".join(login_parts) if login_parts else ""},
    )
    return legacy, state
