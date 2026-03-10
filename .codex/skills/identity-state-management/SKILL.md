---
    name: identity-state-management
    description: |
      Identity State Management skilli ai_usage_monitor içindeki `identity_apply.py`, `identity_snapshot.py`, `collector_helpers.py`, popup identity fields alanlarında tetiklenir. Kullanıcı identity-state-management, mimari, provider, desktop, config, identity, contract, testing, performance veya benzer bakım işi istediğinde otomatik uygulanmalıdır. Bu skill Codex merkezli repo içi çalışma düzenini zorlar; kurallar izlenmezse KDE ve GNOME yüzeyleri arasında contract drift, stale usage, secret sızıntısı veya health gate kırığı oluşur. Bu skill yalnız ai_usage_monitor için yazılmıştır; proje dışı generic öneri üretmez.
    ---

    # Identity State Management

    > Okuyucu maliyetini düşüren en iyi yol, bu repo için doğru sınırları her değişiklikte aynı şekilde korumaktır.

    ## Activation

    This skill activates when:
    - ``identity_apply.py`, `identity_snapshot.py`, `collector_helpers.py`, popup identity fields` altında dosya okunuyor, düzenleniyor veya gözden geçiriliyorsa
    - Kullanıcı identity state management, ilgili bounded context veya komşu alanları anıyorsa
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

    ### Rule 1: Fingerprint ve state key explicit taşı

**Rule**: Identity değişimi gizli yan etkiyle değil açık alanlarla yönetilir.

**Rationale**: Stale veri nedenini görünür kılar.

**Correct** ✅:
```python
# Good: project-specific boundary preserved
def example_ok() -> str:
    return "identity-state-management"
```

**Incorrect** ❌:
```python
# Bad: boundary and intent are unclear
def example_bad():
    return None
# -> Consequence: typed contract ve bakım izi zayıflar.
```
### Rule 2: Snapshot restore correctness-first çalışır

**Rule**: Aynı hesap dönüşünde snapshot restore olur; belirsiz identity’de cache reuse olmaz.

**Rationale**: Yanlış hesap karışmasını önler.

**Correct** ✅:
```python
# Good: project-specific boundary preserved
def example_ok() -> str:
    return "identity-state-management"
```

**Incorrect** ❌:
```python
# Bad: boundary and intent are unclear
def example_bad():
    return None
# -> Consequence: typed contract ve bakım izi zayıflar.
```
### Rule 3: Switch ve changed ayrımını koru

**Rule**: Refetch gerekliliği ile hesap geçişi aynı kavram değildir.

**Rationale**: Gereksiz fetch ve yanlış switching UI’ı önler.

**Correct** ✅:
```python
# Good: project-specific boundary preserved
def example_ok() -> str:
    return "identity-state-management"
```

**Incorrect** ❌:
```python
# Bad: boundary and intent are unclear
def example_bad():
    return None
# -> Consequence: typed contract ve bakım izi zayıflar.
```
### Rule 4: Identity bilinmiyorsa güvenli tarafta kal

**Rule**: Known=false durumunda eski metrics agresif biçimde korunmaz.

**Rationale**: Hesap sızıntısını engeller.

**Correct** ✅:
```python
# Good: project-specific boundary preserved
def example_ok() -> str:
    return "identity-state-management"
```

**Incorrect** ❌:
```python
# Bad: boundary and intent are unclear
def example_bad():
    return None
# -> Consequence: typed contract ve bakım izi zayıflar.
```
### Rule 5: Renderer mismatch guard zorunludur

**Rule**: VM fingerprint ile render fingerprint uyuşmazsa stale bloklar gizlenir.

**Rationale**: Kısa pencere stale render buglarını önler.

**Correct** ✅:
```python
# Good: project-specific boundary preserved
def example_ok() -> str:
    return "identity-state-management"
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
    def should_restore_snapshot(switched: bool, known: bool) -> bool:
    return switched and known
    ```

    **Variations**:
    - Test variation: aynı boundary için küçük regression test ekle.
    - Desktop variation: render katmanı yalnız normalize payload tüketsin.

    ## Anti-Patterns

    ### 🔴 Critical Anti-Pattern
    **Severity**: CRITICAL — merge bloklanır
    **The temptation**: Sorunu en yakın katmanda hızlıca yamamak.
    **The danger**: Identity doğrulanmadan eski metrics taşımak.
    **The fix**: Canonical boundary’ye geri taşı ve regression test ekle.

    ```python
    provider['sessionTokens'] = previous_provider['sessionTokens']
# blindly reusing prior account data
    ```

    ## Performance Budgets

    | Metric | Target | Hard Limit | How to Measure |
    |--------|--------|------------|----------------|
    | Reviewable diff size | <= 250 LOC net | 500 LOC net | `git diff --stat` |
    | Skill-domain unit test runtime | < 5s | 15s | `pytest -q` hedefli set |
    | Health gate after domain change | 0 failed | 0 failed | `make health-ci PYTHON=python` |

    ## Security Checklist

    - [ ] Identity snapshot’ları secret değil ama privacy-sensitive kabul edilir; debug çıktısında minimum alan göster.
    - [ ] Değişiklik proje dışı path üretmiyor; yalnız bu repo altında kalıyor.
    - [ ] Kullanıcıya gösterilen metin secret, token veya local auth path sızdırmıyor.
    - [ ] Test fixture’ları sahte secret kullanıyor; gerçek kullanıcı verisi yok.
    - [ ] Review notunda doğrulama komutları açıkça yazıldı.

    ## Error Scenarios

    | Scenario | Detection | Recovery | User Impact | Severity |
    |----------|-----------|----------|-------------|----------|
    | Hesap değişti ama UI eski metrik gösterdi | identity regression test veya kullanıcı raporu | Mismatch guard ve invalidation akışını düzelt | Yanlış usage güveni oluşur | Critical |
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
    | Depends on | `provider-patterns, presentation-contracts, config-and-runtime-state` | Bu skill aynı bounded context kararlarını devralır |
    | Referenced by | `testing-strategy` | Domain davranışı regression testlerle kilitlenir |
    | Shares decision | `project-architecture` | Klasör sınırı ve contract ownership tek yerden gelir |

    ## Pre-Commit Checklist

    - [ ] Tüm core rules uygulandı
    - [ ] Domain-specific anti-pattern yok
    - [ ] Hedefli testler geçti
    - [ ] `make health-ci PYTHON=python` sonucu temiz veya bilinçli doğrulandı
    - [ ] `tasks/todo.md` review bölümü güncellendi
    - [ ] Gerekliyse `tasks/lessons.md` güncellendi
