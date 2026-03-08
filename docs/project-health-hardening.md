# Project Health Hardening

## Goal

Keep a single shared core with two thin renderers:

- Core owns provider logic, source resolution, identity, and popup/settings view-models.
- KDE/GNOME renderer layers own only render + action dispatch.

## Implementation Plan (Incremental)

### Phase 1 - Quality Gates (Applied)

1. Add a single health entrypoint (`tools/project_health_check.py`)
2. Add CI workflow to run strict health checks on PR/push
3. Add pre-commit hooks for local fast checks
4. Add lightweight line-budget guardrails for known hot files
5. Add renderer-purity static checks
6. Add lifecycle contract checks for GNOME cleanup paths
7. Add type-ish signature checks for core boundary APIs
8. Add function-level complexity budgets for hotspot core files
9. Fix JS syntax gate for QML `.pragma library` files
10. Fix shellcheck violations in KDE install/upgrade scripts
11. Add warning-first file-size and function-complexity early alarms

### Phase 2 - Cleanup (Completed)

1. Centralize health contracts in a single shared module:
   - `tools/project_health_contracts.py`
   - consumed by both `tools/project_health_check.py` and `tests/test_project_health_contracts.py`
2. Split oversized files by responsibilities:
   - GNOME `extension.js`: panel, tabs, provider-detail builders
   - KDE `configGeneral.qml`: group sections and row delegates
   - Core `popup_vm.py`: source/status/metric mappers
3. Move renderer helper logic that is business-like into core VM mapping where possible.
4. Tighten file budgets after first split lands.
5. Renderer purity contract documented:
   - `docs/renderer-purity.md`

### Phase 3 - Regression Hardening (Completed)

1. Add snapshot fixtures for popup-vm contracts.
   - Added: `tests/fixtures/popup_vm_contract_projection.json`
   - Added: `tests/test_popup_vm_fixtures.py`
2. Add parity tests for KDE/GNOME consumption semantics.
3. Add lifecycle regression checks for rapid refresh/open-close cycles.
4. Add identity switch stress tests with source/account flip sequences.

## Risk Reduction Map

- Python/JS/QML syntax checks:
  - Reduce broken release artifacts and runtime parse failures.
- Ruff lint (`F,E9`) + format drift reporting:
  - Reduce hidden runtime bugs and establish formatter visibility without disruptive mass rewrite.
- Pre-commit quick checks:
  - Prevent obvious regressions before commit.
- CI strict mode:
  - Enforce shared baseline across contributors.
- Renderer purity checks:
  - Prevent provider/business logic creep into KDE/GNOME layers.
- Line budgets:
  - Slow down new monolith growth and force decomposition pressure.
- GNOME lifecycle contract:
  - Reduce timeout/cancellable/disconnect leak regressions.
- Type-ish signatures on boundary APIs:
  - Reduce accidental untyped interface drift in shared core contracts.
- Function-level budgets:
  - Catch monolithic function growth earlier than file-level budgets.
- Warning-first size/complexity alarms:
  - Surface hotspots early and block in CI (`--fail-on-warn`).
  - Keep orchestrators/components from silently becoming monoliths.
  - Use target-oriented thresholds (helper `50-120`, UI `80-200`, orchestration `250+ alarm`).
- Shared health contract module:
  - Prevent CI/test/tool rule drift caused by duplicated constants.
- Popup-vm regression fixture:
  - Lock a stable renderer-facing contract projection across refactors.

## Maintenance Guardrails (Current Policy)

1. CI strict mode:
- `make health-ci` runs `tools/project_health_check.py --mode ci --fail-on-warn`.
- Any warning or fail blocks PR.

2. No debt lock policy:
- `FILE_SIZE_BASELINE_REDUCTION_PLAN = {}`
- `PYTHON_FUNCTION_COMPLEXITY_BASELINES = {}`
- Yeni baseline lock eklemek policy ihlali.

3. No mypy quarantine policy:
- `mypy.ini` içinde `ignore_errors = True` yasak.
- typing debt only fix/refactor with real annotations.

4. Lifecycle contract symmetry:
- GNOME ve KDE lifecycle token contract’ları health gate içinde zorunlu.
- Syntax geçmesi, lifecycle sağlıklı olduğu anlamına gelmez; ayrı kontrol edilir.

5. Popup/settings fixture regression:
- Popup VM state matrix + contract projection fixture testleri zorunlu.
- Settings source/status presentation matrix fixture testleri zorunlu.

## Commands

- Quick local gate:
  - `python3 tools/project_health_check.py --mode quick`
- Full local gate:
  - `python3 tools/project_health_check.py --mode full`
- CI-equivalent strict gate:
  - `python3 tools/project_health_check.py --mode ci`
