# Polling Cost Optimization Round 2 Implementation Plan

> **For Codex:** Bu plan Codex workflow'u ile adım adım uygulanır.

**Goal:** Periyodik `popup-vm` refresh maliyetini kısa TTL cache ile düşürmek, ama menu open ve identity-refresh yollarında canlı veri davranışını korumak.

**Architecture:** Cache sınırı provider içinde değil, `collect_popup_vm_payload(...)` çıktısı. Backend `force` parametresiyle cache bypass eder. KDE/GNOME timer path cache kullanır; menu open ve identity refresh path `--force` geçirir.

**Tech Stack:** Python, QML, GJS, pytest, project health checks

---

### Task 1: Backend popup-vm cache

**Files:**
- Modify: `core/ai_usage_monitor/config.py`
- Modify: `core/ai_usage_monitor/collector.py`
- Modify: `core/ai_usage_monitor/runtime_cache.py`
- Test: `tests/test_config.py`
- Test: `tests/test_collector.py`

### Task 2: CLI force parsing

**Files:**
- Modify: `core/ai_usage_monitor/cli.py`
- Test: `tests/test_cli_config.py`

### Task 3: KDE/GNOME force wiring

**Files:**
- Modify: `com.aiusagemonitor/contents/ui/main.qml`
- Modify: `gnome-extension/aiusagemonitor@aimonitor/indicatorLifecycleMixin.js`
- Modify: `gnome-extension/aiusagemonitor@aimonitor/extension.js`
- Modify: `tools/project_health_contracts.py`
- Test: `tests/test_project_health_contracts.py`

### Task 4: Verification

**Run:**
- `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_collector.py tests/test_config.py tests/test_cli_config.py tests/test_project_health_contracts.py`
- `PYTHONPATH=. ./.venv/bin/python -m mypy --config-file mypy.ini core/ai_usage_monitor`
- `make health-ci PYTHON=python`

**Exit Criteria:**
- Timer path TTL içinde `collect_all()` tekrarlamaz
- `--force` cache bypass eder
- KDE/GNOME interaction paths `--force` geçirir
- Quality gate temizdir
