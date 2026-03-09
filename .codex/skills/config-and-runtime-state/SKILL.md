---
    name: config-and-runtime-state
    description: |
      Config and Runtime State skilli ai_usage_monitor içindeki `config.py`, `runtime_cache.py`, `identity_snapshot.py`, `collector.py` alanlarında tetiklenir. Kullanıcı config-and-runtime-state, mimari, provider, desktop, config, identity, contract, testing, performance veya benzer bakım işi istediğinde otomatik uygulanmalıdır. Bu skill Codex merkezli repo içi çalışma düzenini zorlar; kurallar izlenmezse KDE ve GNOME yüzeyleri arasında contract drift, stale usage, secret sızıntısı veya health gate kırığı oluşur. Bu skill yalnız ai_usage_monitor için yazılmıştır; proje dışı generic öneri üretmez.
    ---

    # Config and Runtime State

    > Okuyucu maliyetini düşüren en iyi yol, bu repo için doğru sınırları her değişiklikte aynı şekilde korumaktır.

    ## Activation

    This skill activates when:
    - ``config.py`, `runtime_cache.py`, `identity_snapshot.py`, `collector.py`` altında dosya okunuyor, düzenleniyor veya gözden geçiriliyorsa
    - Kullanıcı config and runtime state, ilgili bounded context veya komşu alanları anıyorsa
    - Kod değişikliği KDE/GNOME parity, provider behavior, source semantics, identity correctness veya health gate riskini etkiliyorsa

    ## Project Context

    | Key | Value |
    |-----|-------|
    | Project | ai_usage_monitor |
    | Language | Python 3.11 baseline + QML/JS adapter layer |
    | Framework | KDE Plasma 6 QML/Kirigami, GNOME Shell 45+ GJS |
    | Relevant Stack | Python 3.11 baseline; pytest 9.0.2, mypy 1.19.1, ruff 0.15.5; KDE Plasma 6 QML/Kirigami and GNOME Shell 45+ GJS |
    | Key Decisions | Codex merkezli workflow, `.codex/skills` proje içine yazılır, shared JSON contract core-canonical kalır |

    ## Core Rules

    ### Rule 1: Config hierarchy explicit olsun

**Rule**: default -> file -> env -> runtime override sırası helper’larda açık yazılır.

**Rationale**: Yanlış override sürprizlerini önler.

**Correct** ✅:
```python
# Good: project-specific boundary preserved
def example_ok() -> str:
    return "config-and-runtime-state"
```

**Incorrect** ❌:
```python
# Bad: boundary and intent are unclear
def example_bad():
    return None
# -> Consequence: typed contract ve bakım izi zayıflar.
```
### Rule 2: Yeni config alanı normalize edilmeden kullanılmaz

**Rule**: Diskten gelen raw değer doğrudan karar noktasına girmez.

**Rationale**: Bozuk config ile runtime sapmasını engeller.

**Correct** ✅:
```python
# Good: project-specific boundary preserved
def example_ok() -> str:
    return "config-and-runtime-state"
```

**Incorrect** ❌:
```python
# Bad: boundary and intent are unclear
def example_bad():
    return None
# -> Consequence: typed contract ve bakım izi zayıflar.
```
### Rule 3: Runtime cache kısa ömürlü ve purpose-bound olmalı

**Rule**: Her cache anahtarının TTL ve invalidation sebebi yazılı olmalı.

**Rationale**: Stale veri ve sonsuz büyüyen state’i önler.

**Correct** ✅:
```python
# Good: project-specific boundary preserved
def example_ok() -> str:
    return "config-and-runtime-state"
```

**Incorrect** ❌:
```python
# Bad: boundary and intent are unclear
def example_bad():
    return None
# -> Consequence: typed contract ve bakım izi zayıflar.
```
### Rule 4: Default-enabled provider kararı ürün kararıdır

**Rule**: Yeni provider sessizce default açılmaz.

**Rationale**: Kullanıcı maliyetini ve hata yüzeyini sınırlar.

**Correct** ✅:
```python
# Good: project-specific boundary preserved
def example_ok() -> str:
    return "config-and-runtime-state"
```

**Incorrect** ❌:
```python
# Bad: boundary and intent are unclear
def example_bad():
    return None
# -> Consequence: typed contract ve bakım izi zayıflar.
```
### Rule 5: State path helper ile yönetilir

**Rule**: Dağınık `Path.home()` birleşimleri yerine merkezi path hesabı kullan.

**Rationale**: Test ve portability kolaylaşır.

**Correct** ✅:
```python
# Good: project-specific boundary preserved
def example_ok() -> str:
    return "config-and-runtime-state"
```

