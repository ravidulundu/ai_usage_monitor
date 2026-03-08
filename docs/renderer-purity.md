# Renderer Purity Rule

## Goal

Keep KDE and GNOME renderers thin and deterministic:

- Renderers only do layout, styling, visibility binding, action dispatch, and input/focus behavior.
- Shared core (`core/ai_usage_monitor/presentation/`) owns all popup policy and fallback logic.

## Forbidden In Renderers

The following must not be produced in KDE/GNOME renderer code:

- reset text production
- pace text production
- source resolution decisions
- account/source identity resolution
- missing-data policy decisions
- action mapping/policy decisions
- provider short-name/subtitle fallback generation
- metric visibility/priority decisions

## Core Ownership

`core/ai_usage_monitor/presentation/popup_vm.py` now owns:

- `popup.tabs` and `popup.switcherTabs` ordering/filtering
- provider short title/badge fallback values
- metric ordering and visibility output (`provider.metrics`)
- missing-data/status/source presentation copy
- panel indicator contract (`popup.panel`):
  - `providerId`
  - `displayText`
  - `percent`
  - `tone`
  - `iconKey`
  - `badgeText`
  - `tooltipLines`

## Renderer Consumption Contract

Renderers should consume VM payload directly and avoid reconstructing policy:

- GNOME: `extension.js` consumes `popup.switcherTabs` + `popup.panel`
- KDE: `FullRepresentation.qml` consumes `popup.switcherTabs`
- KDE compact: `CompactRepresentation.qml` consumes `popup.panel`

For settings provider rows, renderers should consume
`provider.sourceModel.settingsPresentation` and must not rebuild source/status text:

- `sourceModeLabel`
- `activeSourceLabel`
- `sourceStatusLabel`
- `fallbackLabel`
- `availabilityLabel`
- `subtitle`

## Guardrails

- Health gate syntax/lint checks run from `tools/project_health_check.py`.
- Popup VM contract regression is locked by:
  - `tests/test_popup_vm.py`
  - `tests/test_popup_vm_fixtures.py`
  - `tests/fixtures/popup_vm_contract_projection.json`
