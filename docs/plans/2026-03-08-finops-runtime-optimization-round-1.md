# FinOps Runtime Optimization Round 1

> **For Codex:** Bu plan Codex workflow'u ile adım adım uygulanır.

**Goal:** Gereksiz CPU, disk I/O ve dış ağ işini davranış riski oluşturmadan azaltmak. İlk tur, polling mimarisini kırmadan aynı refresh içindeki tekrar işi ve kısa aralıklı tekrar fetch'leri hedefler.

**Architecture:** Değişiklikler dört küçük parçaya ayrılır: ortak kısa ömürlü runtime cache yardımıcısı, Codex local usage/snapshot tek-geçiş refactor'ı, OpenCode auto akışında lazy local fallback, status/cookie yolunda TTL cache. Tüm değişiklikler mevcut state dizinini (`AI_USAGE_MONITOR_STATE_DIR` veya `~/.cache/ai-usage-monitor`) kullanır.

**Tech Stack:** Python, pytest, mypy, project health checks

---

### Task 1: Kısa ömürlü runtime cache altyapısı

**Files:**
- Create: `core/ai_usage_monitor/runtime_cache.py`
- Modify: `core/ai_usage_monitor/status.py`
- Modify: `core/ai_usage_monitor/browser_cookies.py`

**Intent:**
- JSON dosya tabanlı küçük cache yardımıcısı ekle
- Status page ve browser cookie import için TTL/fingerprint destekli tekrar azaltımı sağla

### Task 2: Codex çift taramayı tek geçişe indir

**Files:**
- Modify: `core/ai_usage_monitor/local_usage.py`
- Modify: `core/ai_usage_monitor/providers/codex.py`
- Modify: `tests/test_local_usage.py`
- Modify: `tests/test_codex_normalization.py`

**Intent:**
- `collect_codex()` içindeki local usage ve latest token snapshot için yapılan iki ayrı dosya taramasını tek geçişten besle
- Account switch cutoff davranışını koru

### Task 3: OpenCode auto modunda gereksiz local scan'i kaldır

**Files:**
- Modify: `core/ai_usage_monitor/providers/opencode.py`
- Modify: `tests/test_opencode_provider.py`

**Intent:**
- `source=auto` ve web fetch başarılıysa local CLI state'i önceden kurma
- Fallback gerektiğinde local CLI hesabını hala güvenli şekilde kullan

### Task 4: Verification

**Files:**
- Create: `tests/test_status.py`
- Modify: `tests/test_browser_cookies.py`
- Modify: `tasks/todo.md`

**Run:**
- `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_local_usage.py tests/test_codex_normalization.py tests/test_opencode_provider.py tests/test_browser_cookies.py tests/test_status.py`
- `PYTHONPATH=. ./.venv/bin/python -m mypy --config-file mypy.ini core/ai_usage_monitor`
- `make health-ci PYTHON=python`

**Exit Criteria:**
- Mevcut provider davranışı korunur
- Yeni cache katmanı cache miss/failure durumunda canlı yola düşer
- Hedefli testler ve strict kalite kapıları temiz geçer
