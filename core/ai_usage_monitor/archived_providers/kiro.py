from __future__ import annotations

import re
import subprocess
from datetime import datetime, timedelta, timezone

from core.ai_usage_monitor.cli_detect import resolve_cli_binary
from core.ai_usage_monitor.models import MetricWindow, ProviderState
from core.ai_usage_monitor.providers.base import ProviderBranding, ProviderDescriptor


DESCRIPTOR = ProviderDescriptor(
    id="kiro",
    display_name="Kiro CLI",
    short_name="Kiro",
    default_enabled=True,
    source_modes=("cli",),
    branding=ProviderBranding(icon_key="kiro", color="#FF9900", badge_text="KI"),
)


ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def _parse_mmdd_reset(value: str) -> str | None:
    try:
        month, day = value.split("/")
        now = datetime.now(timezone.utc)
        candidate = datetime(now.year, int(month), int(day), tzinfo=timezone.utc)
        if candidate < now:
            candidate = datetime(
                now.year + 1, int(month), int(day), tzinfo=timezone.utc
            )
        return candidate.isoformat()
    except Exception:
        return None


def parse_kiro_output(output: str) -> dict:
    stripped = strip_ansi(output)
    lowered = stripped.lower()
    if not stripped.strip():
        raise ValueError("Empty output from kiro-cli.")
    if (
        "not logged in" in lowered
        or "login required" in lowered
        or "kiro-cli login" in lowered
    ):
        raise PermissionError("Not logged in to Kiro. Run 'kiro-cli login' first.")

    plan_name = "Kiro"
    plan_match = re.search(r"Plan:\s*(.+)", stripped)
    if plan_match:
        plan_name = plan_match.group(1).strip()
    else:
        banner_match = re.search(r"\|\s*([A-Z0-9 _-]+)\s*\|", stripped)
        if banner_match:
            plan_name = banner_match.group(1).strip().title()

    credits_percent = None
    resets_at = None
    percent_match = re.search(
        r"(\d+)%\s*\(resets on (\d{2}/\d{2})\)", stripped, re.IGNORECASE
    )
    if percent_match:
        credits_percent = float(percent_match.group(1))
        resets_at = _parse_mmdd_reset(percent_match.group(2))

    credits_ratio_match = re.search(
        r"\((\d+(?:\.\d+)?) of (\d+(?:\.\d+)?) covered in plan\)",
        stripped,
        re.IGNORECASE,
    )
    credits_used = float(credits_ratio_match.group(1)) if credits_ratio_match else None
    credits_total = float(credits_ratio_match.group(2)) if credits_ratio_match else None

    bonus_used = bonus_total = bonus_days = None
    bonus_match = re.search(
        r"Bonus credits:\s*(\d+(?:\.\d+)?)/(\d+(?:\.\d+)?) credits used(?:,\s*expires in (\d+) days)?",
        stripped,
        re.IGNORECASE,
    )
    if bonus_match:
        bonus_used = float(bonus_match.group(1))
        bonus_total = float(bonus_match.group(2))
        bonus_days = int(bonus_match.group(3)) if bonus_match.group(3) else None

    if credits_percent is None:
        raise ValueError(
            "No recognizable usage patterns found. Kiro CLI output format may have changed."
        )

    return {
        "plan_name": plan_name,
        "credits_used": credits_used,
        "credits_total": credits_total,
        "credits_percent": credits_percent,
        "bonus_used": bonus_used,
        "bonus_total": bonus_total,
        "bonus_days": bonus_days,
        "resets_at": resets_at,
    }


def collect_kiro(settings: dict | None = None) -> tuple[dict, ProviderState]:
    del settings
    binary = resolve_cli_binary("kiro-cli", env_var="AI_USAGE_MONITOR_KIRO_BIN")
    if binary is None:
        return {"installed": False}, ProviderState(
            id=DESCRIPTOR.id,
            display_name=DESCRIPTOR.display_name,
            installed=False,
            source="cli",
        )

    try:
        whoami = subprocess.run(
            [binary, "whoami"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        combined = f"{whoami.stdout}\n{whoami.stderr}".lower()
        if (
            whoami.returncode != 0
            or "not logged in" in combined
            or "login required" in combined
        ):
            raise PermissionError("Not logged in to Kiro. Run 'kiro-cli login' first.")

        usage = subprocess.run(
            [binary, "chat", "--no-interactive", "/usage"],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        output = usage.stdout if usage.stdout.strip() else usage.stderr
        if usage.returncode != 0 and not output.strip():
            raise RuntimeError(f"Kiro CLI failed with status {usage.returncode}.")

        parsed = parse_kiro_output(output)
        bonus_metric = None
        if (
            parsed["bonus_used"] is not None
            and parsed["bonus_total"]
            and parsed["bonus_total"] > 0
        ):
            bonus_pct = (parsed["bonus_used"] / parsed["bonus_total"]) * 100.0
            bonus_reset = None
            if parsed["bonus_days"] is not None:
                bonus_reset = (
                    datetime.now(timezone.utc) + timedelta(days=parsed["bonus_days"])
                ).isoformat()
            bonus_metric = MetricWindow("Bonus", bonus_pct, bonus_reset)

        legacy = {
            "installed": True,
            "plan": parsed["plan_name"],
            "used_pct": round(parsed["credits_percent"]),
            "reset_time": parsed["resets_at"],
            "bonus_used": parsed["bonus_used"],
            "bonus_total": parsed["bonus_total"],
            "bonus_days": parsed["bonus_days"],
        }
        state = ProviderState(
            id=DESCRIPTOR.id,
            display_name=DESCRIPTOR.display_name,
            installed=True,
            authenticated=True,
            source="cli",
            primary_metric=MetricWindow(
                "Monthly", parsed["credits_percent"], parsed["resets_at"]
            ),
            secondary_metric=bonus_metric,
            extras={"plan": parsed["plan_name"]},
        )
        return legacy, state
    except PermissionError as err:
        legacy = {
            "installed": True,
            "authenticated": False,
            "error": str(err),
            "fail_reason": "auth_required",
        }
        state = ProviderState(
            id=DESCRIPTOR.id,
            display_name=DESCRIPTOR.display_name,
            installed=True,
            authenticated=False,
            status="error",
            source="cli",
            error=str(err),
        )
        return legacy, state
    except subprocess.TimeoutExpired:
        legacy = {
            "installed": True,
            "error": "Kiro CLI timed out.",
            "fail_reason": "timeout",
        }
        state = ProviderState(
            id=DESCRIPTOR.id,
            display_name=DESCRIPTOR.display_name,
            installed=True,
            authenticated=True,
            status="error",
            source="cli",
            error="Kiro CLI timed out.",
        )
        return legacy, state
    except Exception as err:
        legacy = {
            "installed": True,
            "error": f"Failed to parse Kiro usage: {err}",
            "fail_reason": "parse_error",
        }
        state = ProviderState(
            id=DESCRIPTOR.id,
            display_name=DESCRIPTOR.display_name,
            installed=True,
            authenticated=True,
            status="error",
            source="cli",
            error=legacy["error"],
        )
        return legacy, state
