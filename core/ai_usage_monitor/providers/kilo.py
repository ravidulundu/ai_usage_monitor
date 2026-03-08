from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Sequence, TypedDict

from core.ai_usage_monitor.models import MetricWindow, ProviderState
from core.ai_usage_monitor.providers.base import (
    ProviderBranding,
    ProviderConfigField,
    ProviderDescriptor,
)
from core.ai_usage_monitor.shared.http_failures import (
    classify_exception_failure,
    classify_http_failure,
    read_http_error_body,
)


DESCRIPTOR = ProviderDescriptor(
    id="kilo",
    display_name="Kilo Code",
    short_name="Kilo",
    default_enabled=True,
    source_modes=("auto", "api", "cli"),
    config_fields=(
        ProviderConfigField("apiKey", "API Key", secret=True, placeholder="kilo_..."),
    ),
    branding=ProviderBranding(
        icon_key="kilo", asset_name="kilo.svg", color="#F27027", badge_text="KL"
    ),
    status_page_url="https://status.kilocode.ai/",
    usage_dashboard_default_url="https://app.kilo.ai/",
    usage_dashboard_by_source=(
        ("api", "https://app.kilo.ai/"),
        ("cli", "https://app.kilo.ai/"),
    ),
    preferred_source_policy="local_first",
)


PROCEDURES = [
    "user.getCreditBlocks",
    "kiloPass.getState",
    "user.getAutoTopUpPaymentMethod",
]


class KiloSnapshot(TypedDict):
    credits_used: float | None
    credits_total: float | None
    credits_remaining: float | None
    pass_used: float | None
    pass_total: float | None
    pass_bonus: float | None
    pass_resets_at: str | None
    plan_name: str | None
    auto_top_up_enabled: bool | None
    auto_top_up_method: str | None


def _clean(raw: Any) -> str | None:
    if not isinstance(raw, str):
        return None
    value = raw.strip()
    if not value:
        return None
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        value = value[1:-1].strip()
    return value or None


def _api_key(settings: dict[str, Any] | None) -> str | None:
    return _clean((settings or {}).get("apiKey")) or _clean(
        os.environ.get("KILO_API_KEY")
    )


def _auth_file() -> Path:
    return Path.home() / ".local" / "share" / "kilo" / "auth.json"


def _cli_token() -> str | None:
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


def _status_error(status_code: int) -> str | None:
    if status_code in (401, 403):
        return "unauthorized"
    if status_code == 404:
        return "endpoint_not_found"
    if 500 <= status_code <= 599:
        return "service_unavailable"
    return None


def _result_payload(entry: Any) -> Any | None:
    result = entry.get("result") if isinstance(entry, dict) else None
    if not isinstance(result, dict):
        return None
    data = result.get("data")
    if isinstance(data, dict):
        return data.get("json", data)
    return result.get("json")


