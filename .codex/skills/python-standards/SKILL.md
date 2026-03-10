---
    name: python-standards
    description: |
      Python Standards skilli ai_usage_monitor içindeki `core/ai_usage_monitor/**/*.py`, `tools/*.py`, `tests/**/*.py` alanlarında tetiklenir. Kullanıcı python-standards, mimari, provider, desktop, config, identity, contract, testing, performance veya benzer bakım işi istediğinde otomatik uygulanmalıdır. Bu skill Codex merkezli repo içi çalışma düzenini zorlar; kurallar izlenmezse KDE ve GNOME yüzeyleri arasında contract drift, stale usage, secret sızıntısı veya health gate kırığı oluşur. Bu skill yalnız ai_usage_monitor için yazılmıştır; proje dışı generic öneri üretmez.
    ---

    # Python Standards

    > Okuyucu maliyetini düşüren en iyi yol, bu repo için doğru sınırları her değişiklikte aynı şekilde korumaktır.

    ## Activation

    This skill activates when:
    - ``core/ai_usage_monitor/**/*.py`, `tools/*.py`, `tests/**/*.py`` altında dosya okunuyor, düzenleniyor veya gözden geçiriliyorsa
    - Kullanıcı python standards, ilgili bounded context veya komşu alanları anıyorsa
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

    ### Rule 1: Mypy uyumlu imza yaz

**Rule**: Yeni public fonksiyonlar açık dönüş tipi taşımalıdır.

**Rationale**: Core contract’larda sessiz Any sızıntısını engeller.

**Correct** ✅:
```python
# Good: project-specific boundary preserved
def example_ok() -> str:
    return "python-standards"
```

**Incorrect** ❌:
```python
# Bad: boundary and intent are unclear
def example_bad():
    return None
# -> Consequence: typed contract ve bakım izi zayıflar.
```
### Rule 2: Dataclass ve typed model tercih et

**Rule**: Yapısal veri tuple veya gevşek dict ile taşınmaz.

**Rationale**: Provider ve VM katmanında alan karışıklığını azaltır.

**Correct** ✅:
```python
# Good: project-specific boundary preserved
def example_ok() -> str:
    return "python-standards"
```

**Incorrect** ❌:
```python
# Bad: boundary and intent are unclear
def example_bad():
    return None
# -> Consequence: typed contract ve bakım izi zayıflar.
```
### Rule 3: Boundary dışında çıplak exception yayma

**Rule**: Boundary’de normalize edip güvenli hata alanlarına çevir.

**Rationale**: UI ve CLI tarafında tutarsız hata şekillerini engeller.

**Correct** ✅:
```python
# Good: project-specific boundary preserved
def example_ok() -> str:
    return "python-standards"
```

**Incorrect** ❌:
```python
# Bad: boundary and intent are unclear
def example_bad():
    return None
# -> Consequence: typed contract ve bakım izi zayıflar.
```
### Rule 4: Path ve env erişimini lokalize et

**Rule**: `Path.home()` ve env okumaları küçük helper sınırlarında kalır.

**Rationale**: Test izolasyonunu ve runtime determinism’i korur.

**Correct** ✅:
```python
# Good: project-specific boundary preserved
def example_ok() -> str:
    return "python-standards"
```

**Incorrect** ❌:
```python
# Bad: boundary and intent are unclear
def example_bad():
    return None
# -> Consequence: typed contract ve bakım izi zayıflar.
```
### Rule 5: Ruff canonical stildir

**Rule**: Format ve lint için ek Python style sapması yaratma.

**Rationale**: Kod tabanı boyunca okuma maliyetini sabit tutar.

**Correct** ✅:
```python
# Good: project-specific boundary preserved
def example_ok() -> str:
    return "python-standards"
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
    from pathlib import Path
from typing import Any

def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding='utf-8') as handle:
        return json.load(handle)
    ```

    **Variations**:
    - Test variation: aynı boundary için küçük regression test ekle.
    - Desktop variation: render katmanı yalnız normalize payload tüketsin.

    ## Anti-Patterns

    ### 🔴 Critical Anti-Pattern
    **Severity**: CRITICAL — merge bloklanır
    **The temptation**: Sorunu en yakın katmanda hızlıca yamamak.
    **The danger**: Provider veya VM builder içinde tiplenmemiş dict zinciri kurmak mypy debt ve yanlış alan adlarını gizler.
    **The fix**: Canonical boundary’ye geri taşı ve regression test ekle.

    ```python
    def load_json(path):
    return json.load(open(path))
# -> no types, leaked file handle
    ```

    ## Performance Budgets

    | Metric | Target | Hard Limit | How to Measure |
    |--------|--------|------------|----------------|
    | Reviewable diff size | <= 250 LOC net | 500 LOC net | `git diff --stat` |
    | Skill-domain unit test runtime | < 5s | 15s | `pytest -q` hedefli set |
    | Health gate after domain change | 0 failed | 0 failed | `make health-ci PYTHON=python` |

    ## Security Checklist

    - [ ] JSON, cookie ve auth dosyası okuyan her helper path traversal değil repo-controlled path ile çalışmalıdır.
    - [ ] Değişiklik proje dışı path üretmiyor; yalnız bu repo altında kalıyor.
    - [ ] Kullanıcıya gösterilen metin secret, token veya local auth path sızdırmıyor.
    - [ ] Test fixture’ları sahte secret kullanıyor; gerçek kullanıcı verisi yok.
    - [ ] Review notunda doğrulama komutları açıkça yazıldı.

    ## Error Scenarios

    | Scenario | Detection | Recovery | User Impact | Severity |
    |----------|-----------|----------|-------------|----------|
    | Typed field yerine Any sızıyor | mypy veya contract testleri hata verir | İmza daralt ve payload modelini typed yardımcıya taşı | Refactor güveni düşer | Medium |
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
    | Depends on | `project-architecture` | Bu skill aynı bounded context kararlarını devralır |
    | Referenced by | `testing-strategy` | Domain davranışı regression testlerle kilitlenir |
    | Shares decision | `project-architecture` | Klasör sınırı ve contract ownership tek yerden gelir |

    ## Pre-Commit Checklist

    - [ ] Tüm core rules uygulandı
    - [ ] Domain-specific anti-pattern yok
    - [ ] Hedefli testler geçti
    - [ ] `make health-ci PYTHON=python` sonucu temiz veya bilinçli doğrulandı
    - [ ] `tasks/todo.md` review bölümü güncellendi
    - [ ] Gerekliyse `tasks/lessons.md` güncellendi
