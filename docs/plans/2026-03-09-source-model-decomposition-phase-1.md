# Source Model Decomposition Phase 1 Implementation Plan

> **For Codex:** Bu plan Codex workflow'u ile adım adım uygulanır.

**Goal:** `core/ai_usage_monitor/sources/model.py` içindeki source-model üretimini daha küçük modüllere ayırırken mevcut payload sözleşmesini korumak.

**Architecture:** Public giriş noktası `build_provider_source_model(...)` aynı kalacak. İlk fazda yalnız iç yapıyı ayıracağız: input/runtime DTO'ları, settings presentation üretimi ve payload assembly ayrı modüllere taşınacak. Davranış değişikliği yerine sözleşme koruması hedeflenecek.

**Tech Stack:** Python, pytest, mypy

---

### Task 1: Source Model Contract'ını Testle Kilitle

**Files:**
- Modify: `tests/test_settings_presentation_matrix.py`
- Modify: `tests/test_source_strategy.py`
- Read: `tests/fixtures/settings_presentation_matrix.json`

**Step 1: Write the failing test**

```python
def test_build_provider_source_model_contract_is_stable():
    provider = ...
    descriptor = ...
    settings = ...

    payload = build_provider_source_model(
        provider=provider,
        descriptor=descriptor,
        settings=settings,
        configured_source="local_cli",
        resolution={"preferredSource": "local_cli"},
    )

    assert payload["settingsPresentation"]["sourceModeLabel"] == "..."
    assert payload["sourceStrategy"]["preferredSource"] == "local_cli"
    assert payload["availability"]["apiConfigured"] is False
```

**Step 2: Run test to verify it fails if contract drifts**

Run: `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_settings_presentation_matrix.py tests/test_source_strategy.py`

Expected: PASS now; later extraction sırasında sözleşme drift'i olursa FAIL.

**Step 3: Keep assertions focused on public payload shape**

```python
EXPECTED_TOP_LEVEL_KEYS = {
    "canonicalMode",
    "providerCapabilities",
    "sourceStrategy",
    "availability",
    "settingsPresentation",
}
assert EXPECTED_TOP_LEVEL_KEYS <= set(payload)
```

**Step 4: Run test again**

Run: `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_settings_presentation_matrix.py tests/test_source_strategy.py`

Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_settings_presentation_matrix.py tests/test_source_strategy.py
git commit -m "test: lock source model contract before refactor"
```

### Task 2: Input/Runtime Veri Kümelerini Adlandır

**Files:**
- Create: `core/ai_usage_monitor/sources/model_types.py`
- Modify: `core/ai_usage_monitor/sources/model.py`
- Test: `tests/test_source_strategy.py`

**Step 1: Write the failing test**

```python
def test_build_provider_source_model_accepts_existing_inputs():
    payload = build_provider_source_model(...)
    assert payload["resolvedSource"] == "api"
```

**Step 2: Run test to verify baseline**

Run: `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_source_strategy.py`

Expected: PASS

**Step 3: Write minimal implementation**

```python
@dataclass(frozen=True)
class SourceModelInputs:
    available_sources: tuple[str, ...]
    preferred_policy: str
    preferred_source: str
    active_source: str
    resolution_data: dict[str, Any]

@dataclass(frozen=True)
class SourceModelRuntime:
    has_local_capability: bool
    has_api_capability: bool
    has_web_capability: bool
    local_tool_detected: bool
    api_configured: bool
    api_key_present: bool
    auth_state: str
    auth_valid: bool | None
    rate_limit_state: str
    fallback_active: bool
    fallback_reason: str
    canonical_mode: str
    source_label: str
    resolution_reason: str
    supports_probe: bool
    fallback_chain: list[str]
    candidates: list[dict[str, str]]
    source_details: str
    fallback_label: str
