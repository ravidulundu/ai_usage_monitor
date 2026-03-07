from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from core.ai_usage_monitor.models import ProviderState


@dataclass(frozen=True)
class ProviderConfigField:
    key: str
    label: str
    kind: str = "string"
    secret: bool = False
    placeholder: str = ""
    options: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "label": self.label,
            "kind": self.kind,
            "secret": self.secret,
            "placeholder": self.placeholder,
            "options": list(self.options),
        }


@dataclass(frozen=True)
class ProviderBranding:
    icon_key: str | None = None
    asset_name: str | None = None
    color: str = "#64748b"
    badge_text: str | None = None

    def to_dict(self) -> dict:
        return {
            "iconKey": self.icon_key,
            "assetName": self.asset_name,
            "color": self.color,
            "badgeText": self.badge_text,
        }


@dataclass(frozen=True)
class ProviderDescriptor:
    id: str
    display_name: str
    short_name: str | None = None
    default_enabled: bool = True
    source_modes: tuple[str, ...] = ("auto",)
    config_fields: tuple[ProviderConfigField, ...] = field(default_factory=tuple)
    branding: ProviderBranding = field(default_factory=ProviderBranding)


class ProviderCollector(Protocol):
    descriptor: ProviderDescriptor

    def collect_legacy(self) -> dict:
        ...

    def collect_state(self) -> ProviderState:
        ...
