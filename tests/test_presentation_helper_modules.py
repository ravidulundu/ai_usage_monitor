from __future__ import annotations

from core.ai_usage_monitor.models import ProviderState
from core.ai_usage_monitor.presentation.identity_vm import (
    provider_identity_refreshing,
    provider_identity_source_mode,
    switching_state_vm,
)
from core.ai_usage_monitor.presentation.status_vm import (
    provider_status_state,
    status_presentation_vm,
)


def test_identity_helpers_detect_switching_state():
    provider = ProviderState(
        id="codex",
        display_name="OpenAI Codex",
        enabled=True,
        installed=True,
        metadata={"identity": {"changed": True, "accountChanged": True}},
        extras={"accountSwitched": True},
    )

    assert provider_identity_refreshing(provider) is True
    switching = switching_state_vm(provider)
    assert switching["active"] is True
    assert switching["kind"] == "account"
    assert switching["title"] == "Account switched"


def test_identity_source_mode_prefers_identity_then_source_model():
    provider = ProviderState(
        id="opencode",
        display_name="OpenCode",
        source="api",
        metadata={"identity": {"sourceMode": "local_cli"}},
        extras={},
    )
    source_model = {"sourceStrategy": {"resolvedSource": "api"}}
    assert provider_identity_source_mode(provider, source_model) == "local_cli"

    provider.metadata = {}
    provider.extras = {}
    assert provider_identity_source_mode(provider, source_model) == "api"


def test_status_helpers_emit_incident_presentation():
    provider = ProviderState(
        id="vertexai",
        display_name="Vertex AI",
        incident={
            "indicator": "major_outage",
            "description": "Upstream outage. Investigation in progress.",
            "url": "https://status.example.com/incidents/abc",
        },
    )
    status_state = provider_status_state(
        provider=provider,
        status_url="https://status.example.com/",
        stale=False,
        source_presentation={"unavailableReason": None},
    )
    presentation = status_presentation_vm(status_state)

    assert status_state["incidentActive"] is True
    assert status_state["tone"] == "error"
    assert presentation["visible"] is True
    assert presentation["badgeLabel"] == "Service outage"
