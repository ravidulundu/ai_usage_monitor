---
    name: git-workflow
    description: |
      Git Workflow skilli ai_usage_monitor içindeki `git diff`, PR hazırlığı, release öncesi doğrulama alanlarında tetiklenir. Kullanıcı git-workflow, mimari, provider, desktop, config, identity, contract, testing, performance veya benzer bakım işi istediğinde otomatik uygulanmalıdır. Bu skill Codex merkezli repo içi çalışma düzenini zorlar; kurallar izlenmezse KDE ve GNOME yüzeyleri arasında contract drift, stale usage, secret sızıntısı veya health gate kırığı oluşur. Bu skill yalnız ai_usage_monitor için yazılmıştır; proje dışı generic öneri üretmez.
    ---

    # Git Workflow

    > Okuyucu maliyetini düşüren en iyi yol, bu repo için doğru sınırları her değişiklikte aynı şekilde korumaktır.

    ## Activation

    This skill activates when:
    - ``git diff`, PR hazırlığı, release öncesi doğrulama` altında dosya okunuyor, düzenleniyor veya gözden geçiriliyorsa
    - Kullanıcı git workflow, ilgili bounded context veya komşu alanları anıyorsa
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

    ### Rule 1: Commit öncesi ilgili gate’i çalıştır

**Rule**: En az hedefli pytest + gerekirse health gate olmadan commit atma.

**Rationale**: Kırık durumun history’ye girmesini önler.

**Correct** ✅:
```python
# Good: project-specific boundary preserved
def example_ok() -> str:
    return "git-workflow"
```

**Incorrect** ❌:
```python
# Bad: boundary and intent are unclear
def example_bad():
    return None
# -> Consequence: typed contract ve bakım izi zayıflar.
```
### Rule 2: Unrelated change revert etme

**Rule**: Başkasının dirty worktree değişikliğine dokunma.

**Rationale**: İşbirliği riskini azaltır.

**Correct** ✅:
```python
# Good: project-specific boundary preserved
def example_ok() -> str:
    return "git-workflow"
```

**Incorrect** ❌:
```python
# Bad: boundary and intent are unclear
def example_bad():
    return None
# -> Consequence: typed contract ve bakım izi zayıflar.
```
### Rule 3: Commit mesajı kapsamı anlatsın

**Rule**: Özellikle provider/source/identity gibi hassas alanlarda neden net olmalı.

**Rationale**: Tarihçe taranabilir olur.

**Correct** ✅:
```python
# Good: project-specific boundary preserved
def example_ok() -> str:
    return "git-workflow"
```

**Incorrect** ❌:
```python
# Bad: boundary and intent are unclear
def example_bad():
    return None
# -> Consequence: typed contract ve bakım izi zayıflar.
```
### Rule 4: Interactive git kaçın

**Rule**: Non-interactive komutlar ve açık diff incelemesi tercih et.

**Rationale**: Araç kaynaklı hata riskini düşürür.

**Correct** ✅:
```python
# Good: project-specific boundary preserved
def example_ok() -> str:
    return "git-workflow"
```

**Incorrect** ❌:
```python
# Bad: boundary and intent are unclear
def example_bad():
    return None
# -> Consequence: typed contract ve bakım izi zayıflar.
```
### Rule 5: Büyük iş fazlara bölünür

**Rule**: Tek dev commit ile çoklu bounded context karıştırılmaz.

**Rationale**: Bisect ve review kolaylaşır.

**Correct** ✅:
```python
# Good: project-specific boundary preserved
def example_ok() -> str:
    return "git-workflow"
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
    git status --short
git diff -- core/ai_usage_monitor/presentation/popup_vm_source_presentation.py
PYTHONPATH=. ./.venv/bin/python -m pytest -q tests/test_popup_vm.py
    ```

    **Variations**:
    - Test variation: aynı boundary için küçük regression test ekle.
    - Desktop variation: render katmanı yalnız normalize payload tüketsin.

    ## Anti-Patterns

    ### 🔴 Critical Anti-Pattern
    **Severity**: CRITICAL — merge bloklanır
    **The temptation**: Sorunu en yakın katmanda hızlıca yamamak.
    **The danger**: Birden fazla contexti tek doğrulamasız committe toplamak.
    **The fix**: Canonical boundary’ye geri taşı ve regression test ekle.

    ```python
    git add -A && git commit -m 'fix'
# -> no scope, no verification
    ```

    ## Performance Budgets

    | Metric | Target | Hard Limit | How to Measure |
    |--------|--------|------------|----------------|
    | Reviewable diff size | <= 250 LOC net | 500 LOC net | `git diff --stat` |
    | Skill-domain unit test runtime | < 5s | 15s | `pytest -q` hedefli set |
    | Health gate after domain change | 0 failed | 0 failed | `make health-ci PYTHON=python` |

    ## Security Checklist

    - [ ] Commit öncesi diff içinde secret ve local path sızıntısı taranmalıdır.
    - [ ] Değişiklik proje dışı path üretmiyor; yalnız bu repo altında kalıyor.
    - [ ] Kullanıcıya gösterilen metin secret, token veya local auth path sızdırmıyor.
    - [ ] Test fixture’ları sahte secret kullanıyor; gerçek kullanıcı verisi yok.
    - [ ] Review notunda doğrulama komutları açıkça yazıldı.

    ## Error Scenarios

    | Scenario | Detection | Recovery | User Impact | Severity |
    |----------|-----------|----------|-------------|----------|
    | Yanlış dosya stage edildi | git diff --cached review | İstenmeyen hunk’ı unstaged et | Yanlış değişiklik merge olabilir | Medium |
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
    | Depends on | `project-architecture, documentation-standards` | Bu skill aynı bounded context kararlarını devralır |
    | Referenced by | `testing-strategy` | Domain davranışı regression testlerle kilitlenir |
    | Shares decision | `project-architecture` | Klasör sınırı ve contract ownership tek yerden gelir |

    ## Pre-Commit Checklist

    - [ ] Tüm core rules uygulandı
    - [ ] Domain-specific anti-pattern yok
    - [ ] Hedefli testler geçti
    - [ ] `make health-ci PYTHON=python` sonucu temiz veya bilinçli doğrulandı
    - [ ] `tasks/todo.md` review bölümü güncellendi
    - [ ] Gerekliyse `tasks/lessons.md` güncellendi
