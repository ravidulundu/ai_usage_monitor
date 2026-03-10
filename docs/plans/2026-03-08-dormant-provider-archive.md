# Dormant Provider Archive Implementation Plan

> **For Codex:** Bu plan Codex workflow'u ile adım adım uygulanır.

**Goal:** Shipped runtime'a bağlı olmayan dormant provider modüllerini (`kiro`, `jetbrains`, `warp`, `kimik2`) aktif kod yolundan çıkarıp arşivlenmiş/test-dışı bir yüzeye taşımak.

**Architecture:** Refactor üç parçalı ilerler: önce bu provider'ların kalan referanslarını test ve dokümantasyon katmanında görünür kıl, sonra source dosyalarını `archive` alanına taşı ve aktif paket/export zincirini temizle, en sonda kalite kapıları ve dokümantasyonu yeni duruma hizala. Runtime davranışı korunmalı; shipped registry ve fetch stratejileri aynı kalmalı.

**Tech Stack:** Python, pytest, mypy, ruff, project health checks, ripgrep

---

### Task 1: Archive hedefinin kapsamını kilitle

**Files:**
- Modify: `tasks/todo.md`
- Review: `core/ai_usage_monitor/providers/kiro.py`
- Review: `core/ai_usage_monitor/providers/jetbrains.py`
- Review: `core/ai_usage_monitor/providers/warp.py`
- Review: `core/ai_usage_monitor/providers/kimik2.py`
- Review: `tests/test_kiro_provider.py`
- Review: `tests/test_jetbrains_provider.py`
- Review: `tests/test_api_providers.py`
- Review: `tests/test_cli_detect.py`

**Step 1: Görev checklist’ini görünür yap**

`tasks/todo.md` içine arşivleme checklist’i ekle.

**Step 2: Kalan referansları doğrula**

Run: `rg -n "\\b(kiro|jetbrains|warp|kimik2)\\b" core tests README.md docs`

Expected: yalnız testler, legacy docs ve provider source dosyaları listelenir; runtime registry/fetch zinciri dışında kaldığı doğrulanır.

**Step 3: Arşiv politikasını yazılı hale getir**

Kural:
- runtime import yok
- package `__all__` export yok
- CI default test setinde yok
- istersek archive smoke testleri ayrı hedefte koşulabilir

**Step 4: Commit**

```bash
git add tasks/todo.md
git commit -m "docs: scope dormant provider archive work"
```

### Task 2: Önce kırılmayı gösteren testleri güncelle

**Files:**
- Modify: `tests/test_kiro_provider.py`
- Modify: `tests/test_jetbrains_provider.py`
- Modify: `tests/test_api_providers.py`
- Modify: `tests/test_cli_detect.py`
- Create: `tests/test_archived_provider_boundaries.py`

**Step 1: Yeni sınır testi yaz**

`tests/test_archived_provider_boundaries.py` içinde şu davranışları doğrula:

```python
from pathlib import Path


def test_archived_provider_sources_are_not_in_active_provider_package():
    package_text = Path("core/ai_usage_monitor/providers/__init__.py").read_text()
    assert "collect_kiro" not in package_text
    assert "collect_jetbrains" not in package_text
    assert "collect_warp" not in package_text
    assert "collect_kimik2" not in package_text
```

**Step 2: Mevcut provider testlerini archive yoluna çevir**

Importları hedef path'e taşı:
- `core.ai_usage_monitor.archived_providers.kiro`
- `core.ai_usage_monitor.archived_providers.jetbrains`
- `core.ai_usage_monitor.archived_providers.warp`
- `core.ai_usage_monitor.archived_providers.kimik2`

**Step 3: Testi fail ettiğini doğrula**

Run: `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_archived_provider_boundaries.py tests/test_kiro_provider.py tests/test_jetbrains_provider.py tests/test_api_providers.py tests/test_cli_detect.py`

Expected: yeni archive path'leri henüz yoksa import failure veya boundary failure görülür.

**Step 4: Commit**

```bash
git add tests/test_archived_provider_boundaries.py tests/test_kiro_provider.py tests/test_jetbrains_provider.py tests/test_api_providers.py tests/test_cli_detect.py
git commit -m "test: lock archived provider boundaries"
```

### Task 3: Provider dosyalarını archive namespace’ine taşı