def _walk_dicts(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    contexts: list[dict[str, Any]] = []
    queue: list[dict[str, Any]] = [payload]
    while queue:
        current = queue.pop(0)
        contexts.append(current)
        for value in current.values():
            if isinstance(value, dict):
                queue.append(value)
            elif isinstance(value, list):
                queue.extend(item for item in value if isinstance(item, dict))
    return contexts


def _first_value(keys: Sequence[str], contexts: Sequence[dict[str, Any]]) -> Any | None:
    for context in contexts:
        for key in keys:
            if key in context and context[key] is not None:
                return context[key]
    return None


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except Exception:
        return None


def _to_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        low = value.lower()
        if low in ("true", "yes", "on", "enabled"):
            return True
        if low in ("false", "no", "off", "disabled"):
            return False
    return None


def _to_iso(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        return value.replace("Z", "+00:00")
    except Exception:
        return None


def _snapshot_entries(data: bytes) -> Sequence[Any]:
    root = json.loads(data)
    if isinstance(root, dict):
        return [root]
    if isinstance(root, list):
        return root
    return []


def _trpc_payloads(entries: Sequence[Any]) -> dict[str, Any]:
    payloads: dict[str, Any] = {}
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
    return payloads


def _credit_blocks(payloads: dict[str, Any]) -> list[dict[str, Any]]:
    credit_payload = payloads.get("user.getCreditBlocks") or {}
    credit_blocks = (
        credit_payload.get("creditBlocks") if isinstance(credit_payload, dict) else None
    )
    if not isinstance(credit_blocks, list):
        return []
    return [item for item in credit_blocks if isinstance(item, dict)]


def _usage_from_credit_blocks(
    credit_blocks: Sequence[dict[str, Any]],
) -> tuple[float | None, float | None, float | None]:
    if not credit_blocks:
        return None, None, None
    total_sum = 0.0
    remaining_sum = 0.0
    saw_total = False
    saw_remaining = False
    for block in credit_blocks:
        amount = _to_float(block.get("amount_mUsd"))
        balance = _to_float(block.get("balance_mUsd"))
        if amount is not None:
            total_sum += amount / 1_000_000
            saw_total = True
        if balance is not None:
            remaining_sum += balance / 1_000_000
            saw_remaining = True
    if not (saw_total or saw_remaining):
        return None, None, None
    total = total_sum if saw_total else None
    remaining = remaining_sum if saw_remaining else None
    used = (
        max(0.0, total - remaining)
        if total is not None and remaining is not None
        else None
    )
    return used, total, remaining


def _usage_from_credit_contexts(
    credit_contexts: Sequence[dict[str, Any]],
) -> tuple[float | None, float | None, float | None]:
    used = _to_float(
        _first_value(
            ["used", "usedCredits", "creditsUsed", "spent", "consumed"],
            credit_contexts,
        )
    )
    total = _to_float(
        _first_value(
            ["total", "totalCredits", "creditsTotal", "limit"], credit_contexts
        )
    )
    remaining = _to_float(
        _first_value(["remaining", "creditsRemaining", "balance"], credit_contexts)
    )
    return used, total, remaining


def _normalize_credit_usage(
    used: float | None,
    total: float | None,
    remaining: float | None,
) -> tuple[float | None, float | None, float | None]:
    if total is None and used is not None and remaining is not None:
        total = used + remaining
    if used is None and total is not None and remaining is not None:
        used = max(0.0, total - remaining)
    return used, total, remaining


def _pass_plan_name(pass_contexts: Sequence[dict[str, Any]]) -> str | None:
    raw_plan = _first_value(
        ["planName", "tier", "tierName", "subscriptionName"], pass_contexts
    )
    if raw_plan == "tier_19":
        return "Starter"
    if raw_plan == "tier_49":
        return "Pro"
    if raw_plan == "tier_199":
        return "Expert"
    if isinstance(raw_plan, str):
        return raw_plan
    return None


def _pass_usage_state(
    pass_contexts: Sequence[dict[str, Any]],
) -> tuple[str | None, float | None, float | None, float | None]:
    reset_at = _to_iso(
        _first_value(
            ["nextBillingAt", "nextRenewalAt", "renewsAt", "renewAt"], pass_contexts
        )
    )
    pass_used = _to_float(
        _first_value(["currentPeriodUsageUsd", "used", "spent"], pass_contexts)
    )
    pass_total = _to_float(
        _first_value(["currentPeriodBaseCreditsUsd", "total", "limit"], pass_contexts)
    )
    pass_bonus = _to_float(
        _first_value(["currentPeriodBonusCreditsUsd", "bonus"], pass_contexts)
    )
    if pass_total is not None and pass_bonus:
        pass_total += pass_bonus
    return reset_at, pass_used, pass_total, pass_bonus


def _auto_top_up_state(
    auto_contexts: Sequence[dict[str, Any]],
    credit_contexts: Sequence[dict[str, Any]],
) -> tuple[bool | None, Any | None]:
    auto_enabled = _to_bool(
        _first_value(
            ["enabled", "isEnabled", "active", "autoTopUpEnabled"],
            list(auto_contexts) + list(credit_contexts),
        )
    )
    auto_method = _first_value(
        ["paymentMethod", "paymentMethodType", "method", "cardBrand"], auto_contexts
    )
    return auto_enabled, auto_method


def parse_kilo_snapshot(data: bytes) -> KiloSnapshot:
    entries = _snapshot_entries(data)
    payloads = _trpc_payloads(entries)

    credit_contexts = _walk_dicts(payloads.get("user.getCreditBlocks") or {})
    pass_contexts = _walk_dicts(payloads.get("kiloPass.getState") or {})
    auto_contexts = _walk_dicts(payloads.get("user.getAutoTopUpPaymentMethod") or {})

    used, total, remaining = _usage_from_credit_blocks(_credit_blocks(payloads))
    if total is None:
        used, total, remaining = _usage_from_credit_contexts(credit_contexts)
    used, total, remaining = _normalize_credit_usage(used, total, remaining)

    plan_name = _pass_plan_name(pass_contexts)
    reset_at, pass_used, pass_total, pass_bonus = _pass_usage_state(pass_contexts)
    auto_enabled, auto_method = _auto_top_up_state(auto_contexts, credit_contexts)

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


def _fetch_kilo(api_key: str) -> KiloSnapshot:
    req = urllib.request.Request(
        _make_batch_url(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return parse_kilo_snapshot(resp.read())


def _metric_from_values(
    label: str,
    used: float | None,
    total: float | None,
    reset_at: str | None,
    detail: str | None = None,
) -> MetricWindow | None:
    if total is None:
        return None
    if total > 0:
        used_pct = min(100.0, max(0.0, ((used or 0.0) / total) * 100.0))
    else:
        used_pct = 100.0
    return MetricWindow(label, used_pct, reset_at or detail)


def _missing_kilo_installation(source: str) -> tuple[dict[str, Any], ProviderState]:
    return {"installed": False}, ProviderState(
        id=DESCRIPTOR.id,
        display_name=DESCRIPTOR.display_name,
        installed=False,
        source=source,
    )


def _kilo_collection_inputs(
    settings: dict[str, Any] | None,
) -> tuple[str, str | None, str | None]:
    source = str((settings or {}).get("source") or "auto")
    api_key = _api_key(settings)
    cli_token = _cli_token()
    return source, api_key, cli_token


def _select_kilo_auth_source(
    source: str, api_key: str | None, cli_token: str | None
) -> tuple[str, str | None]:
    if source == "api":
        return "api", api_key
    if source == "cli":
        return "cli", cli_token
    if api_key:
        return "api", api_key
    if cli_token:
        return "cli", cli_token
    return source, None


def _kilo_error_response(
    legacy: dict[str, Any], source: str, authenticated: bool
) -> tuple[dict[str, Any], ProviderState]:
    error_text = legacy.get("error")
    return legacy, ProviderState(
        id=DESCRIPTOR.id,
        display_name=DESCRIPTOR.display_name,
        installed=True,
        authenticated=authenticated,
        status="error",
        source=source,
        error=str(error_text) if error_text is not None else None,
    )


def _kilo_missing_credentials_response(
    selected_source: str,
) -> tuple[dict[str, Any], ProviderState]:
    error_message = "Kilo credentials missing for selected source."
    return _kilo_error_response(
        {
            "installed": True,
            "error": error_message,
            "fail_reason": "missing_credentials",
        },
        source=selected_source,
        authenticated=False,
    )


def _fetch_kilo_snapshot(
    source: str,
    selected_source: str,
    selected_token: str,
    cli_token: str | None,
) -> tuple[
    KiloSnapshot | None, str, list[str], tuple[dict[str, Any], ProviderState] | None
]:
    attempts: list[str] = []
    try:
        return _fetch_kilo(selected_token), selected_source, attempts, None
    except urllib.error.HTTPError as err:
        mapped = _status_error(err.code)
        body = read_http_error_body(err)
        if (
            source == "auto"
            and mapped == "unauthorized"
            and selected_source == "api"
            and cli_token
        ):
            attempts.append("api_failed_unauthorized")
            fallback_source = "cli"
            try:
                return _fetch_kilo(cli_token), fallback_source, attempts, None
            except urllib.error.HTTPError as cli_err:
                legacy = {
                    "installed": True,
                    **classify_http_failure(
                        "kilo", cli_err.code, read_http_error_body(cli_err)
                    ),
                }
                auth = str(legacy.get("fail_reason") or "") != "auth_required"
                return (
                    None,
                    fallback_source,
                    attempts,
                    _kilo_error_response(
                        legacy, source=fallback_source, authenticated=auth
                    ),
                )
            except Exception as cli_err:
                legacy = {
                    "installed": True,
                    **classify_exception_failure(cli_err),
                }
                return (
                    None,
                    fallback_source,
                    attempts,
                    _kilo_error_response(
                        legacy, source=fallback_source, authenticated=True
                    ),
                )

        legacy = {
            "installed": True,
            **classify_http_failure("kilo", err.code, body),
        }
        auth = str(legacy.get("fail_reason") or "") != "auth_required"
        return (
            None,
            selected_source,
            attempts,
            _kilo_error_response(legacy, source=selected_source, authenticated=auth),
        )
    except Exception as err:
        legacy = {"installed": True, **classify_exception_failure(err)}
        return (
            None,
            selected_source,
            attempts,
            _kilo_error_response(legacy, source=selected_source, authenticated=True),
        )


def _kilo_metrics_from_snapshot(
    snapshot: KiloSnapshot,
) -> tuple[MetricWindow | None, MetricWindow | None]:
    primary: MetricWindow | None = None
    if snapshot["credits_total"] is not None:
        total = snapshot["credits_total"]
        used = (
            snapshot["credits_used"]
            if snapshot["credits_used"] is not None
            else max(0.0, total - (snapshot["credits_remaining"] or 0.0))
        )
        primary = _metric_from_values("Credits", used, total, None)

    secondary: MetricWindow | None = None
    if snapshot["pass_total"] is not None:
        secondary = _metric_from_values(
            "Kilo Pass",
            snapshot["pass_used"],
            snapshot["pass_total"],
            snapshot["pass_resets_at"],
        )
    return primary, secondary


def _kilo_extras_plan(snapshot: KiloSnapshot) -> str:
    login_parts: list[str] = []
    if snapshot["plan_name"]:
        login_parts.append(str(snapshot["plan_name"]))
    if snapshot["auto_top_up_enabled"] is True:
        login_parts.append(
            "Auto top-up: "
            + (
                str(snapshot["auto_top_up_method"])
                if snapshot["auto_top_up_method"]
                else "enabled"
            )
        )
    elif snapshot["auto_top_up_enabled"] is False:
        login_parts.append("Auto top-up: off")
    return " · ".join(login_parts) if login_parts else ""


def _kilo_success_response(
    snapshot: KiloSnapshot,
    selected_source: str,
    attempts: list[str],
) -> tuple[dict[str, Any], ProviderState]:
    primary, secondary = _kilo_metrics_from_snapshot(snapshot)
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
        extras={"plan": _kilo_extras_plan(snapshot)},
    )
    return legacy, state


def collect_kilo(
    settings: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], ProviderState]:
    source, api_key, cli_token = _kilo_collection_inputs(settings)
    if not api_key and not cli_token:
        return _missing_kilo_installation(source)

    selected_source, selected_token = _select_kilo_auth_source(
        source, api_key, cli_token
    )
    if not selected_token:
        return _kilo_missing_credentials_response(selected_source)

    snapshot, selected_source, attempts, error_response = _fetch_kilo_snapshot(
        source=source,
        selected_source=selected_source,
        selected_token=selected_token,
        cli_token=cli_token,
    )
    if error_response is not None:
        return error_response
    if snapshot is None:
        return _kilo_error_response(
            {"installed": True, "error": "Kilo snapshot missing."},
            source=selected_source,
            authenticated=False,
        )
    return _kilo_success_response(snapshot, selected_source, attempts)
