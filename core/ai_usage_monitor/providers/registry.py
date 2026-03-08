from __future__ import annotations

from core.ai_usage_monitor.providers.base import ProviderDescriptor
from core.ai_usage_monitor.providers.amp import DESCRIPTOR as AMP_DESCRIPTOR
from core.ai_usage_monitor.providers.claude import DESCRIPTOR as CLAUDE_DESCRIPTOR
from core.ai_usage_monitor.providers.copilot import DESCRIPTOR as COPILOT_DESCRIPTOR
from core.ai_usage_monitor.providers.codex import DESCRIPTOR as CODEX_DESCRIPTOR
from core.ai_usage_monitor.providers.gemini import DESCRIPTOR as GEMINI_DESCRIPTOR
from core.ai_usage_monitor.providers.kilo import DESCRIPTOR as KILO_DESCRIPTOR
from core.ai_usage_monitor.providers.minimax import DESCRIPTOR as MINIMAX_DESCRIPTOR
from core.ai_usage_monitor.providers.openrouter import (
    DESCRIPTOR as OPENROUTER_DESCRIPTOR,
)
from core.ai_usage_monitor.providers.ollama import DESCRIPTOR as OLLAMA_DESCRIPTOR
from core.ai_usage_monitor.providers.opencode import DESCRIPTOR as OPENCODE_DESCRIPTOR
from core.ai_usage_monitor.providers.vertexai import DESCRIPTOR as VERTEXAI_DESCRIPTOR
from core.ai_usage_monitor.providers.zai import DESCRIPTOR as ZAI_DESCRIPTOR


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, ProviderDescriptor] = {
            AMP_DESCRIPTOR.id: AMP_DESCRIPTOR,
            CLAUDE_DESCRIPTOR.id: CLAUDE_DESCRIPTOR,
            CODEX_DESCRIPTOR.id: CODEX_DESCRIPTOR,
            GEMINI_DESCRIPTOR.id: GEMINI_DESCRIPTOR,
            COPILOT_DESCRIPTOR.id: COPILOT_DESCRIPTOR,
            VERTEXAI_DESCRIPTOR.id: VERTEXAI_DESCRIPTOR,
            OPENROUTER_DESCRIPTOR.id: OPENROUTER_DESCRIPTOR,
            OLLAMA_DESCRIPTOR.id: OLLAMA_DESCRIPTOR,
            OPENCODE_DESCRIPTOR.id: OPENCODE_DESCRIPTOR,
            ZAI_DESCRIPTOR.id: ZAI_DESCRIPTOR,
            KILO_DESCRIPTOR.id: KILO_DESCRIPTOR,
            MINIMAX_DESCRIPTOR.id: MINIMAX_DESCRIPTOR,
        }

    def list_ids(self) -> list[str]:
        return list(self._providers.keys())

    def list_descriptors(self) -> list[ProviderDescriptor]:
        return list(self._providers.values())

    def descriptor_payload(self) -> list[dict]:
        return [
            {
                "id": descriptor.id,
                "displayName": descriptor.display_name,
                "shortName": descriptor.short_name or descriptor.display_name,
                "iconKey": descriptor.branding.icon_key,
                "defaultEnabled": descriptor.default_enabled,
                "settingsAvailability": descriptor.settings_available,
                "statusPageUrl": descriptor.status_page_url,
                "usageDashboardUrl": descriptor.usage_dashboard_default_url,
                "usageDashboardBySource": descriptor.usage_dashboard_map(),
                "sourceModes": list(descriptor.source_modes),
                "supportedSources": list(descriptor.source_modes),
                "preferredSourcePolicy": descriptor.preferred_source_policy,
                "fetchStrategy": {
                    "supportsProbe": "auto" in descriptor.source_modes
                    or "probe" in descriptor.source_modes,
                },
                "providerCapabilities": {
                    "supportsLocalCli": any(
                        mode in {"cli", "local", "oauth"}
                        for mode in descriptor.source_modes
                    ),
                    "supportsApi": any(
                        mode in {"api"} for mode in descriptor.source_modes
                    ),
                    "supportsWeb": any(
                        mode in {"web", "remote"} for mode in descriptor.source_modes
                    ),
                },
                "configFields": [field.to_dict() for field in descriptor.config_fields],
                "branding": descriptor.branding.to_dict(),
            }
            for descriptor in self.list_descriptors()
        ]
