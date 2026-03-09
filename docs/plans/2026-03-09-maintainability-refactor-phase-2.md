# Maintainability Refactor Phase 2 Implementation Plan

> **For Codex:** Bu plan Codex workflow'u ile adım adım uygulanır.

**Goal:** Kalan büyük hotspot modülleri davranış koruyarak daha okunabilir, daha düşük bağlaşımlı ve daha küçük sorumluluk sınırlarına ayırmak.

**Architecture:** Bu faz davranışsal feature eklemiyor. Yaklaşım, public fonksiyon imzalarını ve mevcut payload contract'larını koruyup iç orchestration akışlarını küçük helper'lara ayırmak, tekrar eden parsing/failure-state üretimini ortak sınırlara çekmek ve testlerle mevcut semantiği kilitlemek.

**Tech Stack:** Python 3.13, pytest, mypy, make health-ci

---

### Task 1: Gemini Provider Ayrıştırması

**Files:**
- Modify: `core/ai_usage_monitor/providers/gemini.py`
- Test: `tests/test_gemini_provider.py`

**Steps:**
1. Mevcut `collect_gemini(...)` akışını credential load / auth refresh retry / success mapping / error mapping sınırlarına ayır.
2. Retry yolunu küçük helper ile izole et; success ve error builder'larını ayrı tut.
3. Mevcut Gemini testleriyle davranışı doğrula; gerekiyorsa yeni success/error contract testi ekle.

### Task 2: OpenCode Provider Ayrıştırması

**Files:**
- Modify: `core/ai_usage_monitor/providers/opencode.py`
- Test: `tests/test_opencode_provider.py`

**Steps:**
1. `collect_opencode(...)` içindeki source resolution, web collect ve local fallback kararlarını helper sınırlarına ayır.
2. Source-mode kararını tek noktaya topla; web success/failure mapping'i küçük fonksiyonlara çıkar.
3. Auto/web/cli testlerini çalıştırarak mevcut semantiği koru.

### Task 3: Config Sınırlarını Netleştirme

**Files:**
- Modify: `core/ai_usage_monitor/config.py`
- Test: `tests/test_config.py`, `tests/test_cli_config.py`

**Steps:**
1. Defaults/schema, provider entry normalization ve persistence fonksiyonlarını mantıksal bloklara ayır.
2. Repeated registry/default-source kararlarını yardımcı fonksiyonlarla sadeleştir.
3. Config normalize ve CLI config testleriyle contract'ı kilitle.

### Task 4: Browser Cookies Query Soyutlaması

**Files:**
- Modify: `core/ai_usage_monitor/browser_cookies.py`
- Test: `tests/test_browser_cookies.py`

**Steps:**
1. Firefox/Chromium query akışlarını backend metadata üzerinden ortak sorgu çekirdeğine indir.
2. Mevcut cache/fingerprint ve public import API'sini koru.
3. Browser cookie testleriyle davranışı doğrula.

### Task 5: Identity Apply Ayrıştırması

**Files:**
- Modify: `core/ai_usage_monitor/identity_apply.py`
- Test: ilgili identity snapshot/store testleri

**Steps:**
1. Transition hesaplama, provider mutasyonu ve persist adımlarını ayrı helper'lara ayır.
2. `switched/changed/restored` semantiğini koru.
3. Identity test setiyle regresyon olmadığını doğrula.

### Task 6: Kilo ve MiniMax Okunabilirlik Turu

**Files:**
- Modify: `core/ai_usage_monitor/providers/kilo.py`
- Modify: `core/ai_usage_monitor/providers/minimax.py`
- Test: `tests/test_kilo_provider.py`, `tests/test_minimax_provider.py`

**Steps:**
1. Top-level collect akışlarında source/auth selection ve success/error mapping sınırlarını netleştir.
2. Boolean veya fallback odaklı karmaşık kararları isimli helper'lara ayır.
3. Provider testleriyle davranışı koru.

### Task 7: Final Verification

**Files:**
- Review only

**Steps:**
1. Hedefli pytest setlerini çalıştır.
2. `python -m mypy --config-file mypy.ini core/ai_usage_monitor` çalıştır.
3. `make health-ci PYTHON=python` çalıştır.
4. `tasks/todo.md` review notlarını tamamla.