**Files:**
- Create: `core/ai_usage_monitor/archived_providers/__init__.py`
- Create: `core/ai_usage_monitor/archived_providers/kiro.py`
- Create: `core/ai_usage_monitor/archived_providers/jetbrains.py`
- Create: `core/ai_usage_monitor/archived_providers/warp.py`
- Create: `core/ai_usage_monitor/archived_providers/kimik2.py`
- Modify: `core/ai_usage_monitor/providers/kiro.py`
- Modify: `core/ai_usage_monitor/providers/jetbrains.py`
- Modify: `core/ai_usage_monitor/providers/warp.py`
- Modify: `core/ai_usage_monitor/providers/kimik2.py`

**Step 1: Arşiv namespace’ini oluştur**

`core/ai_usage_monitor/archived_providers/__init__.py` içinde açık export listesi yaz.

**Step 2: Kodları yeni path’e taşı**

Her provider dosyasını archive namespace’ine birebir taşı.

**Step 3: Eski dosyalarda kırılma kararını uygula**

İki seçenekten biri:
- tercih edilen: eski dosyaları sil ve test/docs importlarını yeni path’e taşı
- compat gerekiyorsa: eski dosyalarda kısa shim bırak

Bu repo için tercih edilen seçenek: eski dosyaları silmek yerine kısa shim bırakma.
Sebep: docs/test dışı local kullanıcı importları bilinmiyor.

Shim örneği:

```python
"""Compatibility shim; archived provider implementation moved."""

from core.ai_usage_monitor.archived_providers.kiro import *  # noqa: F403
```

**Step 4: Testleri tekrar çalıştır**

Run: `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_archived_provider_boundaries.py tests/test_kiro_provider.py tests/test_jetbrains_provider.py tests/test_api_providers.py tests/test_cli_detect.py`

Expected: PASS

**Step 5: Commit**

```bash
git add core/ai_usage_monitor/archived_providers core/ai_usage_monitor/providers/kiro.py core/ai_usage_monitor/providers/jetbrains.py core/ai_usage_monitor/providers/warp.py core/ai_usage_monitor/providers/kimik2.py
git commit -m "refactor: archive dormant provider implementations"
```

### Task 4: Aktif yüzeyi ve dokümantasyonu hizala

**Files:**
- Modify: `README.md`
- Modify: `docs/core-boundaries.md`
- Modify: `tests/test_config.py`
- Modify: `tests/test_provider_registry_shape.py`
- Optionally Modify: `docs/reference/codexbar/providers.md`
- Optionally Modify: `docs/reference/codexbar/configuration.md`

**Step 1: README ve boundaries notunu güncelle**

Net ifade ekle:
- bu provider'lar shipped runtime'da aktif değil
- archive namespace altında tutuluyor
- default runtime ve UI yüzeyinin parçası değiller

**Step 2: Boundary testlerini güncelle**

Gerekirse aktif provider listesi yanında archive statüsünü de assert et.

**Step 3: Legacy reference docs kararını uygula**

İki seçenek:
- docs/reference/codexbar altını tarihsel referans olarak bırak
- ya da “archived / not shipped” notu ekle

Bu repo için en güvenli yaklaşım: not eklemek, tam silmemek.

**Step 4: Commit**

```bash
git add README.md docs/core-boundaries.md tests/test_config.py tests/test_provider_registry_shape.py docs/reference/codexbar/providers.md docs/reference/codexbar/configuration.md
git commit -m "docs: mark dormant providers as archived"
```

### Task 5: Full verification

**Files:**
- Review: `core/ai_usage_monitor/archived_providers/**`
- Review: `core/ai_usage_monitor/providers/**`
- Review: `tests/**`

**Step 1: Hedefli kalite kapıları**

Run: `./.venv/bin/ruff check core tools tests bin --select F401,F841`

Expected: PASS

**Step 2: Hedefli test paketi**

Run: `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_archived_provider_boundaries.py tests/test_kiro_provider.py tests/test_jetbrains_provider.py tests/test_api_providers.py tests/test_cli_detect.py tests/test_config.py tests/test_provider_registry_shape.py`

Expected: PASS

**Step 3: Tam strict kapı**

Run: `make health-ci PYTHON=python`

Expected: `Summary: 17 passed/warned, 0 failed, 0 warnings`

**Step 4: Commit**

```bash
git add -A
git commit -m "chore: complete dormant provider archive"
```
