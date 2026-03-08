# Contributing

## Quick Onboarding

```bash
make setup
```

Bu komut şunları yapar:

- `.venv` oluşturur (yoksa)
- Python dev bağımlılıklarını kurar
- Node bağımlılıklarını kurar (`npm ci`)
- `pre-commit` hook’unu aktive eder

## Günlük Komutlar

```bash
make format   # Python format uygular
make lint     # hızlı kalite kapıları
make typecheck # core Python için gerçek static type check (mypy)
make check    # full quality gates + pytest
make test     # sadece test
```

Eşdeğer npm komutları:

```bash
npm run format
npm run lint
npm run typecheck
npm run check
npm run test
```

## Git Hook

Kurulum:

```bash
make hooks-install
```

Manuel tüm dosyaları çalıştırma:

```bash
make hooks-run
```

## Kodlama Kuralları (Kısa)

1. Renderer purity
- KDE/GNOME renderer katmanında iş kuralı yazma.
- Renderer sadece `layout`, `style/theme binding`, `visibility binding`, `action dispatch`, `input behavior` yapar.

2. Component boundaries
- Büyük UI dosyalarını sorumluluğa göre böl.
- Tek bileşen içinde hem data policy hem render üretme.

3. Provider/account/source state model
- Account/source çözümü ve identity kararları sadece core’da üretilir.
- Renderer sadece core’dan gelen canonical alanları tüketir.

4. File size discipline
- Helper: ~50-120 satır hedefi.
- UI component: ~80-200 satır hedefi.
- Orchestration dosyası 250+ satır ise bölme planı aç.

5. No duplicated presentation logic
- Aynı metin/policy/fallback kuralını KDE ve GNOME’da ayrı ayrı yazma.
- Popup/settings presentation semantiği core `presentation` katmanında tek kaynaktan gelmeli.

## PR Beklentisi

- Davranış değişikliği varsa test ekle.
- `make health-ci` ve `make typecheck` yeşil olmadan PR açma.
- Yeni kod, mevcut health guard’ları bypass etmemeli.

## Enforced Quality Gates (CI)

CI aşağıdaki kapıları zorunlu uygular:

- `python-syntax`, `js-syntax`, `qml-syntax`, `shellcheck`
- `ruff-lint`, `ruff-format`
- `gjs-lint`
- `renderer-purity`
- `debt-guardrails`
- `size-complexity-warnings` (CI’da warning de fail olur)
- `file-budgets`, `function-budgets`
- `gnome-lifecycle-contract`, `kde-lifecycle-contract`
- `mypy`, `pytest`

Yerel CI eşdeğeri:

```bash
make health-ci
```

## Debt Prevention Rules (Hard)

Bu repo’da aşağıdakiler yasak:

1. Yeni baseline lock eklemek (`FILE_SIZE_BASELINE_REDUCTION_PLAN`, `PYTHON_FUNCTION_COMPLEXITY_BASELINES`).
2. `mypy.ini` içinde `ignore_errors = True` override eklemek.
3. Renderer içinde business/presentation policy metni üretmek.

Yeni debt oluştuğunda yaklaşım:

1. Önce split/refactor ile debt’i gerçek olarak düşür.
2. Sonra `make health-ci`, `make typecheck`, ilgili testleri çalıştır.
3. Baseline lock ile alarm susturma yapma.

## Responsibility Boundaries

1. Shared core + two renderers:
- Core: provider/source/account/identity/presentation policy.
- KDE/GNOME: layout + render + dispatch + input behavior.

2. Renderer purity:
- Renderer sadece canonical payload alanlarını tüketir.
- Reset/pace/source/fallback/visibility policy core’da üretilir.

3. Component/file discipline:
- Helper: 50-120 satır.
- UI component: 80-200 satır.
- Orchestrator >250 satır veya büyük fonksiyon alarmdır, split edilmelidir.