```

**Step 4: Replace raw `dict[str, Any]` plumbing in `model.py`**

```python
inputs = build_source_model_inputs(...)
runtime = build_source_model_runtime(provider, settings, inputs)
```

**Step 5: Run tests**

Run: `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_source_strategy.py tests/test_settings_presentation_matrix.py`

Expected: PASS

**Step 6: Commit**

```bash
git add core/ai_usage_monitor/sources/model.py core/ai_usage_monitor/sources/model_types.py tests/test_source_strategy.py
git commit -m "refactor: name source model input and runtime structures"
```

### Task 3: Settings Presentation Üretimini Ayır

**Files:**
- Create: `core/ai_usage_monitor/sources/settings_presentation.py`
- Modify: `core/ai_usage_monitor/sources/model.py`
- Test: `tests/test_settings_presentation_matrix.py`

**Step 1: Write the failing test**

```python
def test_settings_presentation_labels_match_fixture_matrix():
    ...
    assert payload["settingsPresentation"] == expected
```

**Step 2: Run test**

Run: `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_settings_presentation_matrix.py`

Expected: PASS baseline

**Step 3: Move implementation**

```python
def build_settings_presentation(
    *,
    provider: ProviderState,
    inputs: SourceModelInputs,
    runtime: SourceModelRuntime,
) -> dict[str, Any]:
    ...
```

**Step 4: Keep `model.py` as facade**

```python
settings_presentation = build_settings_presentation(
    provider=provider,
    inputs=inputs,
    runtime=runtime,
)
```

**Step 5: Run tests**

Run: `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_settings_presentation_matrix.py tests/test_source_strategy.py`

Expected: PASS

**Step 6: Commit**

```bash
git add core/ai_usage_monitor/sources/model.py core/ai_usage_monitor/sources/settings_presentation.py tests/test_settings_presentation_matrix.py
git commit -m "refactor: extract source settings presentation builder"
```

### Task 4: Payload Assembly'yi Ayır ve Public Facade'ı Küçült

**Files:**
- Create: `core/ai_usage_monitor/sources/payloads.py`
- Modify: `core/ai_usage_monitor/sources/model.py`
- Modify: `core/ai_usage_monitor/sources/__init__.py`
- Test: `tests/test_source_strategy.py`
- Test: `tests/test_popup_vm.py`

**Step 1: Write the failing test**

```python
def test_popup_vm_source_fields_still_project_correctly():
    payload = build_popup_view_model(...)
    provider = payload["popup"]["providers"][0]
    assert "sourceStrategy" in provider
    assert "availability" in provider
```

**Step 2: Run test**

Run: `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_source_strategy.py tests/test_popup_vm.py`

Expected: PASS baseline

**Step 3: Extract payload composition**

```python
def build_provider_source_payload(
    *,
    inputs: SourceModelInputs,
    runtime: SourceModelRuntime,
    settings_presentation: dict[str, Any],
) -> dict[str, Any]:
    ...
```

**Step 4: Shrink `build_provider_source_model(...)`**

```python
def build_provider_source_model(...):
    inputs = build_source_model_inputs(...)
    runtime = build_source_model_runtime(provider, settings, inputs)
    settings_presentation = build_settings_presentation(...)
    return build_provider_source_payload(...)
```

**Step 5: Run targeted verification**

Run: `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_source_strategy.py tests/test_settings_presentation_matrix.py tests/test_popup_vm.py`

Expected: PASS

**Step 6: Run static verification**

Run: `PYTHONPATH=. ./.venv/bin/python -m mypy --config-file mypy.ini core/ai_usage_monitor`

Expected: PASS

**Step 7: Commit**

```bash
git add core/ai_usage_monitor/sources/model.py core/ai_usage_monitor/sources/payloads.py core/ai_usage_monitor/sources/__init__.py tests/test_source_strategy.py tests/test_popup_vm.py
git commit -m "refactor: split source model payload assembly"
```

### Task 5: Final Verification and Review Notes

**Files:**
- Modify: `tasks/todo.md`

**Step 1: Run regression suite**

Run: `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_source_strategy.py tests/test_settings_presentation_matrix.py tests/test_popup_vm.py`

Expected: PASS

**Step 2: Run quality gates**

Run: `make health-ci PYTHON=python`

Expected: PASS or only known warnings, no new failures

**Step 3: Update review notes**

```md
### Review

- `sources/model.py` public API korundu
- source payload contract fixture/test ile kilitlendi
- settings presentation ve payload assembly ayrı modüllere taşındı
```

**Step 4: Commit**

```bash
git add tasks/todo.md
git commit -m "docs: record source model decomposition review"
```
