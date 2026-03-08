# Core Boundaries (Python)

## Responsibility Map

- `core/ai_usage_monitor/providers/`
  - Provider-specific fetch/parsing/auth logic
  - No renderer imports
- `core/ai_usage_monitor/sources/`
  - Source policy + source model production
  - Canonical source decisioning (`preferred/resolved/fallback/availability`)
- `core/ai_usage_monitor/identity.py`
  - Provider/account/source/session identity state + snapshot isolation
  - Identity-change invalidation decisions
- `core/ai_usage_monitor/collector.py`
  - Refresh orchestration (collect -> identity compare -> optional refetch)
  - Cross-provider aggregation only
- `core/ai_usage_monitor/presentation/`
  - Renderer-agnostic popup/settings view-model generation
  - `popup_vm.py` orchestrates; helper domains split:
    - `identity_vm.py`
    - `status_vm.py`
    - `pace_vm.py`
- `core/ai_usage_monitor/shared/`
  - Cross-cutting helpers grouped by concern:
    - `http_failures.py`
    - `oauth.py`
    - `time_utils.py`
- `core/ai_usage_monitor/models.py`
  - Shared data contracts
- `core/ai_usage_monitor/api.py`
  - Public core API surface

## Public vs Internal API

- Public:
  - `core.ai_usage_monitor.collect_legacy_usage`
  - `core.ai_usage_monitor.collect_state_payload`
  - `core.ai_usage_monitor.collect_popup_vm_payload`
- Internal:
  - Provider/sources/presentation helper modules
  - Backward-compatible shims (`source_model.py`, `source_strategy.py`, `util.py`)

## Core Functions To Keep Under Regression Tests

- Collector pipeline:
  - `collect_all`
  - source attempt/fallback behavior
  - identity-change refetch behavior
- Source contracts:
  - `resolve_provider_source_plan`
  - `build_provider_source_model`
- Identity contracts:
  - `apply_identity_to_provider`
  - identity fingerprint/state key behavior
- Presentation contracts:
  - `build_popup_view_model`
  - identity/status/source/pace projection behavior
- Shared helpers:
  - HTTP failure normalization
  - token refresh error mapping
  - timestamp normalization
