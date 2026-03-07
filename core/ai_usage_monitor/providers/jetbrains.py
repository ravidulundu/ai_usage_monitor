from __future__ import annotations

import html
import json
import re
from datetime import datetime
from pathlib import Path

from core.ai_usage_monitor.models import MetricWindow, ProviderState
from core.ai_usage_monitor.providers.base import ProviderBranding, ProviderDescriptor


DESCRIPTOR = ProviderDescriptor(
    id="jetbrains",
    display_name="JetBrains AI",
    default_enabled=True,
    source_modes=("local",),
    branding=ProviderBranding(icon_key="jetbrains", color="#FF3399", badge_text="JB"),
)


IDE_PATTERNS = [
    ("IntelliJIdea", "IntelliJ IDEA"),
    ("PyCharm", "PyCharm"),
    ("WebStorm", "WebStorm"),
    ("GoLand", "GoLand"),
    ("CLion", "CLion"),
    ("DataGrip", "DataGrip"),
    ("RubyMine", "RubyMine"),
    ("Rider", "Rider"),
    ("PhpStorm", "PhpStorm"),
    ("AppCode", "AppCode"),
    ("Fleet", "Fleet"),
    ("AndroidStudio", "Android Studio"),
    ("RustRover", "RustRover"),
    ("Aqua", "Aqua"),
    ("DataSpell", "DataSpell"),
]


def _base_paths() -> list[Path]:
    home = Path.home()
    return [
        home / ".config" / "JetBrains",
        home / ".local" / "share" / "JetBrains",
        home / ".config" / "Google",
    ]


def detect_installed_ides() -> list[dict]:
    detected = []
    for base in _base_paths():
        if not base.exists():
            continue
        for child in base.iterdir():
            if not child.is_dir():
                continue
            dirname = child.name
            lower = dirname.lower()
            for prefix, display_name in IDE_PATTERNS:
                if not lower.startswith(prefix.lower()):
                    continue
                version = dirname[len(prefix):] or "Unknown"
                quota_file = child / "options" / "AIAssistantQuotaManager2.xml"
                if quota_file.exists():
                    detected.append(
                        {
                            "name": display_name,
                            "version": version,
                            "base_path": str(child),
                            "quota_file": str(quota_file),
                            "mtime": quota_file.stat().st_mtime,
                        }
                    )
                break
    return sorted(detected, key=lambda item: item["mtime"], reverse=True)


def decode_html_entities(text: str) -> str:
    return html.unescape(text.replace("&#10;", "\n"))


def _parse_date(value: str | None):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat()
    except Exception:
        return None


def parse_jetbrains_xml(xml_text: str, detected_ide: dict | None = None) -> dict:
    quota_match = re.search(r'name="quotaInfo"\s+value="([^"]+)"', xml_text)
    if not quota_match:
        raise ValueError("No quota information found in the JetBrains AI configuration.")
    quota_info = json.loads(decode_html_entities(quota_match.group(1)))

    refill_info = None
    refill_match = re.search(r'name="nextRefill"\s+value="([^"]+)"', xml_text)
    if refill_match:
        try:
            refill_info = json.loads(decode_html_entities(refill_match.group(1)))
        except Exception:
            refill_info = None

    current = float(quota_info.get("current") or 0)
    maximum = float(quota_info.get("maximum") or 0)
    tariff_quota = quota_info.get("tariffQuota") or {}
    available = float(tariff_quota.get("available") or max(0, maximum - current))
    used_percent = 0.0 if maximum <= 0 else min(100.0, max(0.0, (current / maximum) * 100.0))
    refill_at = _parse_date((refill_info or {}).get("next"))

    return {
        "quota_type": quota_info.get("type"),
        "used": current,
        "maximum": maximum,
        "available": available,
        "used_percent": used_percent,
        "refill_at": refill_at,
        "ide_name": (detected_ide["name"] + " " + detected_ide["version"]) if detected_ide else None,
    }


def collect_jetbrains(settings: dict | None = None) -> tuple[dict, ProviderState]:
    detected = detect_installed_ides()
    if not detected:
        return {"installed": False}, ProviderState(id=DESCRIPTOR.id, display_name=DESCRIPTOR.display_name, installed=False, source="local")

    ide = detected[0]
    try:
        xml_text = Path(ide["quota_file"]).read_text(errors="replace")
        parsed = parse_jetbrains_xml(xml_text, detected_ide=ide)
        legacy = {
            "installed": True,
            "used_pct": round(parsed["used_percent"]),
            "reset_time": parsed["refill_at"],
            "ide_name": parsed["ide_name"],
            "quota_type": parsed["quota_type"],
        }
        state = ProviderState(
            id=DESCRIPTOR.id,
            display_name=DESCRIPTOR.display_name,
            installed=True,
            authenticated=True,
            source="local",
            primary_metric=MetricWindow("Current", parsed["used_percent"], parsed["refill_at"]),
            extras={"plan": parsed["quota_type"], "model": parsed["ide_name"]},
        )
        return legacy, state
    except Exception as err:
        legacy = {"installed": True, "error": f"Could not parse JetBrains AI quota: {err}", "fail_reason": "parse_error"}
        state = ProviderState(
            id=DESCRIPTOR.id,
            display_name=DESCRIPTOR.display_name,
            installed=True,
            authenticated=True,
            status="error",
            source="local",
            error=legacy["error"],
        )
        return legacy, state
