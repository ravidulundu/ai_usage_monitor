# Test Strategy (Core-First, Fixture-Driven)

## Amaç

- Core iş kurallarını renderer’dan bağımsız korumak.
- KDE/GNOME parity regresyonlarını screenshot testine gerek kalmadan erken yakalamak.
- Account/source switch, missing-data, fallback ve action semantiğini sözleşme testleriyle kilitlemek.

## Katmanlar

1. Core unit tests (zorunlu, hızlı)
- `tests/test_source_strategy.py`
- `tests/test_collector.py`
- `tests/test_identity_multi_account.py`
- `tests/test_popup_vm.py`
- `tests/test_collector_cache_invalidation.py`
- `tests/test_descriptor_payload_parse.py`

2. Fixture-based regression/smoke (parity için ana kilit)
- `tests/test_popup_vm_fixtures.py`
- `tests/test_popup_vm_state_matrix.py`
- Fixtures:
  - `tests/fixtures/popup_vm_contract_projection.json`
  - `tests/fixtures/popup_vm_states/state_matrix.json`

3. Health gates / contract checks
- `tests/test_project_health_contracts.py`
- `tests/test_core_api_boundary.py`

## İstenen 10 Alan ve Karşılığı

1. Provider descriptor parse
- `tests/test_descriptor_payload_parse.py`
- `tests/test_cli_config.py`

2. Source resolution
- `tests/test_source_strategy.py`

3. Local-first fallback
- `tests/test_source_strategy.py`
- `tests/test_collector.py`

4. Account switch detection
- `tests/test_identity_multi_account.py`
- `tests/test_collector.py`

5. Source switch detection
- `tests/test_identity_multi_account.py`
- `tests/test_popup_vm_state_matrix.py`

6. Cache invalidation
- `tests/test_collector_cache_invalidation.py`
- `tests/test_collector.py`

7. Popup-VM generation
- `tests/test_popup_vm.py`
- `tests/test_popup_vm_fixtures.py`

8. Missing-data behavior
- `tests/test_popup_vm.py`
- `tests/test_popup_vm_state_matrix.py`

9. Action semantics
- `tests/test_popup_vm.py`
- `tests/test_popup_vm_state_matrix.py`

10. Enabled vs overview provider ayrımı
- `tests/test_popup_vm.py`
- `tests/test_popup_vm_state_matrix.py`

## Fixture/State Senaryoları

`tests/fixtures/popup_vm_states/state_matrix.json` içinde zorunlu senaryolar:

- `normal_state`
- `no_data`
- `stale`
- `error`
- `fallback_active`
- `account_switched`
- `source_switched`
- `provider_unavailable`

Bu liste `tests/test_popup_vm_state_matrix.py` tarafından explicit olarak doğrulanır.

## Çalıştırma

Hızlı core regresyon:

```bash
PYTHONPATH=. ./.venv/bin/pytest -q \
  tests/test_descriptor_payload_parse.py \
  tests/test_source_strategy.py \
  tests/test_collector_cache_invalidation.py \
  tests/test_identity_multi_account.py \
  tests/test_popup_vm.py \
  tests/test_popup_vm_fixtures.py \
  tests/test_popup_vm_state_matrix.py
```

Tam test:

```bash
make test
```

Kalite kapıları:

```bash
make check
```
