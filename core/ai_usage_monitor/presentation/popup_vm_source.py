from __future__ import annotations

# Backward-compatible shim for source helpers split by responsibility.
from core.ai_usage_monitor.presentation.popup_vm_source_model import (  # noqa: F401
    provider_source_model,
    provider_subtitle,
    status_page_url,
    usage_dashboard_url,
)
from core.ai_usage_monitor.presentation.popup_vm_source_presentation import (  # noqa: F401
    source_presentation_vm,
    source_reason_text,
    source_unavailable_reason,
)

__all__ = [
    "provider_source_model",
    "provider_subtitle",
    "source_presentation_vm",
    "source_reason_text",
    "source_unavailable_reason",
    "status_page_url",
    "usage_dashboard_url",
]
