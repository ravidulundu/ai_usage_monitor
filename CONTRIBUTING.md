# Contributing

## Quick Onboarding

```bash
make setup
```

This command does the following:

- creates `.venv` (if missing)
- installs Python dev dependencies
- installs Node dependencies (`npm ci`)
- installs the `pre-commit` hook

## Daily Commands

```bash
make format   # apply Python formatting
make lint     # fast quality gates
make typecheck # real static type check for Python core (mypy)
make check    # full quality gates + pytest
make test     # tests only
```

Equivalent npm commands:

```bash
npm run format
npm run lint
npm run typecheck
npm run check
npm run test
```

## Git Hook

Install:

```bash
make hooks-install
```

Run all files manually:

```bash
make hooks-run
```

## Coding Rules (Short)

1. Renderer purity
- Do not put business logic in KDE/GNOME renderer layers.
- Renderers only handle `layout`, `style/theme binding`, `visibility binding`, `action dispatch`, `input behavior`.

2. Component boundaries
- Split large UI files by responsibility.
- Do not combine data policy and rendering in a single component.

3. Provider/account/source state model
- Account/source resolution and identity decisions must be produced in core only.
- Renderers must consume canonical fields from core only.

4. File size discipline
- Helper: target ~50-120 lines.
- UI component: target ~80-200 lines.
- If an orchestration file is 250+ lines, open a split/refactor plan.

5. No duplicated presentation logic
- Do not duplicate text/policy/fallback rules across KDE and GNOME.
- Popup/settings presentation semantics must come from one source in the core `presentation` layer.

## PR Expectations

- Add tests for behavior changes.
- Do not open a PR unless `make health-ci` and `make typecheck` are green.
- New code must not bypass existing health guards.

## Enforced Quality Gates (CI)

CI enforces the following gates:

- `python-syntax`, `js-syntax`, `qml-syntax`, `shellcheck`
- `ruff-lint`, `ruff-format`
- `gjs-lint`
- `renderer-purity`
- `debt-guardrails`
- `size-complexity-warnings` (in CI, warnings also fail)
- `file-budgets`, `function-budgets`
- `gnome-lifecycle-contract`, `kde-lifecycle-contract`
- `mypy`, `pytest`

Local CI equivalent:

```bash
make health-ci
```

## Debt Prevention Rules (Hard)

The following are prohibited in this repo:

1. Adding new baseline locks (`FILE_SIZE_BASELINE_REDUCTION_PLAN`, `PYTHON_FUNCTION_COMPLEXITY_BASELINES`).
2. Adding `ignore_errors = True` overrides in `mypy.ini`.
3. Generating business/presentation policy text inside renderers.

When new debt appears, use this approach:

1. First, reduce debt with real split/refactor work.
2. Then run `make health-ci`, `make typecheck`, and related tests.
3. Do not silence alarms via baseline lock.

## Responsibility Boundaries

1. Shared core + two renderers:
- Core: provider/source/account/identity/presentation policy.
- KDE/GNOME: layout + render + dispatch + input behavior.

2. Renderer purity:
- Renderers consume canonical payload fields only.
- Reset/pace/source/fallback/visibility policy is produced in core.

3. Component/file discipline:
- Helper: 50-120 lines.
- UI component: 80-200 lines.
- Orchestrator >250 lines or oversized functions are alarms and must be split.