**Incorrect** ❌:
```python
# Bad: boundary and intent are unclear
def example_bad():
    return None
# -> Consequence: typed contract ve bakım izi zayıflar.
```

    ## Approved Patterns

    ### Pattern: Canonical Boundary

    **Use when**: Bu skill alanında yeni helper, collector, view-model veya config akışı eklerken.

    **Implementation**:
    ```python
    def normalized_polling_cache_seconds(value: int | None) -> int:
    if value is None:
        return 10
    return max(0, min(60, value))
    ```

    **Variations**:
    - Test variation: aynı boundary için küçük regression test ekle.
    - Desktop variation: render katmanı yalnız normalize payload tüketsin.

    ## Anti-Patterns

    ### 🔴 Critical Anti-Pattern
    **Severity**: CRITICAL — merge bloklanır
    **The temptation**: Sorunu en yakın katmanda hızlıca yamamak.
    **The danger**: Clamp edilmemiş cache/polling ayarı.
    **The fix**: Canonical boundary’ye geri taşı ve regression test ekle.

    ```python
    polling_cache_seconds = config.get('pollingCacheSeconds', 999999)
# unbounded and unvalidated
    ```

    ## Performance Budgets

    | Metric | Target | Hard Limit | How to Measure |
    |--------|--------|------------|----------------|
    | Reviewable diff size | <= 250 LOC net | 500 LOC net | `git diff --stat` |
    | Skill-domain unit test runtime | < 5s | 15s | `pytest -q` hedefli set |
    | Health gate after domain change | 0 failed | 0 failed | `make health-ci PYTHON=python` |

    ## Security Checklist

    - [ ] State dizinindeki dosyalar secret-adjacent kabul edilir; world-readable veya verbose dump edilmez.
    - [ ] Değişiklik proje dışı path üretmiyor; yalnız bu repo altında kalıyor.
    - [ ] Kullanıcıya gösterilen metin secret, token veya local auth path sızdırmıyor.
    - [ ] Test fixture’ları sahte secret kullanıyor; gerçek kullanıcı verisi yok.
    - [ ] Review notunda doğrulama komutları açıkça yazıldı.

    ## Error Scenarios

    | Scenario | Detection | Recovery | User Impact | Severity |
    |----------|-----------|----------|-------------|----------|
    | Config normalize edilmedi, provider yanlış açıldı | config tests veya user report | Normalizer ve defaults akışını düzelt | Beklenmedik provider fetch’i olur | High |
    | Yanlış bounded context’te patch | review veya contract test | Kodu canonical katmana taşı | Aynı bug farklı yerde tekrar eder | Medium |
    | Doğrulama atlandı | health gate eksik | Hedefli test + final health gate çalıştır | Kırık patch merge riski | High |

    ## Edge Cases

    ### Edge Case: Brownfield Compatibility
    **Scenario**: Eski payload alanı hâlâ bir UI veya test tarafından tüketiliyor.
    **Handling**: Alanı kaldırmak yerine additive geçiş uygula, testleri birlikte güncelle.
    **Code**:
    ```python
    payload = {'newField': 1, 'legacyField': 1}
    ```

    ### Edge Case: Missing Local State
    **Scenario**: Auth dosyası, cache dosyası veya config henüz mevcut değil.
    **Handling**: Fake data dönme; güvenli unavailable veya default path’e düş.
    **Code**:
    ```python
    if not path.exists():
        return None
    ```

    ### Edge Case: Platform Drift
    **Scenario**: KDE ve GNOME aynı alanı farklı yorumluyor.
    **Handling**: Semantiği renderer’dan core contract’a taşı.
    **Code**:
    ```python
    source_presentation = {'unavailableReason': None}
    ```

    ## Integration Points

    | Relationship | Skill | Detail |
    |-------------|-------|--------|
    | Depends on | `data-validation, project-architecture` | Bu skill aynı bounded context kararlarını devralır |
    | Referenced by | `testing-strategy` | Domain davranışı regression testlerle kilitlenir |
    | Shares decision | `project-architecture` | Klasör sınırı ve contract ownership tek yerden gelir |

    ## Pre-Commit Checklist

    - [ ] Tüm core rules uygulandı
    - [ ] Domain-specific anti-pattern yok
    - [ ] Hedefli testler geçti
    - [ ] `make health-ci PYTHON=python` sonucu temiz veya bilinçli doğrulandı
    - [ ] `tasks/todo.md` review bölümü güncellendi
    - [ ] Gerekliyse `tasks/lessons.md` güncellendi
