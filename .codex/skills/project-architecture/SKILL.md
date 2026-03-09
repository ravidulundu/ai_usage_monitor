---
    name: project-architecture
    description: |
      Project Architecture skilli ai_usage_monitor içindeki `core/ai_usage_monitor/`, `com.aiusagemonitor/contents/`, `gnome-extension/aiusagemonitor@aimonitor/`, `docs/`, `tasks/` alanlarında tetiklenir. Kullanıcı project-architecture, mimari, provider, desktop, config, identity, contract, testing, performance veya benzer bakım işi istediğinde otomatik uygulanmalıdır. Bu skill Codex merkezli repo içi çalışma düzenini zorlar; kurallar izlenmezse KDE ve GNOME yüzeyleri arasında contract drift, stale usage, secret sızıntısı veya health gate kırığı oluşur. Bu skill yalnız ai_usage_monitor için yazılmıştır; proje dışı generic öneri üretmez.
    ---

    # Project Architecture

    > Okuyucu maliyetini düşüren en iyi yol, bu repo için doğru sınırları her değişiklikte aynı şekilde korumaktır.

    ## Activation

    This skill activates when:
    - ``core/ai_usage_monitor/`, `com.aiusagemonitor/contents/`, `gnome-extension/aiusagemonitor@aimonitor/`, `docs/`, `tasks/`` altında dosya okunuyor, düzenleniyor veya gözden geçiriliyorsa
    - Kullanıcı project architecture, ilgili bounded context veya komşu alanları anıyorsa
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

    ### Rule 1: Katman sınırını koru

**Rule**: Python core iş kuralını üretir, KDE ve GNOME yalnız render eder.

**Rationale**: Sessiz davranış drift’ini ve çift bakım yükünü engeller.

**Correct** ✅:
```python
# Good: project-specific boundary preserved
def example_ok() -> str:
    return "project-architecture"
```

**Incorrect** ❌:
```python
# Bad: boundary and intent are unclear
def example_bad():
    return None
# -> Consequence: typed contract ve bakım izi zayıflar.
```
### Rule 2: Contract üretimini core içinde tut

**Rule**: `popup-vm`, `config-ui` ve `sourceModel` şekilleri renderer içinde yeniden kurulmaz.

**Rationale**: Aynı alanın iki yerde farklı yorumlanmasını engeller.

**Correct** ✅:
```python
# Good: project-specific boundary preserved
def example_ok() -> str:
    return "project-architecture"
```

**Incorrect** ❌:
```python
# Bad: boundary and intent are unclear
def example_bad():
    return None
# -> Consequence: typed contract ve bakım izi zayıflar.
```
### Rule 3: Archived provider kodunu aktif runtime ile karıştırma

**Rule**: `core/ai_usage_monitor/archived_providers/` yalnız legacy/test alanıdır.

**Rationale**: Dormant kodun tekrar aktif yüzeye sızmasını engeller.

**Correct** ✅:
```python
# Good: project-specific boundary preserved
def example_ok() -> str:
    return "project-architecture"
```

**Incorrect** ❌:
```python
# Bad: boundary and intent are unclear
def example_bad():
    return None
# -> Consequence: typed contract ve bakım izi zayıflar.
```
### Rule 4: Plan ve review kaydı zorunludur

**Rule**: Önemsiz olmayan her iş `tasks/todo.md` içinde planlanır ve review bölümüyle kapanır.

**Rationale**: Karar hafızasını ve regresyon izlenebilirliğini korur.

**Correct** ✅:
```python
# Good: project-specific boundary preserved
def example_ok() -> str:
    return "project-architecture"
```

**Incorrect** ❌:
```python
# Bad: boundary and intent are unclear
def example_bad():
    return None
# -> Consequence: typed contract ve bakım izi zayıflar.
```
### Rule 5: Yeni bounded context açmadan önce mevcutu genişlet

**Rule**: Aynı kavram için ikinci helper çöplüğü yaratılmaz.

**Rationale**: Kavramsal parçalanmayı ve gizli coupling’i azaltır.

**Correct** ✅:
```python
# Good: project-specific boundary preserved
def example_ok() -> str:
    return "project-architecture"
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
    from core.ai_usage_monitor.collector import collect_popup_vm_payload

def build_popup_json(preferred_provider_id: str | None = None) -> dict:
    return collect_popup_vm_payload(preferred_provider_id=preferred_provider_id, force=False)
    ```

    **Variations**:
    - Test variation: aynı boundary için küçük regression test ekle.
    - Desktop variation: render katmanı yalnız normalize payload tüketsin.

    ## Anti-Patterns

    ### 🔴 Critical Anti-Pattern
    **Severity**: CRITICAL — merge bloklanır
    **The temptation**: Sorunu en yakın katmanda hızlıca yamamak.
    **The danger**: KDE veya GNOME tarafında core dışı yeni payload alanları üretmek iki UI arasında sessiz drift yaratır.
    **The fix**: Canonical boundary’ye geri taşı ve regression test ekle.

    ```python
    # GNOME renderer içinde yeni payload üretmek YASAK
payload = {"providers": [], "activeTab": "codex"}
    ```

    ## Performance Budgets

    | Metric | Target | Hard Limit | How to Measure |
    |--------|--------|------------|----------------|
    | Reviewable diff size | <= 250 LOC net | 500 LOC net | `git diff --stat` |
    | Skill-domain unit test runtime | < 5s | 15s | `pytest -q` hedefli set |
    | Health gate after domain change | 0 failed | 0 failed | `make health-ci PYTHON=python` |

    ## Security Checklist

    - [ ] Skill veya helper üretirken yalnız bu repo altında çalış; ev dizini veya başka repo path’lerinden örnek kopyalama yapma.
    - [ ] Değişiklik proje dışı path üretmiyor; yalnız bu repo altında kalıyor.
    - [ ] Kullanıcıya gösterilen metin secret, token veya local auth path sızdırmıyor.
    - [ ] Test fixture’ları sahte secret kullanıyor; gerçek kullanıcı verisi yok.
    - [ ] Review notunda doğrulama komutları açıkça yazıldı.

    ## Error Scenarios

    | Scenario | Detection | Recovery | User Impact | Severity |
    |----------|-----------|----------|-------------|----------|
    | Renderer beklediği alanı bulamıyor | popup VM contract testleri kırılır | Core contract güncellemesini geri al veya testleri kasıtlı değişiklikle birlikte güncelle | UI boş kart veya yanlış metrik gösterir | High |
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
    | Depends on | `none` | Bu skill aynı bounded context kararlarını devralır |
    | Referenced by | `testing-strategy` | Domain davranışı regression testlerle kilitlenir |
    | Shares decision | `project-architecture` | Klasör sınırı ve contract ownership tek yerden gelir |

    ## Pre-Commit Checklist

    - [ ] Tüm core rules uygulandı
    - [ ] Domain-specific anti-pattern yok
    - [ ] Hedefli testler geçti
    - [ ] `make health-ci PYTHON=python` sonucu temiz veya bilinçli doğrulandı
    - [ ] `tasks/todo.md` review bölümü güncellendi
    - [ ] Gerekliyse `tasks/lessons.md` güncellendi
