---
    name: performance-optimization
    description: |
      Performance Optimization skilli ai_usage_monitor içindeki `collector.py`, `collector_helpers.py`, `local_usage.py`, `status.py`, `browser_cookies.py`, desktop timers alanlarında tetiklenir. Kullanıcı performance-optimization, mimari, provider, desktop, config, identity, contract, testing, performance veya benzer bakım işi istediğinde otomatik uygulanmalıdır. Bu skill Codex merkezli repo içi çalışma düzenini zorlar; kurallar izlenmezse KDE ve GNOME yüzeyleri arasında contract drift, stale usage, secret sızıntısı veya health gate kırığı oluşur. Bu skill yalnız ai_usage_monitor için yazılmıştır; proje dışı generic öneri üretmez.
    ---

    # Performance Optimization

    > Okuyucu maliyetini düşüren en iyi yol, bu repo için doğru sınırları her değişiklikte aynı şekilde korumaktır.

    ## Activation

    This skill activates when:
    - ``collector.py`, `collector_helpers.py`, `local_usage.py`, `status.py`, `browser_cookies.py`, desktop timers` altında dosya okunuyor, düzenleniyor veya gözden geçiriliyorsa
    - Kullanıcı performance optimization, ilgili bounded context veya komşu alanları anıyorsa
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

    ### Rule 1: Timer yolunda cached refresh tercih et

**Rule**: UI timer varsayılan olarak live force-fetch yapmamalıdır.

**Rationale**: Arka plan CPU ve ağ maliyetini düşürür.

**Correct** ✅:
```python
# Good: project-specific boundary preserved
def example_ok() -> str:
    return "performance-optimization"
```

**Incorrect** ❌:
```python
# Bad: boundary and intent are unclear
def example_bad():
    return None
# -> Consequence: typed contract ve bakım izi zayıflar.
```
### Rule 2: Tam dosya taramasını memoize et

**Rule**: Fingerprint değişmediyse local usage parser tekrar full scan yapmaz.

**Rationale**: Disk I/O ve CPU yükünü sınırlar.

**Correct** ✅:
```python
# Good: project-specific boundary preserved
def example_ok() -> str:
    return "performance-optimization"
```

**Incorrect** ❌:
```python
# Bad: boundary and intent are unclear
def example_bad():
    return None
# -> Consequence: typed contract ve bakım izi zayıflar.
```
### Rule 3: Status ve cookie erişimine TTL koy

**Rule**: Dakikalık değişmeyen veri her cycle yeniden çekilmez.

**Rationale**: Gereksiz remote/local churn’ü azaltır.

**Correct** ✅:
```python
# Good: project-specific boundary preserved
def example_ok() -> str:
    return "performance-optimization"
```

**Incorrect** ❌:
```python
# Bad: boundary and intent are unclear
def example_bad():
    return None
# -> Consequence: typed contract ve bakım izi zayıflar.
```
### Rule 4: Provider freshness seçici olmalı

**Rule**: Her provider aynı cache politikasını kullanmaz.

**Rationale**: Stale account verisi ile aşırı fetch arasındaki dengeyi korur.

**Correct** ✅:
```python
# Good: project-specific boundary preserved
def example_ok() -> str:
    return "performance-optimization"
```

**Incorrect** ❌:
```python
# Bad: boundary and intent are unclear
def example_bad():
    return None
# -> Consequence: typed contract ve bakım izi zayıflar.
```
### Rule 5: Yeni loop eklemeden önce event-driven seçeneği sorgula

**Rule**: Polling son çare olmalıdır.

**Rationale**: Uzun vadeli FinOps borcunu sınırlar.

**Correct** ✅:
```python
# Good: project-specific boundary preserved
def example_ok() -> str:
    return "performance-optimization"
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
    def should_use_cached_popup(now_ts: float, cached_until_ts: float) -> bool:
    return now_ts < cached_until_ts
    ```

    **Variations**:
    - Test variation: aynı boundary için küçük regression test ekle.
    - Desktop variation: render katmanı yalnız normalize payload tüketsin.

    ## Anti-Patterns

    ### 🔴 Critical Anti-Pattern
    **Severity**: CRITICAL — merge bloklanır
    **The temptation**: Sorunu en yakın katmanda hızlıca yamamak.
    **The danger**: Her popup timer tick’inde live fetch yapmak.
    **The fix**: Canonical boundary’ye geri taşı ve regression test ekle.

    ```python
    while True:
    fetch_all_usage(force=True)
# tight loop burns CPU
    ```

    ## Performance Budgets

    | Metric | Target | Hard Limit | How to Measure |
    |--------|--------|------------|----------------|
    | Reviewable diff size | <= 250 LOC net | 500 LOC net | `git diff --stat` |
    | Skill-domain unit test runtime | < 5s | 15s | `pytest -q` hedefli set |
    | Health gate after domain change | 0 failed | 0 failed | `make health-ci PYTHON=python` |

    ## Security Checklist

    - [ ] Cache içine secret veya raw cookie materyali yazma; yalnız normalize edilmiş, gerekli minimum state sakla.
    - [ ] Değişiklik proje dışı path üretmiyor; yalnız bu repo altında kalıyor.
    - [ ] Kullanıcıya gösterilen metin secret, token veya local auth path sızdırmıyor.
    - [ ] Test fixture’ları sahte secret kullanıyor; gerçek kullanıcı verisi yok.
    - [ ] Review notunda doğrulama komutları açıkça yazıldı.

    ## Error Scenarios

    | Scenario | Detection | Recovery | User Impact | Severity |
    |----------|-----------|----------|-------------|----------|
    | Fingerprint cache stale kaldı | Regression test veya unexpected stale metric | Force path ve invalidation kuralını düzelt | Kullanıcı eski usage görebilir | High |
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
    | Depends on | `project-architecture, python-standards, testing-strategy` | Bu skill aynı bounded context kararlarını devralır |
    | Referenced by | `testing-strategy` | Domain davranışı regression testlerle kilitlenir |
    | Shares decision | `project-architecture` | Klasör sınırı ve contract ownership tek yerden gelir |

    ## Pre-Commit Checklist

    - [ ] Tüm core rules uygulandı
    - [ ] Domain-specific anti-pattern yok
    - [ ] Hedefli testler geçti
    - [ ] `make health-ci PYTHON=python` sonucu temiz veya bilinçli doğrulandı
    - [ ] `tasks/todo.md` review bölümü güncellendi
    - [ ] Gerekliyse `tasks/lessons.md` güncellendi
