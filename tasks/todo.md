# TODO

## 2026-03-09 - Architecture and Contract Audit

- [x] `project-architecture`, `presentation-contracts`, `identity-state-management` skill kurallarına göre audit kapsamını sabitle
- [x] Canonical popup/identity contract üretimini core katmanda incele
- [x] KDE ve GNOME renderer tüketimini canonical contract ile karşılaştır
- [x] Identity snapshot/apply/invalidation akışında stale veya drift risklerini doğrula
- [x] Bulguları severity + dosya:line + risk + kısa düzeltme ile raporla
- [x] Review bölümüne incelenen kanıt yollarını ve kullanılan komutları yaz

### Review

- İncelenen ana kanıt yolları:
  - `core/ai_usage_monitor/presentation/*.py`
  - `core/ai_usage_monitor/identity_*.py`
  - `core/ai_usage_monitor/collector.py`
  - `core/ai_usage_monitor/collector_helpers.py`
  - `core/ai_usage_monitor/providers/codex.py`
  - `com.aiusagemonitor/contents/ui/*.qml`
  - `com.aiusagemonitor/contents/ui/*.js`
  - `gnome-extension/aiusagemonitor@aimonitor/*.js`
  - `tools/project_health_contracts.py`
  - `tests/test_popup_vm.py`
  - `tests/test_identity_multi_account.py`
  - `tests/test_settings_presentation_matrix.py`
- Kullanılan tarama komutları:
  - `rg -n "popup_vm|sourcePresentation|settingsPresentation|identity|fingerprint|switchingState|resolvedSource|preferredSource|unavailableReason" core/ai_usage_monitor com.aiusagemonitor/contents gnome-extension/aiusagemonitor@aimonitor tests`
  - `rg -n "Source switched|Refreshing usage|statusTags|reasonText|identityFingerprint|stateIdentityKey|sourcePresentation" com.aiusagemonitor/contents/ui gnome-extension/aiusagemonitor@aimonitor`
  - `rg -n "accountStateKey|providerStateKey|stateIdentityKey|activeIdentity|activeIdentityFingerprint" core/ai_usage_monitor com.aiusagemonitor/contents/ui gnome-extension/aiusagemonitor@aimonitor tests`
  - `rg -n "settingsPresentation|sourceReasonLabel|sourceStatusLabel|availabilityLabel|strategyLabel" core/ai_usage_monitor tests`
  - `rg --files com.aiusagemonitor/contents gnome-extension/aiusagemonitor@aimonitor | rg "(qml|js)$"`

## 2026-03-09 - Security/Data Validation/Dependency Audit

- [x] `project-architecture`, `security-hardening`, `data-validation`, `dependency-management` ve `documentation-standards` skill kurallarını oku
- [x] `core/ai_usage_monitor/` ve ilgili toolchain dosyalarında security-hardening odaklı tarama yap
- [x] `config`, parser ve provider boundary'lerinde data-validation odaklı tarama yap
- [x] `requirements-dev.txt`, `package.json`, `.pre-commit-config.yaml` ve script çağrılarında dependency-management odaklı tarama yap
- [x] Kanıtlı bulguları severity + dosya:line + risk + remediation ile raporla
- [x] Review bölümüne kullanılan doğrulama komutlarını ve audit kapsamını yaz

### Review

- Audit kapsamı `security-hardening`, `data-validation`, `dependency-management` ve bunları bağlayan config/provider/toolchain sınırlarıyla sınırlı tutuldu.
- Kanıt toplamak için kullanılan ana komutlar:
  - `rg -n "shell=True|subprocess\\.|json\\.loads|token|cookie|secret|Authorization|api[_-]?key" core tools com.aiusagemonitor gnome-extension tests`
  - `nl -ba core/ai_usage_monitor/{browser_cookies.py,config.py,cli.py,runtime_cache.py,shared/oauth.py,providers/minimax.py,providers/openrouter.py}`
  - `nl -ba com.aiusagemonitor/contents/ui/{configGeneral.qml,ConfigBackend.js}`
  - `nl -ba gnome-extension/aiusagemonitor@aimonitor/{prefs.js,prefsBackend.js}`
  - `python - <<'PY' ... normalize_config(...) ... PY` ile unknown field preservation ve non-object normalize davranışı doğrulandı
- Çalıştırılmış davranış kanıtı:
  - `normalize_config({"providers":[{"id":"copilot","enabled":true,"source":"api","unexpected":{"nested":1}}]})` sonucu `unexpected={'nested': 1}` değerini koruyor.
  - `normalize_config([])` sonucu default config'e (`refreshInterval=60`) düşüyor; bu `config-save-json` boundary'sinde non-object payload'un sessiz default reset'e dönüşebildiğini doğruluyor.

## 2026-03-09 - Skill-Driven Project Audit

- [x] `AGENTS.md` içindeki yerel skill aktivasyon haritasına göre audit kapsamını kilitle
- [x] Mimari/contract/identity alanlarını `project-architecture`, `presentation-contracts`, `identity-state-management` perspektifiyle tara
- [x] Güvenlik/doğrulama alanlarını `security-hardening`, `data-validation`, `dependency-management` perspektifiyle tara
- [x] Test/perf/observability alanlarını `testing-strategy`, `performance-optimization`, `observability` perspektifiyle tara
- [x] Bulguları risk seviyesi + dosya referansı + önerilen aksiyon ile raporla
- [x] Review bölümüne doğrulama komutları ve audit özetini yaz

### Review

- Audit üç paralel alt-ajan (mimari/contract, security/validation, test/perf/observability) + yerel kanıt okuması ile birleştirildi.
- Ana kanıt dosyaları:
  - `core/ai_usage_monitor/runtime_cache.py`
  - `core/ai_usage_monitor/browser_cookies.py`
  - `core/ai_usage_monitor/config.py`
  - `core/ai_usage_monitor/cli.py`
  - `core/ai_usage_monitor/providers/codex.py`
  - `core/ai_usage_monitor/provider_freshness.py`
  - `core/ai_usage_monitor/identity_snapshot.py`
  - `core/ai_usage_monitor/status.py`
  - `com.aiusagemonitor/contents/ui/main.qml`
  - `gnome-extension/aiusagemonitor@aimonitor/indicatorLifecycleMixin.js`
- Kullanılan ana doğrulama/tarama komutları:
  - `rg --files ... | xargs wc -l | sort -nr | head -n 25`
  - `python AST taraması` ile 40+ satır fonksiyon envanteri
  - `nl -ba ...` ile dosya:line doğrulama
  - alt-ajan tarafından çalıştırılan hedefli suite: `./.venv/bin/python -m pytest -q tests/test_local_usage.py tests/test_browser_cookies.py tests/test_status.py tests/test_collector.py tests/test_collector_cache_invalidation.py tests/test_project_health_contracts.py` (`48 passed`)

## 2026-03-09 - Project Bootstrapper Brownfield Analysis

- [x] Bootstrap giriş dokümanını ve skill referanslarını oku
- [x] README, boundary dokümanı ve giriş noktalarından brownfield mimariyi doğrula
- [x] Ana bounded context'leri, giriş noktalarını ve kritik veri akışlarını çıkar
- [x] Skill bootstrap için önemli brownfield risklerini netleştir
- [x] Kısa ve somut mimari özetini kullanıcıya sun

### Review

- Repo üç ana katmana ayrılıyor: shared Python core, KDE plasmoid, GNOME extension.
- Gerçek giriş yüzeyleri `core/ai_usage_monitor/cli.py`, KDE wrapper `com.aiusagemonitor/contents/scripts/fetch_all_usage.py`, GNOME subprocess çağrıları ve opsiyonel `bin/ai-usage-monitor-state`.
- Kritik runtime zinciri: config -> registry/source strategy -> provider collectors -> identity store invalidation/refetch -> normalized `AppState` -> popup/settings VM -> desktop render.
- Bootstrap için en önemli brownfield riskleri: UI'ların shared JSON contract'a sıkı bağlı olması, provider/source/identity semantiğinin dağınık ama hassas olması, ve health gate'lerin mimari kararları fiilen kilitlemesi.
- Etkin stack doğrulaması: Python 3.11 baseline, KDE Plasma/QML 6, GNOME Shell JS/GJS, pytest+mypy+Ruff+ESLint+pre-commit kalite kapıları.
- Resmi registry üzerinden doğrulanan güncel araç sürümleri: `pytest 9.0.2`, `mypy 1.19.1`, `ruff 0.15.5`, `eslint 10.0.3`.

## 2026-03-09 - Project Bootstrapper Generation

- [x] Codex merkezli proje içi skill hedefini `.codex/skills/` olarak sabitle
- [x] Onaylanan skill map için proje-özgü skill suite üret
- [x] `_bootstrap-manifest.json` oluştur
- [x] `AGENTS.md` içine proje-scope kilidi ekle
- [x] Bootstrap validator ile sonucu doğrula

### Review

- Skill suite proje içine `.codex/skills/` altında üretildi; `.claude/` varsayımı kaldırıldı.
- Üretilen 16 skill:
  - `project-architecture`
  - `python-standards`
  - `security-hardening`
  - `error-handling`
  - `data-validation`
  - `testing-strategy`
  - `performance-optimization`
  - `dependency-management`
  - `documentation-standards`
  - `git-workflow`
  - `desktop-integration-patterns`
  - `provider-patterns`
  - `identity-state-management`
  - `presentation-contracts`
  - `config-and-runtime-state`
  - `observability`
- Manifest [._bootstrap-manifest.json](/home/osmandulundu/projects/personal/ai_usage_monitor/.codex/skills/_bootstrap-manifest.json) altında oluşturuldu.
- [AGENTS.md](/home/osmandulundu/projects/personal/ai_usage_monitor/AGENTS.md) proje-scope kilidi ve Codex-merkezli bootstrap yönlendirmesiyle güncellendi.
- [AGENTS.md](/home/osmandulundu/projects/personal/ai_usage_monitor/AGENTS.md) ayrıca 16 yerel skill için açık aktivasyon haritası ve hangi işte hangi skill zincirinin kullanılacağını içeriyor.
- Doğrulama:
  - `python /home/osmandulundu/.codex/skills/project-bootstrapper/scripts/validate_bootstrap.py .codex/skills` PASS (`16 skills`, `80 rules`, `240 code blocks`, `0 errors`, `0 warnings`)

## 2026-03-09 - CLI Dispatch Decomposition Phase 1

- [x] `main(...)` içindeki mode dispatch zincirini handler map'e indir
- [x] `config-ui` / `popup-vm` / config save path'lerini küçük handler'lara ayır
- [x] Mevcut CLI testleriyle davranışı koru
- [x] Hedefli pytest + mypy + `make health-ci PYTHON=python` ile doğrula

### Review

- [cli.py](/home/osmandulundu/projects/personal/ai_usage_monitor/core/ai_usage_monitor/cli.py) içinde `main(...)` artık yalnız parse + dispatch yapıyor.
- Yeni sınırlar:
  - `parse_mode(...)`
  - `_handle_legacy(...)`
  - `_handle_state(...)`
  - `_handle_popup_vm(...)`
  - `_handle_config_*` handler'ları
  - `COMMAND_HANDLERS`
- `test_cli_config.py` üzerinden mevcut CLI davranışı korundu.

## 2026-03-09 - Maintainability Refactor Phase 2

- [x] `providers/gemini.py` içindeki orchestration / retry / mapping akışını küçük helper sınırlarına ayır
- [x] `providers/opencode.py` içindeki source resolution / web fetch / fallback akışını helper sınırlarına ayır
- [x] `config.py` içindeki schema/defaults / normalize / persistence sınırlarını netleştir
- [x] `browser_cookies.py` içinde browser-query tekrarını backend tanımıyla sadeleştir
- [x] `identity_apply.py` içindeki transition hesaplama / apply / persist akışını ayrıştır
- [x] `providers/kilo.py` ve `providers/minimax.py` için en yüksek kaldıraçlı readability refactor'larını uygula
- [x] Her fazı hedefli pytest + mypy ile kilitle; finalde `make health-ci PYTHON=python` çalıştır

### Review

- Refactor hedefi davranış değiştirmek değil, okuyucu maliyetini düşürmek.
- Öncelik sırası:
  - `gemini.py`
  - `opencode.py`
  - `config.py`
  - `browser_cookies.py`
  - `identity_apply.py`
  - `kilo.py` / `minimax.py`
- Uygulanan ana sınırlar:
  - [gemini.py](/home/osmandulundu/projects/personal/ai_usage_monitor/core/ai_usage_monitor/providers/gemini.py) içinde credential-load / retry-refresh / success-error builder adımları ayrıldı.
  - [opencode.py](/home/osmandulundu/projects/personal/ai_usage_monitor/core/ai_usage_monitor/providers/opencode.py) içinde local fallback, web collect ve error mapping sınırları netleştirildi.
  - [config.py](/home/osmandulundu/projects/personal/ai_usage_monitor/core/ai_usage_monitor/config.py) içinde registry/default scalar settings ve normalize akışı küçük helper bloklara ayrıldı.
  - [browser_cookies.py](/home/osmandulundu/projects/personal/ai_usage_monitor/core/ai_usage_monitor/browser_cookies.py) içinde ortak `CookieBackend` tabanlı query çekirdeği çıkarıldı.
  - [identity_apply.py](/home/osmandulundu/projects/personal/ai_usage_monitor/core/ai_usage_monitor/identity_apply.py) içinde transition hesaplama, provider apply ve persist adımları ayrıldı.
  - [kilo.py](/home/osmandulundu/projects/personal/ai_usage_monitor/core/ai_usage_monitor/providers/kilo.py) ve [minimax.py](/home/osmandulundu/projects/personal/ai_usage_monitor/core/ai_usage_monitor/providers/minimax.py) top-level collect akışları success/error helper sınırlarıyla sadeleştirildi.
- Yeni/sertleşen regresyon testleri:
  - [test_gemini_provider.py](/home/osmandulundu/projects/personal/ai_usage_monitor/tests/test_gemini_provider.py)
  - [test_opencode_provider.py](/home/osmandulundu/projects/personal/ai_usage_monitor/tests/test_opencode_provider.py)
  - [test_kilo_provider.py](/home/osmandulundu/projects/personal/ai_usage_monitor/tests/test_kilo_provider.py)
  - [test_minimax_provider.py](/home/osmandulundu/projects/personal/ai_usage_monitor/tests/test_minimax_provider.py)
- Doğrulama:
  - `PYTHONPATH=. ./.venv/bin/python -m pytest -q tests/test_gemini_provider.py tests/test_opencode_provider.py tests/test_config.py tests/test_browser_cookies.py tests/test_identity_multi_account.py tests/test_kilo_provider.py tests/test_minimax_provider.py tests/test_claude_provider.py tests/test_vertexai_provider.py tests/test_local_usage.py tests/test_cli_config.py tests/test_collector.py tests/test_collector_cache_invalidation.py tests/test_settings_presentation_matrix.py tests/test_source_strategy.py tests/test_popup_vm.py` PASS (`103 passed, 3 subtests passed`)
  - `PYTHONPATH=. ./.venv/bin/python -m mypy --config-file mypy.ini core/ai_usage_monitor` PASS
  - `make health-ci PYTHON=python` PASS (`17 passed/warned, 0 failed, 0 warnings`)

## 2026-03-09 - Stable Fallback Metrics Visibility Fix

- [x] `fallbackActive` durumunda stabil fallback ile geçici source-switch refresh state'ini ayır
- [x] Stable fallback senaryosunda session/weekly metric görünürlüğünü testle kilitle
- [x] Presentation mypy + `make health-ci PYTHON=python` ile doğrula

### Review

- [popup_vm_source_presentation.py](/home/osmandulundu/projects/personal/ai_usage_monitor/core/ai_usage_monitor/presentation/popup_vm_source_presentation.py) artık `source_switched` unavailable reason'ını sadece gerçek source-refresh geçişinde üretir.
- Stabil fallback (`preferredSource != resolvedSource` ama identity refresh yok) artık metriği saklamıyor; mevcut resolved source metric'leri görünür kalıyor.
- Yeni regresyon testi [test_popup_vm.py](/home/osmandulundu/projects/personal/ai_usage_monitor/tests/test_popup_vm.py) içinde stable fallback senaryosunu kilitliyor.
- Doğrulama:
  - `PYTHONPATH=. ./.venv/bin/python -m pytest -q tests/test_popup_vm.py tests/test_popup_vm_state_matrix.py tests/test_presentation_helper_modules.py` PASS (`29 passed, 8 subtests passed`)
  - `PYTHONPATH=. ./.venv/bin/python -m mypy --config-file mypy.ini core/ai_usage_monitor/presentation` PASS
  - `make health-ci PYTHON=python` PASS (`17 passed/warned, 0 failed, 0 warnings`)

## 2026-03-09 - Claude Provider Decomposition Phase 1

- [x] `collect_claude(...)` içindeki credential fetch / request / success / error akışlarını helper'lara ayır
- [x] Identity/extras/incident üretimini ortak helper'lara çıkar
- [x] Missing-credentials ve success davranışını testle kilitle
- [x] Hedefli pytest + mypy + `make health-ci PYTHON=python` ile doğrula

### Review

- [claude.py](/home/osmandulundu/projects/personal/ai_usage_monitor/core/ai_usage_monitor/providers/claude.py) içinde şu sınırlar ayrıldı:
  - `_claude_extras(...)`
  - `_claude_incident()`
  - `_load_claude_credentials()`
  - `_fetch_claude_usage(...)`
  - `_build_claude_legacy(...)`
  - `_claude_success_state(...)`
  - `_claude_error_state(...)`
- Yeni koruma testleri [test_claude_provider.py](/home/osmandulundu/projects/personal/ai_usage_monitor/tests/test_claude_provider.py) içinde credentials yok ve başarı durumlarını kilitliyor.

## 2026-03-09 - Vertex AI Provider Decomposition Phase 1

- [x] `collect_vertexai(...)` içindeki success/error/project-missing akışlarını helper'lara ayır
- [x] Quota filter literal'larını isimlendirilmiş sabitlere çıkar
- [x] Success ve project-missing davranışlarını testle kilitle
- [x] Hedefli pytest + mypy + `make health-ci PYTHON=python` ile doğrula

### Review

- [vertexai.py](/home/osmandulundu/projects/personal/ai_usage_monitor/core/ai_usage_monitor/providers/vertexai.py) içinde şu sınırlar ayrıldı:
  - `USAGE_FILTER` / `LIMIT_FILTER`
  - `_vertex_extras(...)`
  - `_vertex_not_installed()`
  - `_vertex_project_missing(...)`
  - `_fetch_vertex_quota_percent(...)`
  - `_vertex_success_state(...)`
  - `_vertex_error_state(...)`
- Yeni koruma testleri [test_vertexai_provider.py](/home/osmandulundu/projects/personal/ai_usage_monitor/tests/test_vertexai_provider.py) içinde project eksik ve başarı durumlarını kilitliyor.

## 2026-03-09 - Popup VM Presentation Decomposition Phase 1

- [x] `provider_vm(...)` içindeki identity/source/status/link bloklarını helper'lara ayır
- [x] `metric_vm(...)` içindeki loading/value/unavailable dallarını helper'lara ayır
- [x] Mevcut popup VM contract testleriyle davranışı koru
- [x] Hedefli pytest + mypy + `make health-ci PYTHON=python` ile doğrula

### Review

- [popup_vm_provider.py](/home/osmandulundu/projects/personal/ai_usage_monitor/core/ai_usage_monitor/presentation/popup_vm_provider.py) içinde provider payload üretimi şu bloklara ayrıldı:
  - `_provider_identity_fields(...)`
  - `_provider_source_fields(...)`
  - `_provider_status_fields(...)`
  - `_provider_action_fields(...)`
- [popup_vm_metrics_core.py](/home/osmandulundu/projects/personal/ai_usage_monitor/core/ai_usage_monitor/presentation/popup_vm_metrics_core.py) içinde `metric_vm(...)` şu dallara ayrıldı:
  - `_metric_source_text(...)`
  - `_metric_loading_vm(...)`
  - `_metric_value_vm(...)`
  - `_metric_unavailable_text(...)`
- Popup VM contract testleriyle payload anahtarları ve semantik korunmuş durumda.

## 2026-03-09 - Local Usage Decomposition Phase 1

- [x] Claude ve Vertex local usage akışını ortak çekirdeğe indir
- [x] Mevcut cache/fingerprint davranışını koru
- [x] Yeni test ile Vertex filtre davranışını kilitle
- [x] Hedefli pytest + mypy + `make health-ci PYTHON=python` ile doğrula

### Review

- [local_usage.py](/home/osmandulundu/projects/personal/ai_usage_monitor/core/ai_usage_monitor/local_usage.py) içinde Claude ve Vertex için ortak message-usage çekirdeği çıkarıldı:
  - `_claude_usage_roots()`
  - `_existing_roots(...)`
  - `_iter_jsonl_objects(...)`
  - `_message_usage_tokens(...)`
  - `_build_daily_snapshot(...)`
  - `_scan_cached_message_usage(...)`
- Davranış korunarak kopya tarama akışı kaldırıldı; cache/fingerprint mantığı aynı kaldı.
- Yeni koruma testi [test_local_usage.py](/home/osmandulundu/projects/personal/ai_usage_monitor/tests/test_local_usage.py) içinde non-vertex mesajların Vertex toplamına girmediğini kilitliyor.

## 2026-03-09 - Collector Helpers Decomposition Phase 1

- [x] `collect_provider(...)` içindeki attempt/cache/fallback akışını helper'lara ayır
- [x] Metadata/source-model finalization adımını ayrı helper'a çıkar
- [x] Yeni unit test ile attempt sırası ve metadata korumasını kilitle
- [x] Hedefli pytest + mypy + `make health-ci PYTHON=python` ile doğrula

### Review

- [collector_helpers.py](/home/osmandulundu/projects/personal/ai_usage_monitor/core/ai_usage_monitor/collector_helpers.py) içinde şu sınırlar ayrıldı:
  - `configured_source_value(...)`
  - `_attempt_settings(...)`
  - `_collect_attempt_result(...)`
  - `_collect_enabled_provider(...)`
  - `_apply_provider_metadata(...)`
- Dış sözleşme korunarak `collect_provider(...)` daha kısa ve okunabilir hale geldi.
- Yeni koruma testi [test_collector_cache_invalidation.py](/home/osmandulundu/projects/personal/ai_usage_monitor/tests/test_collector_cache_invalidation.py) içinde explicit attempt sırası + metadata/source-model devamlılığını kilitliyor.

## 2026-03-09 - Source Model Decomposition Phase 1 Execution

- [x] Source-model contract testlerini sıkılaştır
- [x] `SourceModelInputs` ve `SourceModelRuntime` yapılarını çıkar
- [x] Settings presentation üretimini ayrı modüle taşı
- [x] Payload assembly'yi ayrı modüle taşı
- [x] Hedefli pytest + mypy + `make health-ci PYTHON=python` ile doğrula

### Review

- `build_provider_source_model(...)` public yüzeyi korunarak iç akış dört parçaya ayrıldı:
  - [common.py](/home/osmandulundu/projects/personal/ai_usage_monitor/core/ai_usage_monitor/sources/common.py)
  - [model_types.py](/home/osmandulundu/projects/personal/ai_usage_monitor/core/ai_usage_monitor/sources/model_types.py)
  - [settings_presentation.py](/home/osmandulundu/projects/personal/ai_usage_monitor/core/ai_usage_monitor/sources/settings_presentation.py)
  - [payloads.py](/home/osmandulundu/projects/personal/ai_usage_monitor/core/ai_usage_monitor/sources/payloads.py)
- Ana facade dosyası [model.py](/home/osmandulundu/projects/personal/ai_usage_monitor/core/ai_usage_monitor/sources/model.py) 832 satırdan 450 satıra indi.
- Contract kilidi olarak `tests/test_settings_presentation_matrix.py`, `tests/test_source_strategy.py` ve `tests/test_popup_vm.py` kullanıldı.

## 2026-03-09 - Source Model Decomposition Phase 1 Plan

- [x] İlk uygulanacak refactor hedefini seç (`sources/model.py`)
- [x] Faz-1 implementasyon planını yaz
- [x] Test ve doğrulama kapılarını plan içine kilitle
- [x] Planı `docs/plans/2026-03-09-source-model-decomposition-phase-1.md` altına kaydet

### Review

- İlk uygulanacak adım olarak `sources/model.py` seçildi; çünkü audit içindeki en büyük dosya ve en yüksek bağlaşım burada.
- Faz-1 bilinçli olarak davranış değiştirmiyor; yalnız iç modülerliği artırıp public `build_provider_source_model(...)` yüzeyini koruyor.
- Plan test-first ilerliyor: `test_settings_presentation_matrix.py`, `test_source_strategy.py`, `test_popup_vm.py` contract kilidi olarak kullanılacak.

## 2026-03-09 - Abstraction Quality & Duplicate Code Audit

- [ ] Üretim kodu envanterini çıkar ve audit kapsamını netleştir (Python core + renderer giriş katmanı)
- [ ] SRP ihlali, util/helper çöplüğü, data clump, abstraction level uyuşmazlığı için hotspot analizi yap
- [ ] Kopya kod ve shared abstraction fırsatlarını dosya/satır bazlı kanıtla
- [ ] Bulguları sürdürülebilirlik etkisi + önerilen ayrıştırma/ortak abstraction ile raporla
- [ ] Review notunu `tasks/todo.md` içine ekle

## 2026-03-08 - Maintainability Audit

- [x] Uzun fonksiyonlar, büyük dosyalar ve derin iç içe geçmeleri çıkar
- [x] Soyutlama kalitesi, bağlaşım/uyum ve tutarlılık bulgularını üretim kodunda topla
- [x] Bulguları refactor örnekleriyle raporla

### Review

- Audit kapsamı: `core/ai_usage_monitor`, `gnome-extension/aiusagemonitor@aimonitor`, `com.aiusagemonitor/contents/ui` (generated ve `node_modules` hariç).
- Öncelikli bulgular:
  - 400+ satır dosyalar: `sources/model.py`, `providers/kilo.py`, `providers/opencode.py`, `providers/minimax.py`, `providers/gemini.py`, `local_usage.py`
  - 40+ satır fonksiyonlarda orchestration + parse + presentation sorumluluklarının birleşmesi
  - Derin iç içe geçme: provider fallback/retry blokları ve popup metric üretimi
  - Boolean flag akışları: `force` / `force_refresh` / `forceRefresh` çağrı zinciri
  - İsimlendirme ve literal yoğunluğu: `legacy` payload adı, fallback/status reason string kodları, tekrarlayan sabitler

## 2026-03-08 - FinOps Sweep Reduction Round 3

- [x] `collect_all()` içinde güvenli provider freshness katmanını ekle
- [x] `claude` ve `vertexai` local usage taramalarını fingerprint cache ile azalt
- [x] Yeni kurulum için pahalı/niş provider default setini daralt
- [x] Regresyon testleri ve kalite kapılarıyla doğrula

### Review

- Bu tur popup-level cache'in ötesine geçip cache miss / force dışı backend sweep maliyetini azaltacak.
- Güvenli kapsam:
  - provider freshness sadece kimliği settings/env ile stabil provider'larda açılacak
  - browser/session tabanlı provider'lar bu turda freshness cache'e alınmayacak
- Hedef:
  - `vertexai`, `copilot`, `openrouter` gibi remote-heavy provider'larda gereksiz tekrar fetch'i azaltmak
  - `claude` / `vertexai` local usage tam dosya taramasını dosya fingerprint cache ile kırpmak
  - yeni kurulumda pahalı ve niş provider'ları varsayılan açık başlatmamak
- Uygulanan değişiklikler:
  - `provider_freshness.py` eklendi; collector-call seviyesinde kısa TTL cache yalnız `vertexai`, `copilot`, `openrouter` için aktif
  - `collector_helpers.py` cache miss/hit mantığını collector çağrısına sardı; identity-change refetch yolu cache bypass ediyor
  - `collector.py` içindeki force-refresh akışı popup-level force ile provider freshness bypass'ını hizalıyor
  - `models.py` içine `from_dict` roundtrip desteği eklendi
  - `local_usage.py` içinde `claude` ve `vertexai` için file-fingerprint tabanlı local usage cache eklendi
  - yeni varsayılan disabled provider'lar:
    - `amp`, `kilo`, `minimax`, `ollama`, `openrouter`, `vertexai`, `zai`
- Yeni test korumaları:
  - `tests/test_models.py` state roundtrip
  - `tests/test_local_usage.py` claude/vertex cache reuse
  - `tests/test_config.py` expensive provider default disable
  - `tests/test_collector.py` provider freshness cache
- Doğrulama:
  - `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_models.py tests/test_local_usage.py tests/test_config.py tests/test_collector.py tests/test_collector_cache_invalidation.py` PASS (`33 passed`)
  - `PYTHONPATH=. ./.venv/bin/python -m mypy --config-file mypy.ini core/ai_usage_monitor` PASS
  - `make health-ci PYTHON=python` PASS (`17 passed/warned, 0 failed, 0 warnings`)

## 2026-03-08 - Polling Cost Optimization Round 2 Design

- [x] KDE + GNOME polling entrypoint'lerini ve refresh tetikleyicilerini analiz et
- [x] Collector/identity/source-resolution sınırlarını cache uygunluğu açısından çıkar
- [x] En düşük riskli ikinci tur TTL/cache tasarımını belirle
- [x] Dosya etki alanı, davranış riskleri ve test stratejisini dokümante et

### Review

- Mevcut maliyet zinciri:
  - KDE: `main.qml` içindeki periyodik `refreshTimer` + `onExpandedChanged` anlık refresh
  - GNOME: `indicatorLifecycleMixin._scheduleRefresh()` periyodik refresh + menu open refresh
  - Her refresh bir `python3 ... fetch_all_usage.py popup-vm` subprocess'i başlatıyor
  - Backend `collect_all()` her çağrıda tüm aktif provider'ları topluyor; identity switch varsa ek refetch turu yapabiliyor
- En düşük riskli ikinci tur kararı:
  - Provider-level cache yerine `popup-vm payload` sınırında kısa TTL cache
  - Etkileşimli akış (menu open / identity refresh) `--force` ile cache bypass
  - Background poll (timer) cache kullanabilir
- Neden bu yaklaşım:
  - `collector_helpers.collect_provider` + source fallback + identity refetch semantiğine dokunmuyor
  - Provider descriptor/registry/fetch stratejisi contract'ını bozmuyor
  - Sadece orchestrasyon katmanında tekrar işi azaltıyor

## 2026-03-08 - Polling Cost Optimization Round 2 Execution

- [x] `popup-vm` payload için kısa TTL cache ekle
- [x] CLI tarafına `popup-vm --force` parse desteği ekle
- [x] KDE timer/menu/identity refresh path'lerini force semantiğiyle ayır
- [x] GNOME timer/menu/identity refresh path'lerini force semantiğiyle ayır
- [x] Config normalize alanına `pollingCacheSeconds` ekle
- [x] Regresyon testleri ve lifecycle contract kontrollerini güncelle
- [x] Doğrulama: hedefli pytest + mypy + `make health-ci PYTHON=python`

### Review

- Uygulanan yaklaşım provider-level cache değil, `collect_popup_vm_payload(...)` seviyesinde TTL cache oldu.
- Yeni davranış:
  - background timer poll cache kullanabilir
  - menu open ve identity refresh yolları `--force` ile cache bypass eder
- Backend değişiklikleri:
  - `config.py` içine `pollingCacheSeconds` eklendi (`default=10`, clamp `0..60`)
  - `collector.py` içinde popup payload cache key: `mode + preferredProviderId + normalized config`
  - `cli.py` içinde `popup-vm --force` ve `popup-vm <provider> --force` parse desteği eklendi
- Frontend wiring:
  - KDE `refresh(false)` timer, `refresh(true)` menu open / identity refresh / initial load
  - GNOME `_refresh(false)` timer, `_refresh(true)` menu open / identity refresh / initial load
- Koruma:
  - lifecycle contract tokenları `--force` wiring için güncellendi
  - collector/config/cli testleri cache hit, force bypass ve arg parse davranışını kilitliyor
- Dokümanlar:
  - `docs/plans/2026-03-08-polling-cost-optimization-round-2-design.md`
  - `docs/plans/2026-03-08-polling-cost-optimization-round-2.md`
- Doğrulama:
  - `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_collector.py tests/test_config.py tests/test_cli_config.py tests/test_project_health_contracts.py` PASS (`46 passed`)
  - `PYTHONPATH=. ./.venv/bin/python -m mypy --config-file mypy.ini core/ai_usage_monitor` PASS
  - `make health-ci PYTHON=python` PASS (`17 passed/warned, 0 failed, 0 warnings`)

## 2026-03-08 - FinOps Runtime Optimization Round 1

- [x] FinOps tranche planını yaz ve kapsamı kilitle
- [x] Codex local usage + latest snapshot çift taramasını tek geçişe indir
- [x] OpenCode auto akışında gereksiz local/web çift scan maliyetini kaldır
- [x] Status page ve browser cookie import yoluna düşük riskli disk-backed cache ekle
- [x] Regresyon testlerini ekle ve hedefli kalite kapılarını çalıştır

### Review

- Bu tur agresif polling mimarisini değiştirmedi; runtime davranışı korunarak tekrar iş azaltıldı.
- Uygulanan optimizasyonlar:
  - `runtime_cache.py` ile state dir altında TTL tabanlı küçük JSON cache yardımıcısı eklendi
  - `status.py` artık status endpoint yanıtlarını kısa süreli cache'liyor
  - `browser_cookies.py` aynı DB fingerprint'i için cookie import sonucunu kısa süreli cache'liyor
  - `collect_codex()` ikinci `rglob` turunu kaldırıp aynı dosya listesini local usage + latest snapshot yollarında yeniden kullanıyor
  - `collect_opencode()` auto/web başarı yolunda gereksiz ön local scan yapmıyor; web success/error yolunda local usage en fazla bir kez hesaplanıyor
- Yeni regresyon korumaları:
  - `tests/test_status.py`
  - `tests/test_browser_cookies.py` cache reuse vakası
  - `tests/test_local_usage.py` supplied files fast-path vakası
  - `tests/test_codex_normalization.py` supplied files ile reglobbing olmaması
  - `tests/test_opencode_provider.py` web başarı yolunda tek local usage scan
- Doğrulama:
  - `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_local_usage.py tests/test_codex_normalization.py tests/test_opencode_provider.py tests/test_browser_cookies.py tests/test_status.py` PASS (`24 passed`)
  - `PYTHONPATH=. ./.venv/bin/python -m mypy --config-file mypy.ini core/ai_usage_monitor` PASS
  - `make health-ci PYTHON=python` PASS (`17 passed/warned, 0 failed, 0 warnings`)

## 2026-03-08 - Dormant Provider Archive Plan

- [x] Dormant provider arşivleme kapsamını çıkar
- [x] `kiro` / `jetbrains` / `warp` / `kimik2` için arşivleme planını yaz
- [x] Test, docs ve compat risklerini plan içinde ayrı ele al
- [x] Uygulama planını `docs/plans/2026-03-08-dormant-provider-archive.md` altında kaydet

### Review

- Plan, dormant provider implementation'larını active runtime yüzeyinden çıkarıp
  `core.ai_usage_monitor.archived_providers` namespace'ine taşıyacak şekilde yazıldı.
- Güvenli tercih:
  - runtime registry/fetch yüzeyi temiz kalır
  - eski importlar için gerekirse shim bırakılır
  - default CI'da ana ürün davranışı korunur
- Plan dosyası:
  - `docs/plans/2026-03-08-dormant-provider-archive.md`

## 2026-03-08 - Dormant Provider Archive Execution

- [x] Archive namespace oluştur (`core.ai_usage_monitor.archived_providers`)
- [x] `kiro` / `jetbrains` / `warp` / `kimik2` implementasyonlarını archive namespace'ine taşı
- [x] Eski provider modüllerini compat shim'e çevir
- [x] Test importlarını archive namespace'e taşı ve boundary test ekle
- [x] README ve core boundary dokümantasyonunu archived/not-shipped ayrımıyla güncelle
- [x] Doğrulama: hedefli pytest + `ruff` + `mypy` + `make health-ci PYTHON=python`

### Review

- Yeni aktif olmayan namespace:
  - `core.ai_usage_monitor.archived_providers`
- Taşınan implementasyonlar:
  - `kiro`, `jetbrains`, `warp`, `kimik2`
- Compat yaklaşımı:
  - eski `core.ai_usage_monitor.providers.*` modülleri ince shim olarak bırakıldı
  - böylece dış import riski minimize edilirken shipped runtime yüzeyi temiz kaldı
- Yeni koruma:
  - `tests/test_archived_provider_boundaries.py` aktif package/registry/fetch yüzeyine bu provider'ların geri sızmasını kilitliyor
- Doğrulama:
  - `pytest -q tests/test_archived_provider_boundaries.py tests/test_kiro_provider.py tests/test_jetbrains_provider.py tests/test_api_providers.py tests/test_cli_detect.py tests/test_config.py tests/test_provider_registry_shape.py` PASS (`19 passed`)
  - `PYTHONPATH=. ./.venv/bin/python -m mypy --config-file mypy.ini core/ai_usage_monitor` PASS
  - `make health-ci PYTHON=python` PASS (`17 passed/warned, 0 failed, 0 warnings`)

## 2026-03-08 - Dead Code Cleanup

- [x] Audit içindeki yüksek güven dead-code bulgularını kaldır
- [x] Düşük riskli medium import/export temizliklerini uygula
- [x] Runtime import zincirinden shipped olmayan provider eager-importlarını çıkar
- [x] Doğrulama: hedefli testler + `make health-ci PYTHON=python`

### Review

- Kaldırılan dead code:
  - `extension.js` içindeki mixin tarafından gölgelenen iki timeout temizleme metodu
  - buna bağlı `GLib` importu
  - `ConfigPresentation.js` ve GNOME prefs presentation tarafındaki kullanılmayan helper/export yüzeyi
  - `tools/project_health_check.py` içindeki kullanılmayan `CheckResult.ok`
  - `core.ai_usage_monitor.api.PublicPayload`
  - `core.ai_usage_monitor.providers.base.ProviderCollector`
- Runtime import yüzeyi daraltıldı:
  - `core.ai_usage_monitor.providers.__init__` artık shipped olmayan `kiro` / `jetbrains` / `warp` / `kimik2` collector’larını eager-import etmiyor
- Doğrulama:
  - `pytest -q tests/test_project_health_contracts.py tests/test_core_api_boundary.py tests/test_provider_registry_shape.py tests/test_config.py` PASS (`25 passed`)
  - `make health-ci PYTHON=python` PASS (`17 passed/warned, 0 failed, 0 warnings`)

## 2026-03-08 - Dead Code Audit

- [x] Repo kapsamını, entrypoint'leri ve manifestleri doğrula
- [x] Python modüllerinde unreachable declaration ve dead flow adaylarını çıkar
- [x] GNOME JS / KDE JS-QML yüzeyinde unused import, unreachable declaration ve dead file adaylarını çıkar
- [x] Paket seviyesinde phantom dependency adaylarını doğrula
- [x] Dinamik kullanım / framework hook / public API istisnalarıyla yanlış pozitifleri ele
- [x] Bulguları risk seviyesine göre triage edip raporla

### Review

- Doğrulanan yüksek güven bulgular:
  - `extension.js` içinde mixin tarafından gölgelenen iki timeout temizleme metodu
  - buna bağlı ölü `GLib` importu
  - `ConfigPresentation.js` içindeki kullanılmayan `humanizeReason`
  - `tools/project_health_check.py` içindeki kullanılmayan `CheckResult.ok` property
- Düşük/orta risk bulgular çoğunlukla backward-compat shim veya shipped runtime'a bağlı olmayan legacy provider kodu:
  - `source_model.py`, `popup_vm_source.py`, `state.py`, `util.py`
  - runtime registry/fetch stratejilerinden dışlanan `kiro` / `jetbrains` / `warp` / `kimik2`
- Paket seviyesi phantom dependency doğrulaması:
  - `eslint` ve `eslint-plugin-jsdoc` aktif kullanılıyor
  - `requirements-dev.txt` içindeki araçların hepsi quality gate'lerde referanslı

## 2026-03-08 - PR Review + CI Fix Round

- [x] Copilot review yorumlarına karşılık gelen patchleri doğrula ve uygula
- [x] Shellcheck SC2015 kırığını `install.sh` içinde güvenli if bloğuna çevir
- [x] `qmllint` tespitini CI runner path farklılıklarına dayanıklı hale getir
- [x] `qmllint` çıktısında import-resolution warning ile gerçek syntax hatasını ayır
- [x] Quality workflow içinde Qt6 binary path'lerini `GITHUB_PATH` ile aç
- [x] Doğrulama: `make lint`, `make typecheck`, `make health-ci PYTHON=python`

### Review

- CI kırığı iki kök nedenden geliyordu:
  - `com.aiusagemonitor/install.sh` satırındaki SC2015 deseni
  - bazı runner ortamlarında `qmllint` binary'sinin PATH dışında kalması
- Uygulanan patch sonrası yerel strict kapı temiz:
  - `make health-ci PYTHON=python` PASS (`17 passed/warned, 0 failed, 0 warnings`)

- [x] Audit: GNOME lint coverage dışı JS dosyaları var mı doğrula
- [x] Audit: baseline lock altında kalan legacy büyük dosyaları ve görünürlük seviyesini doğrula
- [x] Audit: KDE/GNOME settings source-status presentation tekrarlarını çıkar
- [x] GNOME lint kapsamını manuel listeden otomatik keşfe geçir
- [x] Baseline lock raporunu `BASELINE_TIGHTEN_DUE` sinyali ile dürüstleştir
- [x] Settings presentation fallback policy tekrarını renderer tarafında azalt (KDE+GNOME)
- [x] Doğrulamalar: lint/check + hedefli testler

## 2026-03-08 - Post-Mypy Quality Debt Round 1

- [x] GNOME lint coverage hardening:
  - `GNOME_EXTENSION_JS_TARGETS` otomatik keşif (`rglob`) ile üretildi
  - `eslint` globları `**/*.js` olacak şekilde genişletildi
  - coverage testleri recursive hale getirildi
- [x] Baseline/complexity signal hardening:
  - `size-complexity-warnings` içinde yeni `BASELINE_TIGHTEN_DUE` sınıfı eklendi
  - `DEBT_SUMMARY` alanına `tighten_due` eklendi
  - legacy lock altında kalıp next-baseline seviyesinde kalan borçlar açıkça raporlanır hale getirildi
- [x] Settings duplicated presentation policy reduction:
  - KDE `ConfigPresentation.js` fallback policy üretimi sadeleştirildi
  - GNOME `prefsProviderPresentation.js` fallback policy üretimi sadeleştirildi
  - Canonical `sourceModel.settingsPresentation` alanları primary source olarak bırakıldı
- [x] Doğrulama:
  - `npm run -s lint:gjs` PASS
  - `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_project_health_contracts.py tests/test_cli_config.py tests/test_collector.py` PASS (`31 passed`)
  - `python tools/project_health_check.py --mode quick` PASS (yalnız beklenen complexity debt WARN)

### Review

- GNOME lint coverage:
  - toplam JS: `17`
  - lint kapsanan: `17`
  - kapsanmayan: `0`
- Baseline debt görünürlüğü:
  - önceki modelde yalnız `LEGACY_DEBT_LOCKED` altında saklanan borçlar artık
    `BASELINE_TIGHTEN_DUE` olarak ayrı görünüyor.
- Kalan en büyük debt sinyali:
  - provider parser/orchestration fonksiyonlarında `BASELINE_BREACH` ve
    `BASELINE_TIGHTEN_DUE` alarmları.

- [x] Faz 14: `providers.minimax` typing debt temizliği + override kaldırma
- [x] Faz 15: `providers.opencode` typing debt temizliği + override kaldırma
- [x] Faz 16: `mypy.ini` quarantine kontrolü + final doğrulama (`make typecheck`, ilgili testler)

## 2026-03-08 - Mypy Hardening Round 5 (Quarantine Zero)

- [x] `providers.minimax` helper imzaları eklendi:
  - `_hosts`, `parse_cookie_override`, `_cookie_override`, `_auto_cookie`, `parse_minimax_payload`, URL helperları
- [x] `providers.minimax` union daraltmaları düzeltildi:
  - `_region`, `_api_token`, `settings.get(...).strip()` akışları
- [x] `providers.minimax` override kaldırıldı:
  - `core.ai_usage_monitor.providers.minimax`
- [x] `providers.opencode` helper imzaları eklendi:
  - `_collect_workspace_ids_json`, `_extract_number`, `_extract_int`, `_fetch_server_text`
- [x] `providers.opencode` union daraltmaları düzeltildi:
  - `_local_auth_type`, `auth_type` Optional/string akışları
- [x] `providers.opencode` override kaldırıldı:
  - `core.ai_usage_monitor.providers.opencode`
- [x] Faz sonu doğrulamalar:
  - Faz 14 `make typecheck`: PASS
  - Faz 15 `make typecheck`: PASS
  - Faz 16 `make typecheck`: PASS
  - `pytest tests/test_minimax_provider.py tests/test_opencode_provider.py`: `9 passed`

### Review

- Kalan `ignore_errors` override sayısı: `2 -> 0`
- Sonuç: `mypy quarantine debt sıfırlandı`

- [x] Faz 11: `providers.copilot` ve `providers.claude` quarantine kaldır + tip düzeltmeleri
- [x] Faz 12: `providers.codex` ve `providers.gemini` quarantine kaldır + tip düzeltmeleri
- [x] Faz 13: `providers.minimax` ve `providers.opencode` için gerçek debt envanteri çıkar
- [x] Her faz sonunda `make typecheck` çalıştır

## 2026-03-08 - Mypy Hardening Round 4

- [x] `mypy.ini` quarantine’den kaldırıldı:
  - `core.ai_usage_monitor.providers.copilot`
  - `core.ai_usage_monitor.providers.claude`
  - `core.ai_usage_monitor.providers.codex`
  - `core.ai_usage_monitor.providers.gemini`
- [x] `copilot` typing cleanup: token/settings daraltma, payload dict normalizasyonu, error alanı tipi
- [x] `claude` typing cleanup: data/legacy/identity tip normalizasyonu, error alanı tipi
- [x] `codex` typing cleanup: `normalize_codex_rate_limits` imzaları ve typed payload/local usage
- [x] `gemini` typing cleanup: bucket/payload/refreshtoken akışı tip daraltma ve error alanı tipi
- [x] `minimax` + `opencode` debt envanteri (geçici config ile overridesiz mypy denemesi)

### Review

- Faz sonu typecheck:
  - Faz 11: `make typecheck` PASS
  - Faz 12: `make typecheck` PASS
  - Faz 13: `make typecheck` PASS
- Quarantine debt:
  - `ignore_errors`: `6 -> 2`
  - Kalan modüller: `providers.minimax`, `providers.opencode`
- Faz 13 envanteri (`minimax` + `opencode`, overridesiz):
  - Toplam: `19` hata
  - `minimax`: `12` hata
  - `opencode`: `7` hata
  - Kod bazında: `no-untyped-def=14`, `union-attr=3`, `no-any-return=2`

- [x] Faz 8: `providers.kilo` eksik 13 imzayı tamamla
- [x] Faz 8: `providers.kilo` carve-out override’ını kaldır
- [x] Faz 9: core override debt temizliği (`local_usage`, `browser_cookies`, `presentation.identity_vm`)
- [x] Faz 10: düşük churn provider override debt azaltımı (`ollama`, `vertexai`, `zai`)
- [x] Her faz sonunda `make typecheck` ile temiz doğrulama

## 2026-03-08 - Mypy Hardening Round 3

- [x] `providers.kilo` içindeki eksik 13 imza tamamlandı
- [x] `mypy.ini` içinden `providers.kilo` carve-out kaldırıldı
- [x] `local_usage` ignore override kaldırıldı ve union/annotation hataları düzeltildi
- [x] `browser_cookies` ignore override kaldırıldı ve query row typing düzeltildi
- [x] `presentation.identity_vm` ignore override kaldırıldı ve dict narrowing düzeltildi
- [x] Provider quarantine debt reduction:
  - `core.ai_usage_monitor.providers.ollama` override kaldırıldı
  - `core.ai_usage_monitor.providers.vertexai` override kaldırıldı
  - `core.ai_usage_monitor.providers.zai` override kaldırıldı
- [x] Faz sonu doğrulamalar:
  - Faz 8 `make typecheck`: PASS
  - Faz 9 `make typecheck`: PASS
  - Faz 10 `make typecheck`: PASS

### Review

- `ignore_errors` override sayısı: `12 -> 6`
- `disallow_incomplete_defs` carve-out sayısı: `1 -> 0`
- Kalan quarantine modülleri:
  - `core.ai_usage_monitor.providers.claude`
  - `core.ai_usage_monitor.providers.codex`
  - `core.ai_usage_monitor.providers.copilot`
  - `core.ai_usage_monitor.providers.gemini`
  - `core.ai_usage_monitor.providers.minimax`
  - `core.ai_usage_monitor.providers.opencode`

- [x] Faz 5: `amp` ve `jetbrains` carve-out borcunu kapat
- [x] Faz 5: `kilo` için strict annotation debt listesini çıkar
- [x] Faz 6: provider `ignore_errors` debt’ini düşük-churn modüllerde azalt
- [x] Faz 7: `sources.*` ve `presentation.*` için modül bazlı `disallow_untyped_calls` aç
- [x] Her faz sonunda `make typecheck` çalıştır ve doğrula

## 2026-03-08 - Mypy Hardening Round 2

- [x] `amp` ve `jetbrains` için annotation eksiklerini düzelt
- [x] `mypy.ini` carve-out’tan `providers.amp` ve `providers.jetbrains` kayıtlarını kaldır
- [x] `kilo` için eksik annotation envanteri üret (`13` eksik imza)
- [x] Provider override debt reduction (low-churn):
  - `core.ai_usage_monitor.providers.kimik2` override kaldırıldı
  - `core.ai_usage_monitor.providers.openrouter` override kaldırıldı
  - `core.ai_usage_monitor.providers.warp` override kaldırıldı
- [x] `sources.*` ve `presentation.*` için `disallow_untyped_calls = True` aç
- [x] `popup_vm.py` no-untyped-call hatası için `ProviderRegistry.__init__` imzasını tipli hale getir

### Review

- `ignore_errors` sayısı: `15 -> 12`
- `disallow_incomplete_defs` carve-out sayısı: `3 -> 1` (yalnız `providers.kilo`)
- Faz sonu typecheck:
  - Faz 5: `make typecheck` PASS
  - Faz 6: `make typecheck` PASS
  - Faz 7: `make typecheck` PASS

- [x] Faz 1: `warn_unreachable` aç ve 3 unreachable hatayı düzelt
- [x] Faz 2: `disallow_incomplete_defs` aç ve cli/config/collector_helpers/status imzalarını tamamla
- [x] Faz 3: modül bazlı `disallow_untyped_defs` strictness’i etkinleştir (sources/models/identity_apply/popup_vm_source)
- [x] Faz 4: 4 kritik override’ı kaldır (`popup_vm_metrics_core`, `popup_vm_usage_blocks`, `identity_fingerprint`, `identity_snapshot`) ve tip hatalarını düzelt
- [x] Her faz sonunda `make typecheck` çalıştır

## 2026-03-08 - Mypy Incremental Strictness Hardening

- [x] `mypy.ini` global: `warn_unreachable = True`
- [x] `mypy.ini` global: `disallow_incomplete_defs = True`
- [x] Faz-2 geçişi için provider modüllerine geçici carve-out (`amp`, `jetbrains`, `kilo`)
- [x] Faz-3 scoped strictness:
  - `core.ai_usage_monitor.sources.*`
  - `core.ai_usage_monitor.models`
  - `core.ai_usage_monitor.identity_apply*`
  - `core.ai_usage_monitor.presentation.popup_vm_source*`
- [x] Faz-4 debt reduction:
  - `ignore_errors` kaldırıldı: `core.ai_usage_monitor.presentation.popup_vm_metrics_core`
  - `ignore_errors` kaldırıldı: `core.ai_usage_monitor.presentation.popup_vm_usage_blocks`
  - `ignore_errors` kaldırıldı: `core.ai_usage_monitor.identity_fingerprint`
  - `ignore_errors` kaldırıldı: `core.ai_usage_monitor.identity_snapshot`
- [x] Hedefli tip düzeltmeleri ve doğrulama

### Review

- `ignore_errors` override sayısı: `19 -> 15`
- `make typecheck`:
  - Faz 1: PASS
  - Faz 2: PASS
  - Faz 3: PASS
  - Faz 4: PASS
- Kalan debt (bilinçli): provider tarafında `disallow_incomplete_defs = False` carve-out (`amp`, `jetbrains`, `kilo`).

- [x] GNOME lifecycle contract’ı extension.js token kontrolünden çok-dosyalı kurala genişlet
- [x] KDE için lifecycle contract check’i ekle (timer/DataSource/destruction cleanup)
- [x] lifecycle check raporunu syntax’tan ayrı isimlerle görünür hale getir
- [x] lifecycle contract regression testleri ekle
- [x] make lint ve hedefli testlerle doğrula

## 2026-03-08 - Lifecycle Guard Hardening (GNOME + KDE)

- [x] `tools/project_health_contracts.py` içinde GNOME/KDE lifecycle kurallarını dosya bazlı tanımla
- [x] GNOME kurallarını `extension.js` + `indicatorLifecycleMixin.js` + `indicatorContentFlowMixin.js` kapsayacak şekilde genişlet
- [x] KDE kurallarını `main.qml` + `configGeneral.qml` için timer/source/disconnect/destruction odaklı tanımla
- [x] `tools/project_health_check.py` içinde generic lifecycle contract checker ekle
- [x] Health check adlarını netleştir: `gnome-lifecycle-contract`, `kde-lifecycle-contract`
- [x] `tests/test_project_health_contracts.py` içine lifecycle contract regression testleri ekle
- [x] `make lint` ve hedefli pytest doğrulamasını çalıştır

### Review

- Lifecycle contract sinyali artık syntax check’ten ayrı ve explicit:
  - `gnome-lifecycle-contract` (3 dosya)
  - `kde-lifecycle-contract` (2 dosya)
- Yeni sinyal tipi:
  - `required_tokens` yoksa `FAIL`
  - `forbidden_tokens` varsa `FAIL`
  - `warn_tokens` görülürse `WARN`
- Doğrulama:
  - `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_project_health_contracts.py` => `14 passed`
  - `./.venv/bin/python tools/project_health_check.py --mode quick` => lifecycle check’ler `PASS`
  - `make lint` => `0 failed` (yalnız mevcut legacy complexity debt WARN)

- [x] KDE/GNOME settings presentation duplicate policy noktalarını çıkar
- [x] Core `sourceModel.settingsPresentation` canonical alanlarını renderer’lara bağla
- [x] KDE `ConfigPresentation.js` fonksiyonlarını canonical alan-first hale getir
- [x] GNOME `prefsProviderPresentation.js` fonksiyonlarını canonical alan-first hale getir
- [x] GNOME prefs payload akışında `state.providers[*].sourceModel` erişimini garanti et
- [x] Settings canonical alanları için core test kilidi ekle/güncelle
- [x] Hedefli lint/test/check komutlarıyla doğrula
- [x] `docs/renderer-purity.md` içine settings canonical contract notunu ekle
- [x] `tasks/lessons.md` dosyasına bu düzeltmeden öğrenim ekle

## 2026-03-07 - Settings Presentation Canonicalization (KDE + GNOME)

- [x] KDE/GNOME settings duplicate source/status text policy üretimlerini tespit et
- [x] Core `sourceModel.settingsPresentation` alanlarını renderer’larda primary source yap
- [x] KDE settings row’da `sourceStatusLabel` + `fallbackLabel` binding’i ekle
- [x] GNOME prefs status/reason satırlarını canonical alanlardan üret
- [x] GNOME backend çağrısını `config-ui-full` ile live state içerecek hale getir
- [x] CLI `config-ui-full` modunu ekle ve testle kilitle
- [x] Complexity breach oluşturmadan `build_provider_source_model` fonksiyonunu helper’lara böl
- [x] Lint/typecheck/test doğrulamalarını çalıştır

### Review

- Değişen çekirdek contract:
  - `sourceModel.settingsPresentation` artık KDE/GNOME settings tarafında primary tüketim kaynağı.
- Değişen dosyalar:
  - `core/ai_usage_monitor/sources/model.py`
  - `core/ai_usage_monitor/cli.py`
  - `com.aiusagemonitor/contents/ui/ConfigPresentation.js`
  - `com.aiusagemonitor/contents/ui/configGeneral.qml`
  - `com.aiusagemonitor/contents/ui/ConfigProvidersSection.qml`
  - `com.aiusagemonitor/contents/ui/SettingsProviderRow.qml`
  - `gnome-extension/aiusagemonitor@aimonitor/prefsProviderPresentation.js`
  - `gnome-extension/aiusagemonitor@aimonitor/prefsProviderExpander.js`
  - `gnome-extension/aiusagemonitor@aimonitor/prefs.js`
  - `docs/renderer-purity.md`
  - `tests/test_cli_config.py`
  - `tests/test_collector.py`
- Doğrulama:
  - `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_cli_config.py tests/test_collector.py` => `17 passed`
  - `make lint` => `0 failed` (`size-complexity-warnings`: yalnız mevcut legacy debt uyarıları)
  - `make typecheck` => `Success: no issues found in 65 source files`

- [x] Debt reduction: `popup_vm.py` dosyasını source/panel/metric/action/common bölümlerine gerçek modül sınırlarıyla ayır
- [x] Debt reduction: `extension.js` dosyasını lifecycle/fetch/render builder modüllerine ayır
- [x] Debt reduction: `prefs.js` dosyasını provider presentation + provider expander + form row helper modüllerine ayır
- [x] Debt reduction: `configGeneral.qml` dosyasını section component’lerine ayır (General/Overview/Providers/Footer)
- [x] Debt reduction: `identity.py` dosyasını fingerprint/store/snapshot/apply akış modüllerine ayır
- [x] Debt reduction: `collector.py` dosyasını collect pipeline helper modüllerine ayır
- [x] Debt reduction: `FullRepresentation.qml` içinde selection/tabs state logic’ini ayrı helper component’e taşı
- [x] Debt reduction: `PopupHeader.qml` source/status chip bloklarını alt component’lere ayır
- [x] Her adımda hedefli syntax/lint/test doğrulaması çalıştır

## 2026-03-07 - Real Debt Reduction (No Baseline-Only)

- [x] Öncelik-1 `popup_vm.py` gerçek modül ayrımı (tabs/provider/source/metrics/panel/common)
- [x] Öncelik-2 `extension.js` mixin bazlı gerçek bölme
- [x] Öncelik-3 `prefs.js` helper/presentation/expander modülleri
- [x] Öncelik-4 `configGeneral.qml` section component ayrımı
- [x] Öncelik-5 `identity.py` façade + apply/context/store/fingerprint/snapshot modülleri
- [x] Öncelik-6 `collector.py` façade + `collector_helpers.py` pipeline ayrımı
- [x] Öncelik-7 `FullRepresentation.qml` selection helper JS ayrımı
- [x] Öncelik-8 `PopupHeader.qml` title/source/status alt component ayrımı

### Review

- Satır hedefleri: 8 öncelik dosyanın tamamı alarm eşiği altına indirildi.
- Doğrulama:
  - `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_popup_vm.py tests/test_popup_vm_fixtures.py tests/test_collector.py tests/test_identity_multi_account.py tests/test_presentation_helper_modules.py` => `42 passed`
  - `node --check ...` (extension/prefs + yeni GNOME modülleri) => başarılı
  - `qmllint ...` (config + popup header/full representation + yeni KDE componentleri) => başarılı
  - `python3 tools/project_health_check.py --mode quick` => `13 passed/warned, 0 failed, 0 warnings`

- [x] Warning-first guard için legacy debt baseline kilidi ekle (strict eşikleri koru, büyümeyi yakala)
- [x] Health check’i warning-free doğrula

- [x] Size/complexity eşiklerini önerilen profile çek (helper 50–120, UI 80–200, orchestration 250+ alarm)
- [x] Warning-first guard’ın önerilen eşiklerde çalıştığını doğrula

- [x] Size/complexity guard eşiklerini mevcut mimariye göre güvenli sınıra kalibre et
- [x] Health check çıktısını warning-free duruma getir

- [x] Riskli dosyaları satır/fonksiyon büyüklüğü açısından tespit et
- [x] Warning-first dosya boyutu eşik politikasını tanımla
- [x] Basit fonksiyon complexity (line+branch) uyarı politikasını ekle
- [x] Health check’e CI/local’de çalışan size-complexity warning guard ekle
- [x] Contract testlerini yeni policy alanlarıyla güncelle
- [x] lessons.md’ye bu turdan dersleri ekle

## 2026-03-07 - Size/Complexity Guard (Warning-First)

- [x] `tools/project_health_contracts.py` içine dosya boyutu warning eşiklerini ekle
- [x] Python fonksiyon complexity warning eşiklerini ekle (`lines + branch points`)
- [x] Complexity izlemesini hedef dosya listesiyle sınırla (sürdürülebilir gürültü seviyesi)
- [x] `tools/project_health_check.py` içine `size-complexity-warnings` check’i ekle
- [x] `tests/test_project_health_contracts.py` testlerini policy sanity + file existence ile genişlet
- [x] Quick health check çıktısını doğrula (WARN üretir, FAIL etmez)

### Review

- Guard davranışı:
  - Yeni check adı: `size-complexity-warnings`
  - Çıkış tipi: `WARN` (warning-first), pipeline’ı kırmaz
  - Çalışma yeri: `tools/project_health_check.py` (quick/full/ci modlarının hepsinde)
- Risk sinyalleri (örnek alarm dosyaları):
  - `gnome-extension/.../extension.js`
  - `gnome-extension/.../prefs.js`
  - `core/.../presentation/popup_vm.py`
  - `core/.../identity.py`
  - `com.aiusagemonitor/contents/ui/configGeneral.qml`
- Doğrulama:
  - `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_project_health_contracts.py` => `7 passed`
  - `python3 tools/project_health_check.py --mode quick` => `0 failed, 1 warning`

- [x] Renderer purity ihlallerini KDE/GNOME tarafında satır bazında tespit et
- [x] Core `popup_vm` contract’ına renderer policy/fallback ihtiyacını taşı (selection/tabs/panel)
- [x] GNOME renderer helper/policy logiclerini VM-first binding’e indir
- [x] KDE renderer helper/policy logiclerini VM-first binding’e indir
- [x] Renderer purity kuralını dokümante et (`docs/`)
- [x] Renderer purity regresyon testlerini ekle/güncelle
- [x] Hedefli test/lint/syntax doğrulamalarını çalıştır
- [x] lessons.md’ye bu turdan dersleri ekle

## 2026-03-07 - Renderer Purity (KDE + GNOME)

- [x] `popup_vm` contract’ına `switcherTabs`, `selectableProviderIds`, `panel` alanlarını ekle
- [x] GNOME popup tab/panel fallback/policy helperlarını kaldır ve VM-first binding’e geçir
- [x] KDE Full/Compact representation’ı VM-first contract tüketimine geçir
- [x] Renderer’da metric order/panel tone/fallback badge policy üretimini azalt
- [x] Renderer purity kuralını `docs/renderer-purity.md` ile dokümante et
- [x] Popup VM regression fixture/testlerini yeni contract alanlarıyla güncelle

### Review

- Taşınan policy logic:
  - Tab/switcher sıralama + selectable provider listesi artık core `popup_vm` üretimi.
  - Panel tone/percent/display/tooltip fallback artık core `popup.panel` üretimi.
  - Metric order/visibility renderer’da tekrar sıralanmak yerine core `provider.metrics` sırası tüketiliyor.
- Renderer cleanup:
  - GNOME `popupSelection.js` fallback/spec/policy üretiminden çıkarıldı.
  - KDE `PopupSelectionPolicy.js` ve `PopupTabModel.js` kaldırıldı.
- Doğrulama:
  - `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_popup_vm.py tests/test_popup_vm_fixtures.py` => `24 passed`
  - `node --check gnome-extension/aiusagemonitor@aimonitor/extension.js gnome-extension/aiusagemonitor@aimonitor/popupSelection.js`
  - `qmllint com.aiusagemonitor/contents/ui/FullRepresentation.qml com.aiusagemonitor/contents/ui/ProviderDetailSection.qml com.aiusagemonitor/contents/ui/CompactRepresentation.qml`
  - `python3 tools/project_health_check.py --mode quick` => `0 failed, 0 warnings`

- [x] Core health hardening için mevcut klasör/sorumluluk haritasını netleştir
- [x] `presentation/popup_vm.py` içindeki identity/status/pace helper bloklarını ayrı modüllere böl
- [x] `util.py` içindeki dağınık yardımcıları `core/shared` altında sorumluluk bazlı modüllere ayır
- [x] Provider importlarını yeni core modül sınırlarına geçir ve type hintleri güçlendir
- [x] Public/internal API sınırlarını netleştir (`__init__`/api yüzeyi)
- [x] Core odaklı regression testlerini ekle/güncelle
- [x] Core test ve health gate doğrulamalarını çalıştır
- [x] lessons.md’ye bu turdan çıkarımları ekle

## 2026-03-07 - Core-Only Health Hardening (Incremental)

- [x] `popup_vm` helper bloklarını modül bazında ayır (`identity_vm`, `status_vm`, `pace_vm`)
- [x] `util.py` yardımcılarını sorumluluk bazlı `shared/` modüllerine böl (`http_failures`, `oauth`, `time_utils`)
- [x] Provider modüllerini legacy util yerine yeni shared importlarına geçir
- [x] `sources/` paketi ile source strategy/model sorumluluğunu netleştir (shim backward-compat korunarak)
- [x] Public API yüzeyini `api.py` ile explicit hale getir (`__init__` export sınırı)
- [x] Yeni modül sınırları için hedefli testler ekle
- [x] Sağlık kapıları + core testlerini doğrula

### Review

- Bölünen core dosyaları:
  - `presentation/popup_vm.py` -> `presentation/identity_vm.py`, `presentation/status_vm.py`, `presentation/pace_vm.py`
  - `util.py` -> `shared/http_failures.py`, `shared/oauth.py`, `shared/time_utils.py` (+ `util.py` compatibility shim)
  - `source_model.py` ve `source_strategy.py` -> `sources/model.py` ve `sources/strategy.py` (+ backward-compatible shim)
- API sınırları:
  - `core/ai_usage_monitor/api.py` eklendi; public yüzey bu dosya üzerinden export ediliyor.
  - `core/ai_usage_monitor/__init__.py` sadece public collector API'lerini dışa açıyor.
- Doğrulama:
  - `python3 tools/project_health_check.py --mode quick` => `0 failed`
  - `PYTHONPATH=. ./.venv/bin/pytest -q` => `111 passed`
  - `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_core_api_boundary.py tests/test_presentation_helper_modules.py tests/test_shared_helpers.py` => `8 passed`

- [x] Project health hardening planını (core/renderer sınırları + kalite kapıları) repo gerçek durumuna göre güncelle
- [x] Quality gates: JS syntax false-positive ve shellcheck hatalarını gider
- [x] Quality gates: type-ish + complexity kontrolünü health check pipeline’a ekle
- [x] Cleanup: health contract sabitlerini tek kaynağa taşı (script + test drift riskini azalt)
- [x] Test/regression: fixture tabanlı popup-vm sözleşme testi ekle
- [x] CI/local doğrulama komutlarını çalıştır ve review notunu güncelle
- [x] lessons.md dosyasına bu turdan yeni öğrenimleri ekle

- [x] `local_cli` canonical preferred source policy’yi source strategy katmanında tanımla
- [x] Collector’da source candidate attempt zinciri ile local→remote fallback uygula
- [x] Config normalize/default akışında local-first hybrid provider’lar için `local_cli` preference desteği ekle
- [x] Source model/popup-vm reason mapping’i local-unavailable fallback semantiğiyle güncelle
- [x] KDE/GNOME settings source dropdown’larına `local_cli` seçeneğini ekle ve preferred source görünürlüğünü iyileştir
- [x] Source policy değişikliklerini testlerle kilitle ve full suite doğrula

- [x] Source model canonical alanlarını provider state ve popup-vm üzerinde netleştir (preferred/resolved/available/fallback/local/api/auth)
- [x] availability içinde `apiConfigured` alanını ekle ve consumerları buna geçir
- [x] KDE/GNOME settings provider row strateji satırına `availableSources` görünürlüğü ekle
- [x] Popup source status/availability kontrolünü `apiConfigured` aware hale getir
- [x] Source-aware contract için testleri güncelle ve doğrula

## 2026-03-07 - Developer Ergonomics Hardening

- [x] Pre-commit hook setup akışını sadeleştir (`make hooks-install`, `make hooks-run`)
- [x] Repo komut ergonomisini tek yüzeye topla (`make setup/format/lint/check/test`)
- [x] npm script tarafında aynı komutları onboarding dostu aliaslarla yayınla
- [x] Kısa `CONTRIBUTING.md` dokümanını ekle (onboarding + kurallar)
- [x] README içine contribution rehberi linki ve tek-komut setup notu ekle
- [x] Komut/hook akışını çalıştırıp doğrula

### Review

- Değişen dosyalar:
  - `Makefile`
  - `package.json`
  - `.pre-commit-config.yaml`
  - `CONTRIBUTING.md` (yeni)
  - `README.md`
- Doğrulama:
  - `make check` => `14 passed/warned, 0 failed, 0 warnings`
  - `make lint` => `13 passed/warned, 0 failed, 0 warnings`
  - `make test` => `123 passed, 20 subtests passed`
  - `./.venv/bin/pre-commit run --all-files` => tüm hook’lar `Passed`

## 2026-03-07 - GNOME Lint Coverage Expansion

- [x] GNOME extension altındaki lint dışı JS dosyalarını tespit et
- [x] `GJS_LINT_TARGETS` kapsamını tüm extension JS dosyalarına genişlet
- [x] `JS_SYNTAX_TARGETS` içinde GNOME extension JS kapsamını tam hale getir
- [x] `npm run lint:gjs` komutunu tüm GNOME JS dosyalarını kapsayacak şekilde güncelle
- [x] Kapsamın drift etmemesi için contract testi ekle
- [x] Lint/syntax/health akışını doğrula

### Review

- Lint dışında kalan dosya sayısı: `14` (toplam `17` içinde önce `3` kapsanıyordu).
- Yeni kapsam:
  - `tools/project_health_contracts.py` içinde `GNOME_EXTENSION_JS_TARGETS` (17 dosya)
  - `GJS_LINT_TARGETS` ve `JS_SYNTAX_TARGETS` GNOME tarafında bu listeyi kullanıyor.
- Eklenen koruma:
  - `tests/test_project_health_contracts.py` içine GNOME JS lint/syntax target coverage testleri eklendi.
- Doğrulama:
  - `npm run lint:gjs` => `PASS`
  - `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_project_health_contracts.py` => `11 passed`
  - `make lint` => `gjs-lint checked 17 files`, `0 failed`

## 2026-03-07 - Real Python Typecheck (mypy)

- [x] Python core için gerçek type checker seç ve ekle
- [x] `mypy.ini` ile kontrollü ilk kapsam + typed-debt quarantine tanımla
- [x] `make typecheck` komutunu gerçek mypy çalıştıracak şekilde bağla
- [x] Health check full/ci akışına mypy kontrolünü ekle
- [x] pre-commit içine `python-core-typecheck` hook’unu ekle
- [x] npm script tarafına `typecheck` komutunu ekle
- [x] İlk mypy çalıştırmasını al ve kalan geçici ignore alanlarını dokümante et
- [x] Tüm kalite kapılarını tekrar doğrula

### Review

- Seçim: `mypy` (Python-native, mevcut toolchain ile uyumlu, CI/pre-commit entegrasyonu düşük sürtünmeli).
- Eklenen dosya:
  - `mypy.ini`
- Değişen dosyalar:
  - `requirements-dev.txt`
  - `Makefile`
  - `tools/project_health_check.py`
  - `.pre-commit-config.yaml`
  - `package.json`
  - `.github/workflows/quality-gates.yml`
  - `core/ai_usage_monitor/presentation/popup_vm_source_model.py`
  - `core/ai_usage_monitor/config.py`
- İlk ham mypy çıktısı:
  - `72 errors in 19 files` (config öncesi).
- İlk kontrollü mypy çıktısı (config + 2 küçük fix sonrası):
  - `Success: no issues found in 65 source files`.
- Doğrulama:
  - `make typecheck` => `PASS`
  - `npm run typecheck` => `PASS`
  - `make check` => `mypy PASS`, `0 failed`
  - `pre-commit run --all-files` => `python-core-typecheck Passed`

## 2026-03-07 - Baseline Lock Tightening (Debt Visibility)

- [x] Baseline skip davranışını analiz et (`line_count <= baseline => skip`)
- [x] Skip modelini legacy-debt görünür olacak şekilde kaldır
- [x] Legacy debt / baseline breach / new debt ayrımını raporla
- [x] Gevşek legacy baselines’i kategori bazlı geçici toleranslara çek
- [x] Dosya bazlı reduction planını (current/target/temp baseline/next baseline) dokümante et
- [x] Sağlık çıktısında “0 warning = 0 debt” algısını düzelten notu ekle
- [x] Health check + contract testlerini doğrula

### Review

- Değişen policy:
  - `tools/project_health_check.py` artık baseline altında olsa bile debt’i `LEGACY_DEBT_LOCKED` olarak WARN eder.
  - `BASELINE_BREACH` ve `NEW_DEBT` ayrı sınıflar halinde raporlanır.
  - `DEBT_SUMMARY` satırı eklendi.
- Gevşek baseline düzeltmesi:
  - `tools/project_health_contracts.py` içindeki eski monolit baseline değerleri kaldırıldı.
  - `FILE_SIZE_BASELINE_REDUCTION_PLAN` ve ondan türeyen geçici baseline modeli eklendi.
  - Stale function baseline kayıtları temizlendi.
- Dokümantasyon:
  - `docs/size-complexity-baseline-policy.md` eklendi.
- Doğrulama:
  - `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_project_health_contracts.py` => `12 passed`
  - `python3 tools/project_health_check.py --mode quick` => `size-complexity-warnings` artık debt’i görünür WARN ediyor
  - `make check` => `0 failed`, `1 warnings` (legacy debt görünür)

- [x] Pace tracking’i popup-vm presentation katmanına taşı ve renderer’dan bağımsızlaştır
- [x] Session/weekly metriclerde pace secondaryText üretimi ve visibility kuralını ekle
- [x] Deficit/reserve/lasts-until-reset semantiğini metric bazında normalize et
- [x] Pace davranışı için popup-vm test senaryolarını ekle ve çalıştır

- [x] KDE popup provider detail anatomy sırasını sabitle (header -> session -> weekly -> custom -> extra -> cost -> actions)
- [x] GNOME popup provider detail anatomy sırasını sabitle (header -> session -> weekly -> custom -> extra -> cost -> actions)
- [x] Renderer seviyesinde metric order guard ekle (VM sırasından bağımsız contract)
- [x] Syntax + popup-vm regresyon doğrulamasını çalıştır

- [x] KDE popup tabs row üretimini `enabledProviderIds` tabanlı yap ve overview tabını ayrı ekle
- [x] GNOME popup tabs row üretimini `enabledProviderIds` tabanlı yap ve overview tabını ayrı ekle
- [x] KDE/GNOME settings copy metinlerini enabled tabs vs overview ayrımını netleştirecek şekilde güncelle
- [x] Syntax ve popup-vm test doğrulamasını çalıştır

## 2026-03-07 - Practical Test Strategy (Core-First)

- [x] 10 hedef test alanını mevcut suite ile eşleştirip gap analizi çıkar
- [x] Provider descriptor parse için explicit contract testi ekle
- [x] Cache invalidation için collector helper odaklı testleri ekle
- [x] Fixture/state matrisi dokümantasyonunu tek dosyada netleştir
- [x] Hedefli pytest setini çalıştırıp review bölümüne sonucu yaz

### Review

- Eklenen testler:
  - `tests/test_descriptor_payload_parse.py`
  - `tests/test_collector_cache_invalidation.py`
  - `tests/test_popup_vm_state_matrix.py` içine zorunlu scenario adları kontrolü
- Eklenen doküman:
  - `docs/test-strategy.md`
- Fixture güncellemesi:
  - `tests/fixtures/popup_vm_states/state_matrix.json` beklentileri güncel popup-vm contract ile hizalandı.
- Doğrulama:
  - `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_descriptor_payload_parse.py tests/test_source_strategy.py tests/test_collector_cache_invalidation.py tests/test_identity_multi_account.py tests/test_popup_vm.py tests/test_popup_vm_fixtures.py tests/test_popup_vm_state_matrix.py` => `38 passed`
  - `python3 tools/project_health_check.py --mode quick` => `13 passed/warned, 0 failed, 0 warnings`

- [x] Codex account identity kaynağını doğrula (`~/.codex/auth.json`) ve provider state'e account-aware metadata ekle
- [x] Account switch detection ekle (önceki account -> yeni account) ve switch anında eski snapshot'ı invalid et
- [x] Token snapshot seçimini cutoff-aware yap: switch öncesi token_count event'lerini dışla
- [x] `collect_codex` davranışını incremental düzelt (mevcut popup-vm / collector kontratını bozmadan)
- [x] Account switch regresyonunu yakalayan testleri ekle (önce test, sonra fix)
- [x] İlgili testleri çalıştır ve sonucu review bölümüne yaz
- [x] Provider/account/source/session identity modelini collector seviyesinde normalize et
- [x] Provider state key'i için fingerprint üret ve metadata/extras içine yaz
- [x] Fingerprint değişiminde stale metrikleri tek çevrim invalidate et
- [x] popup-vm provider çıktısına identity payload ekle
- [x] Claude/Gemini gibi provider'larda account candidate alanlarını enrich et
- [x] Tüm test setini çalıştır ve doğrula
- [x] Cache katmanlarını çıkar (in-memory, polling, CLI/popup-vm, provider/identity store)
- [x] Account fingerprint değişiminde cache invalidation ve stale render engelleme ekle
- [x] UI tarafında identity-change sonrası force refresh ve kısa refreshing state bağla
- [x] Refresh pipeline'ı identity->compare->invalidate->force-refetch->render sırasına getir
- [x] popup-vm payload'ına selected provider identity alanını (`activeIdentity`) ekle
- [x] KDE renderer'da son-render fingerprint mismatch kontrolünü ProviderDetailSection'a bağla
- [x] GNOME renderer'da fingerprint mismatch anında safe switching state göster
- [x] Identity mismatch durumunda eski metrics/extra/cost bloklarının authoritative render'ını engelle
- [x] Popup identity/switching sözleşmesini testlerle kilitle ve tüm testleri çalıştır
- [x] Multi-account provider state modelini ayır (provider-level aktif kimlik + account fingerprint snapshot map)
- [x] Account/session sinyali yoksa explicit identity-missing state üret
- [x] Identity switch anında account snapshot restore veya invalidate/refetch kararını state katmanında ver
- [x] Provider/account state key alanlarını extras içinde yayınla (`providerStateKey`, `accountStateKey`)
- [x] Multi-account davranışını testlerle kilitle (switch-back snapshot restore + identity missing state)
- [x] Multi-account regression test matrisi ekle (switch, stale cache, identity missing, rapid refresh race, session switch, stale UI)
- [x] KDE settings layout/hierarchy düzenlemesi (general/overview/providers section ayrımı)
- [x] KDE provider config kartlarını satır bazlı, compact ve dengeli hale getir
- [x] GNOME prefs group hiyerarşisini ve provider row düzenini ürün seviyesine taşı
- [x] Settings UI düzenini functionality bozmadan doğrula (syntax/test)
- [x] OpenCode tab görünmeme root-cause analizini tamamla (detection vs renderer)
- [x] OpenCode local install detection'ı PATH bağımlılığından çıkar (fallback binary/auth konumları)
- [x] OpenCode auth/local path fallback'lerini güncelle ve regresyon testleri ekle
- [x] İlgili testleri çalıştır ve review notlarını güncelle
- [x] KDE settings ekranında section grouping ve form hizasını rafine et
- [x] General/Overview/Providers bloklarında spacing ritmini compact ve dengeli hale getir
- [x] Provider satırını ortak component+grid yapısına taşı
- [x] Alt aksiyon butonlarını doğal KDE ayar paneli yerleşimine çek
- [x] QML syntax kontrolünü çalıştırıp review notlarını güncelle
- [x] Enable/disable görünürlük mantığını popup-vm tarafında düzelt (enabled => görünür, disabled => gizli)
- [x] Kurulu olmayan ama enabled provider'ları görünür tutarken sıralamada alta al
- [x] Overview kartlarını yalnız kurulu provider'larla sınırla
- [x] Popup VM regresyon testlerini ekle ve tüm testleri çalıştır
- [x] GNOME prefs ekranında section hierarchy ve spacing cleanup uygula
- [x] Overview provider seçim alanını uzun liste yerine kompakt grid seçime çevir
- [x] Provider config satırlarını ortak builder fonksiyonuyla normalize et
- [x] GNOME settings için hafif prefs.css ekle ve gereksiz padding/marginleri azalt
- [x] GNOME settings değişikliklerini doğrula ve review notunu güncelle
- [x] Provider source modelini canonical alanlarla tanımla (preferred/active/available/fallback/auth)
- [x] Collector seviyesinde source model üretimini entegre et
- [x] Popup-vm provider contract'ına source model presentation alanlarını taşı
- [x] KDE ve GNOME popup header'da source details görünürlüğü ekle
- [x] KDE ve GNOME settings provider subtitle'larını source model bazlı gösterime geçir
- [x] Source model regresyon testlerini ekle ve tüm testleri çalıştır
- [x] Provider capability/source strategy/availability modelini canonical alanlarla genişlet
- [x] Descriptor payload'a capability alanlarını ekle ve settings fallback'inde kullan
- [x] popup-vm provider contract'ına capability/strategy/availability map alanlarını taşı
- [x] KDE settings provider row'da capability/strategy/availability görünürlüğünü ekle
- [x] GNOME settings provider row'da capability/strategy/availability görünürlüğünü ekle
- [x] Source capability contract testlerini ekle/güncelle ve ilgili testleri çalıştır
- [x] Settings provider row'larını source-aware bilgi mimarisiyle rafine et (badge + active source + status)
- [x] KDE provider row'da source mode/active source/status chip katmanı ekle
- [x] GNOME provider row'da source mode badge + active source/status özeti ekle
- [x] İlgili syntax ve test doğrulamalarını çalıştır
- [x] Popup-vm'e renderer tüketebileceği sourcePresentation alanını ekle
- [x] Metric unavailable copy'yi source-aware nedenlerle güncelle
- [x] KDE popup header'da source mode/active source/status badge katmanını göster
- [x] GNOME popup header'da source mode/active source/status pill katmanını göster
- [x] Popup source-aware değişiklikleri test/syntax ile doğrula
- [x] Provider descriptor modelini canonical metadata alanlarıyla genişlet (status/usage/sources/policy)
- [x] Collector akışını descriptor-driven hale getir ve fetch strategy katmanını ayır
- [x] Popup URL/status çözümünü descriptor metadata üzerinden çalıştır
- [x] Descriptor refactor sonrası testleri çalıştır ve review notunu güncelle
- [x] Provider fetch strategy arayüzünü tanımla (strategy object + fetcher map)
- [x] Source resolution policy katmanını ekle (preferred/resolved hint/fallback chain/probe)
- [x] Collector içinde source resolution planını üretip source model’e taşı
- [x] popup-vm/settings için source strategy alanlarını canonical contract’a yayınla
- [x] Source strategy regresyon testlerini ekle ve tüm testleri çalıştır
- [x] Enabled providers ve Overview providers ayrımını popup-vm contract’ında explicit hale getir
- [x] KDE/GNOME settings metinlerini enabled vs overview ayrımını net anlatacak şekilde güncelle
- [x] KDE overview seçiminde enabled/detected bağımlılığını kaldır (seçim bağımsızlığı)
- [x] Overview bağımsızlığı için popup-vm testlerini güncelle ve doğrula

## Review

- Canonical local-first policy (CodexBar-style):
  - `source_strategy` artık explicit `preferredSource=local_cli` değerini tanıyor ve aday zincirini local→remote şeklinde üretiyor.
  - `collector` source candidate zincirini attempt ederek ilk authoritative sonucu seçiyor; local başarısızsa aynı cycle’da remote fallback’e geçiyor.
  - `configuredSource` metadata olarak kullanıcı tercihini (`local_cli`) koruyor; `resolvedSource` aktif kaynağı (`cli/api/web`) gösteriyor.
  - `source_model` fallback reason semantiği genişletildi: local-first fallback için `local_unavailable`.
  - popup reason metni source-aware: `Local source unavailable, fallback active`.
- Settings entegrasyonu:
  - KDE/GNOME source seçim dropdown’ları local+remote destekleyen provider’larda `local_cli` opsiyonunu gösteriyor.
  - Strategy metinleri preferred/active source’u daha okunur source tokenlarıyla gösteriyor (`LOCAL CLI`, `API`, `WEB`).
  - `availableSources` görünürlüğü strategy satırında korunuyor.
- Doğrulama:
  - `node --check gnome-extension/aiusagemonitor@aimonitor/prefs.js`
  - `qmllint com.aiusagemonitor/contents/ui/configGeneral.qml`
  - `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_source_strategy.py tests/test_config.py tests/test_collector.py tests/test_popup_vm.py` => `35 passed`
  - `PYTHONPATH=. ./.venv/bin/pytest -q` => `93 passed`

- Source-aware provider state hardening:
  - `source_model.availability` içine `apiConfigured` eklendi; artık canonical alan hem top-level hem availability altında taşınıyor.
  - popup-vm provider payload’ına canonical flat source alanları eklendi:
    - `preferredSource`, `resolvedSource`, `availableSources`, `fallbackReason`,
    - `localToolInstalled`, `apiConfigured`, `authValid`.
  - source-aware status/availability kararları (`API configured` / `API not configured`) `apiConfigured` öncelikli olacak şekilde güncellendi.
  - KDE/GNOME settings `Strategy` satırına `availableSources` bilgisi eklendi, böylece kullanıcı hangi source’ların hazır olduğunu row seviyesinde görebiliyor.
- Doğrulama:
  - `node --check gnome-extension/aiusagemonitor@aimonitor/prefs.js`
  - `qmllint com.aiusagemonitor/contents/ui/configGeneral.qml`
  - `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_popup_vm.py tests/test_collector.py tests/test_source_strategy.py` => `29 passed`
  - `PYTHONPATH=. ./.venv/bin/pytest -q` => `90 passed`

- Pace tracking (popup-vm presentation):
  - Eski durum: `_pace_text` sadece `codex/claude` weekly için çalışıyordu; session pace yoktu, visibility kuralı sınırlıydı.
  - Yeni durum:
    - pace hesaplaması metric-window tabanlı hale getirildi (`label` + reset pencere çözümü),
    - `session` ve `weekly` için secondaryText üretimi presentation katmanında yapılıyor,
    - metin semantiği: `Pace: On pace|X% in deficit|X% in reserve · Lasts until reset|Runs out in ...`,
    - pencere başlangıcı gürültü koruması eklendi (kind-aware minimum elapsed threshold).
  - Renderer etkisi: KDE/GNOME tarafı değişmeden aynı `secondaryText` contract’ını kullanıyor; renderer yeni string üretmüyor.
  - Testler:
    - `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_popup_vm.py` => `17 passed`
    - `PYTHONPATH=. ./.venv/bin/pytest -q` => `90 passed`

- Popup anatomy parity:
  - KDE `ProviderDetailSection.qml` metric render sırası renderer içinde normalize edildi: `session -> weekly -> custom/model`.
  - GNOME `extension.js` için `_orderedMetrics()` eklendi; `buildMetricsSection()` bu sıralamayı zorunlu kullanıyor.
  - Böylece her iki platformda sabit contract korunuyor: `tabs -> header -> session -> weekly -> optional custom/model -> extra -> cost -> actions`.
  - Progress line/spacing/theme tokenları korunarak compact utility popup hissi bozulmadan parity sağlandı.
- Doğrulama:
  - `node --check gnome-extension/aiusagemonitor@aimonitor/extension.js`
  - `qmllint com.aiusagemonitor/contents/ui/ProviderDetailSection.qml com.aiusagemonitor/contents/ui/FullRepresentation.qml`
  - `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_popup_vm.py` => `14 passed`

- Root cause (tabs görünürlüğü): popup top tabs sırası her renderer’da doğrudan `popup.tabs` tüketimine bağlıydı; `enabledProviderIds` contract’ı renderer seviyesinde zorunlu kaynak olarak kullanılmıyordu ve overview tab seçimi de top-row akışına tam bağlı değildi.
- Çözüm:
  - KDE `FullRepresentation.qml`: tabs modeli `enabledProviderIds` bazlı üretime geçirildi; `hasOverview` varsa ayrı overview tab en üste eklendi; overview seçildiğinde `OverviewCardsSection` render ediliyor.
  - GNOME `extension.js`: tabs row `enabledProviderIds` bazlı üretime geçirildi; `hasOverview` varsa overview tab eklendi; overview seçimi `buildOverviewCards()` içeriğine bağlandı.
  - Settings copy (KDE/GNOME): enabled providers’ın normal top popup tabs’i kontrol ettiği, overview seçiminin ise sadece overview cards’ı etkilediği açık yazıldı.
- Doğrulama:
  - `node --check gnome-extension/aiusagemonitor@aimonitor/extension.js`
  - `node --check gnome-extension/aiusagemonitor@aimonitor/prefs.js`
  - `qmllint com.aiusagemonitor/contents/ui/FullRepresentation.qml com.aiusagemonitor/contents/ui/configGeneral.qml`
  - `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_popup_vm.py` => `14 passed`

- Root cause: `collect_codex` sadece provider bazında en yeni `token_count` event'ini okuyordu; active account kimliği (`~/.codex/auth.json`) state key'ine dahil edilmediği için account switch sonrası eski hesabın snapshot'ı yeni hesaba taşınabiliyordu.
- Çözüm: `codex` provider'a account identity/switch takip katmanı eklendi (`~/.cache/ai-usage-monitor/codex_identity_state.json`), switch algılanınca cutoff timestamp belirlenip cutoff öncesi `token_count` event'leri ve local usage hesapları geçersiz sayılıyor.
- State güncellemesi: `ProviderState.extras` artık account-aware alanlar (`accountId`, `accountIdentityKey`, `accountSwitched`, `accountSwitchCutoff`, `authMode`) taşıyor; popup-vm aynı provider seçimini korurken account-specific metrikleri yeniden bağlıyor.
- Yeni identity modeli: collector artık her provider için `providerId + sourceId + accountId + sessionId` bileşiminden fingerprint üretip `metadata.identity` ve `extras.identityFingerprint` alanlarını set ediyor.
- İnvalidation kuralı: fingerprint değişirse (provider sabit kalsa da account/source/session değişmişse) ilk çevrimde metrikler temizleniyor (`primary/secondary/local_usage -> None`, `hasData=false`) ve bir sonraki poll'da yeni identity verisi normal akışta gösteriliyor.
- Cache noktaları:
  - in-memory: GNOME (`_popupVm/_popupProviders`) ve KDE (`popupData`) son payload'ı tutuyor
  - polling cache: GNOME `refresh-interval` timer ve KDE `refreshTimer`
  - CLI result cache: ayrı TTL cache yok, her poll `fetch_all_usage.py popup-vm` ile yeni payload üretiyor
  - provider status cache: ayrı cache yok, provider collector'lar her çağrıda source'dan yeniden çözüyor
  - identity store cache: `provider_identity_state.json` (genel fingerprint geçmişi) + Codex için `codex_identity_state.json` (cutoff)
- Yeni invalidation:
  - collector-level fingerprint değişiminde provider metrikleri/buckets/local usage invalidate
  - popup-vm `identityRefreshPending` sinyali üretir; metric copy `Refreshing account...` olur
  - GNOME/KDE UI bu sinyali görünce 300ms içinde force refresh tetikler
- Yeni refresh pipeline:
  - phase-1: provider collect + identity compare
  - identity değişen provider varsa: phase-2 aynı cycle içinde force re-fetch
  - popup-vm yalnızca phase-2 sonrası state ile üretilir (wrong-data render engellenir)
- Multi-account state ayrımı:
  - `provider_identity_state.json` provider entry'si artık aktif fingerprint + fingerprint->snapshot map (`snapshots`) tutuyor
  - snapshot key doğrudan identity fingerprint (`providerId+sourceId+accountId+sessionId`) olduğu için aynı provider altında account A/B ayrılıyor
  - switch anında yeni fingerprint için snapshot varsa restore edilir (`restoredFromSnapshot=true`) ve gereksiz force-refetch atlanır
  - snapshot yoksa invalidate + force-refetch akışı korunur
  - account/session sinyali yoksa `identity.known=false`, `identity.scope=provider`, `identity.confidence=low` açıkça işaretlenir ve account snapshot kullanılmaz
- Renderer güvenlik katmanı:
  - popup-vm artık `popup.activeIdentity` + `popup.activeIdentityFingerprint` taşıyor
  - KDE/GNOME renderer son render fingerprint ile yeni VM fingerprint'i karşılaştırıyor
  - mismatch anında metrics/extra/cost geçici olarak gizlenip VM kaynaklı `switchingState` ara durumu gösteriliyor
  - takip eden hızlı refresh sonrası fingerprint stabil ise tam render geri geliyor
- Settings UI revizyonu:
  - KDE `configGeneral.qml` üç net yüzeye ayrıldı: `General`, `Overview`, `Providers`
  - Provider yönetimi kartlarında icon + title/subtitle + configure + enabled switch dengeli satır düzenine alındı
  - Expand içeriği daha form-benzeri hale getirildi (source satırı + field label/input istifi)
  - GNOME `prefs.js` tarafında group hiyerarşisi netleştirildi ve provider expander header'larına icon + configure + enabled eklendi
- Doğrulama:
  - `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_codex_normalization.py` => `5 passed`
  - `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_local_usage.py` => `4 passed`
  - `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_collector.py` => `8 passed`
  - `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_popup_vm.py` => `9 passed`
  - `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_identity_multi_account.py` => `4 passed`
  - `PYTHONPATH=. ./.venv/bin/pytest -q` => `71 passed`
- Tabs görünmeme ek root cause:
  - `opencode`/`kiro-cli` install detection GNOME/KDE süreç PATH'ine bağımlıydı (`shutil.which`); kullanıcı kabuğunda kurulu binary shell PATH'inde olsa bile extension ortamında görünmeyebildi.
  - `opencode` auth/local usage path'i sadece `~/.local/share/opencode` kabul ediyordu; bazı kurulumlarda `~/.config/opencode` kullanıldığı için local identity/usage bulunamayıp provider `installed=false` düşebiliyordu.
- Tabs görünmeme ek çözüm:
  - Ortak CLI binary resolver eklendi (`core.ai_usage_monitor.cli_detect.resolve_cli_binary`) ve kullanıcı bin fallback dizinleri ile env override desteklendi.
  - `opencode` ve `kiro` provider'ları resolver'a geçirildi.
  - `opencode` auth + local usage scan `~/.config/opencode` fallback'iyle genişletildi.
- Ek doğrulama:
  - `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_cli_detect.py tests/test_opencode_provider.py tests/test_kiro_provider.py tests/test_local_usage.py` => `17 passed`
  - `PYTHONPATH=. ./.venv/bin/pytest -q` => `78 passed`
- KDE settings UI cleanup:
  - `General` section label/control hizası sabit form label sütunu ile normalize edildi; `Display style` radio grubu flow düzenine alındı.
  - `Providers` listesi tek tip satır bileşenine taşındı (`SettingsProviderRow.qml`), böylece icon/title-subtitle/configure/enabled kolonları tüm satırlarda aynı grid hizasına geçti.
  - Provider expand alanındaki source/config field satırları 2 kolon grid ile hizalandı, vertical rhythm sıkılaştırıldı.
  - Alt buton barı sadeleştirildi ve doğal settings footer akışına çekildi.
- Son doğrulama:
  - `qmllint com.aiusagemonitor/contents/ui/configGeneral.qml com.aiusagemonitor/contents/ui/SettingsProviderRow.qml` => hata yok
  - `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_config.py tests/test_cli_config.py` => `9 passed`
- Enable/disable görünürlük düzeltmesi:
  - Root cause: popup-vm `visible providers` filtresi `enabled && installed` idi; bu yüzden settings'te enable edilen ama detection tarafında `installed=false` kalan provider tab'a hiç düşmüyordu.
  - Çözüm: popup görünürlüğü `enabled` bazına çekildi, `installed=false` provider'lar sıralamada alta alındı.
  - Overview kartları gürültü üretmemesi için kurulu provider'larla sınırlandı.
- Ek doğrulama:
  - `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_popup_vm.py tests/test_collector.py tests/test_config.py` => `22 passed`
  - `PYTHONPATH=. ./.venv/bin/pytest -q` => `80 passed`
- GNOME settings UI cleanup:
  - `prefs.js` section yapısı sadeleştirildi: `General settings`, `Overview providers`, `Shared provider config`, `Actions`.
  - General kontrolleri (refresh/panel tool/display style) tek grupta ve compact row class ile hizalandı.
  - Overview seçim alanı `SwitchRow` uzun akışından çıkarılıp 2/3 kolonlu kompakt check grid'e taşındı.
  - Provider satırları ortak builder (`createProviderConfigExpander`) ile standardize edildi; icon + configure + enabled + field rows aynı ritimde render ediliyor.
  - Alt aksiyon alanı `Reload shared settings` action row ile net bir footer group'a taşındı.
  - Settings'e özel `prefs.css` eklendi; yalnız spacing/padding margin kompaktlaştırması yapıldı.
- GNOME settings doğrulama:
  - `node --check gnome-extension/aiusagemonitor@aimonitor/prefs.js` => syntax ok
  - `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_config.py tests/test_cli_config.py` => `9 passed`
- Source model (local-first/api/hybrid/unavailable) güncellemesi:
  - `core.ai_usage_monitor.source_model` eklendi ve canonical alanlar üretildi:
    - `preferredSource`, `activeSource`, `availableSources`
    - `fallbackState`
    - `sourceLabel`, `sourceDetails`
    - `authState`, `localToolDetected`, `apiConfigured`
    - `canonicalMode` (`local_cli|api|hybrid|unavailable`)
  - Collector `_collect_provider` içinde her provider için `provider.source_model` ve `metadata.sourceModel` set ediliyor.
  - `ProviderState.to_dict()` artık `sourceModel` yayımlıyor.
  - Popup-vm provider çıktısına `sourceModel`, `sourceLabel`, `sourceDetails`, `authState`, `fallbackState` eklendi.
  - Popup subtitle artık backend source label ile üretiliyor (renderer string üretmiyor).
  - KDE popup header `sourceDetails` satırı eklendi.
  - GNOME popup header `sourceDetails` satırı eklendi.
  - KDE/GNOME settings provider subtitle alanları source model'den beslenecek şekilde güncellendi.
- Source model doğrulama:
  - `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_collector.py tests/test_popup_vm.py tests/test_models.py` => `22 passed`
  - `PYTHONPATH=. ./.venv/bin/pytest -q` => `82 passed`
  - `node --check gnome-extension/aiusagemonitor@aimonitor/prefs.js`
  - `node --check gnome-extension/aiusagemonitor@aimonitor/extension.js`
  - `qmllint com.aiusagemonitor/contents/ui/PopupHeader.qml com.aiusagemonitor/contents/ui/configGeneral.qml com.aiusagemonitor/contents/ui/SettingsProviderRow.qml`
- Provider capability/source strategy genişletmesi:
  - `sourceModel` artık üç açık blok taşıyor:
    - `providerCapabilities`: `supportsLocalCli`, `supportsApi`, `supportsWeb`
    - `sourceStrategy`: `preferredSource`, `resolvedSource`, `fallbackReason`, `resolutionReason`
    - `availability`: `localToolInstalled`, `apiKeyPresent`, `authValid`, `rateLimitState`
  - Descriptor payload'a `providerCapabilities` eklendi; settings tarafında live state yokken fallback olarak kullanılıyor.
  - popup-vm provider contract'ına `providerCapabilities`, `sourceStrategy`, `availability` top-level mapleri eklendi.
  - KDE settings provider row artık `Capabilities`, `Strategy`, `Availability` bilgisini hem satırda hem expand içinde gösteriyor.
  - GNOME settings provider expander içine aynı üç bilgi bloğu eklendi.
  - Doğrulama:
    - `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_collector.py tests/test_popup_vm.py tests/test_cli_config.py` => `27 passed`
    - `PYTHONPATH=. ./.venv/bin/pytest -q` => `82 passed`
    - `node --check gnome-extension/aiusagemonitor@aimonitor/prefs.js`
    - `qmllint com.aiusagemonitor/contents/ui/configGeneral.qml com.aiusagemonitor/contents/ui/SettingsProviderRow.qml`
- Source-aware settings row revizyonu:
  - KDE `SettingsProviderRow` satırı source hiyerarşisine geçirildi:
    - title yanında source mode badge
    - ayrı active source chip
    - status chip listesi (`CLI detected/missing`, `API configured/missing`, `fallback active`, `auth required`, `unavailable`)
    - configure + enabled state korunuyor
  - KDE expand alanına `Why this source` satırı eklendi; source çözüm sebebi sade metinle gösteriliyor.
  - GNOME provider expander başlığı source-aware subtitle'a geçirildi (`mode · active · status`).
  - GNOME satırına source mode badge suffix eklendi.
  - GNOME expand alanına `Status` + `Why this source` satırları eklendi.
  - Doğrulama:
    - `qmllint com.aiusagemonitor/contents/ui/configGeneral.qml com.aiusagemonitor/contents/ui/SettingsProviderRow.qml`
    - `node --check gnome-extension/aiusagemonitor@aimonitor/prefs.js`
    - `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_collector.py tests/test_popup_vm.py tests/test_cli_config.py` => `27 passed`
    - `PYTHONPATH=. ./.venv/bin/pytest -q` => `82 passed`
- Popup source-awareness revizyonu:
  - popup-vm provider contract'ına `sourcePresentation` eklendi:
    - `modeLabel`
    - `activeSourceLabel`
    - `statusTags`
    - `reasonText`
    - `unavailableReason` (`code`, `text`)
  - Missing metrics copy source-aware yapıldı (`CLI not installed`, `API not configured`, `Auth invalid`, `Local usage unavailable`, `Source switched`).
  - Switching-state metni source semantiğine çekildi (`Source switched`, `Refreshing usage for active source`).
  - KDE `PopupHeader.qml` source badge/chip satırı + source reason render edecek şekilde güncellendi.
  - GNOME `extension.js` + `stylesheet.css` header source pill satırı ve source reason render edecek şekilde güncellendi.
  - Doğrulama:
    - `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_popup_vm.py` => `13 passed`
    - `PYTHONPATH=. ./.venv/bin/pytest -q` => `83 passed`
    - `qmllint com.aiusagemonitor/contents/ui/PopupHeader.qml`
    - `node --check gnome-extension/aiusagemonitor@aimonitor/extension.js`
- Descriptor-driven provider refactor:
  - `ProviderDescriptor` modeline canonical metadata alanları eklendi:
    - `settings_available`
    - `status_page_url`
    - `usage_dashboard_default_url`
    - `usage_dashboard_by_source`
    - `preferred_source_policy`
  - Descriptor payload artık canonical UI alanlarını yayınlıyor:
    - `iconKey`, `settingsAvailability`, `statusPageUrl`, `usageDashboardUrl`, `usageDashboardBySource`
    - `supportedSources`, `preferredSourcePolicy`
  - Fetch katmanı ayrıştırıldı:
    - yeni `core.ai_usage_monitor.providers.fetch_strategies` modülü ile provider fetch mapping tek yerde toplandı
    - collector descriptor listesini iterate ediyor, fetch strategy’yi ayrı katmandan alıyor
  - Popup URL/status çözümü descriptor metadata’ya taşındı:
    - usage dashboard URL seçimi descriptor by-source mapping üzerinden
    - status page URL descriptor alanından
    - geçiş dönemi için yalnız OpenCode workspace billing linki dinamik özel durum olarak bırakıldı
  - Source model policy hizalaması:
    - `preferred_source_policy` source-model üretiminde dikkate alınıyor
    - `sourceStrategy.policy` ve `preferredSourcePolicy` alanları yayınlanıyor
  - Doğrulama:
    - `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_cli_config.py tests/test_collector.py tests/test_popup_vm.py` => `28 passed`
    - `PYTHONPATH=. ./.venv/bin/pytest -q` => `83 passed`
    - `python3 -m py_compile core/ai_usage_monitor/providers/base.py core/ai_usage_monitor/providers/registry.py core/ai_usage_monitor/providers/fetch_strategies.py core/ai_usage_monitor/collector.py core/ai_usage_monitor/source_model.py core/ai_usage_monitor/presentation/popup_vm.py`
- CodexBar-style fetch strategy + source resolution:
  - Yeni `source_strategy` katmanı eklendi:
    - `resolve_provider_source_plan` ile `preferredSource`, `resolvedSourceHint`, `fallbackChain`, `supportsProbe`, `resolutionReason`, `candidates` üretiliyor.
    - Source türleri canonical hale getiriliyor (`local_cli`, `api`, `web`, `oauth`, `probe`).
  - Yeni fetch strategy arayüzü:
    - `ProviderFetchStrategy` (strategy object) + `fetcher_map` eklendi.
    - Collector descriptor-driven akışta fetcher + source strategy planı birlikte kullanıyor.
  - Canonical source alanları:
    - `sourceModel.sourceStrategy` artık `policy`, `supportsProbe`, `fallbackChain`, `candidates` içeriyor.
    - `preferredSource` / `resolvedSource` alanları provider başına canonical kaldı.
  - Visibility/debug:
    - `metadata.sourceResolutionPlan` ve `metadata.fetchStrategy` ile fallback/auth/config analizi görünür.
    - popup-vm ve settings sözleşmesi source-model alanlarını tüketmeye devam ediyor.
  - Doğrulama:
    - `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_source_strategy.py tests/test_cli_config.py tests/test_collector.py tests/test_popup_vm.py` => `31 passed`
    - `PYTHONPATH=. ./.venv/bin/pytest -q` => `86 passed`
    - `python3 -m py_compile core/ai_usage_monitor/source_strategy.py core/ai_usage_monitor/providers/fetch_strategies.py core/ai_usage_monitor/collector.py core/ai_usage_monitor/source_model.py core/ai_usage_monitor/providers/registry.py core/ai_usage_monitor/providers/base.py`
- Enabled vs Overview ayrımı:
  - Yeni kavramsal contract popup-vm içinde açıklandı:
    - `enabledProviderIds`: normal provider tablarını belirler
    - `overviewProviderIds`: overview kartları için kullanıcı seçimi
    - `overviewCardProviderIds`: gerçekten render edilen overview kartları
    - `overviewSelectionIndependent`: bu iki kavramın bağımsız olduğunu açık işaretler
  - `hasOverview` artık overview seçimine bağlı (kart varlığına değil), böylece kavramlar net ayrıştı.
  - Overview kart üretimi `enabled provider` listesinden değil `overviewProviderIds` + tüm provider state’ten türetiliyor.
  - KDE settings:
    - Overview seçiminde enabled/detected kilidi kaldırıldı.
    - Açıklama metni güncellendi: overview seçimi normal provider tabs görünürlüğünü kontrol etmez.
  - GNOME settings:
    - Overview group/hint ve shared provider config açıklamaları aynı ayrımı net anlatacak şekilde güncellendi.
  - Doğrulama:
    - `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_popup_vm.py tests/test_cli_config.py tests/test_collector.py` => `29 passed`
    - `PYTHONPATH=. ./.venv/bin/pytest -q` => `87 passed`
    - `qmllint com.aiusagemonitor/contents/ui/configGeneral.qml`
    - `node --check gnome-extension/aiusagemonitor@aimonitor/prefs.js`

## 2026-03-07 - Provider+Account+Source State Key

- [x] `identity.py` içinde canonical state identity modelini `providerId + accountFingerprint + sourceMode` olarak tanımla
- [x] Snapshot cache key'lerini `stateKey` üstüne taşı ve restore/invalidation akışını güncelle
- [x] Account/source switch sinyallerini (`accountChanged`, `sourceChanged`) identity payload + extras'a ekle
- [x] popup-vm provider contract'ına `accountFingerprint`, `sourceMode`, `stateIdentityKey` alanlarını ekle
- [x] Regression testlerini source/account switch ve popup-vm alanları için güncelle
- [x] Testleri çalıştır ve doğrula

### Review

- Root fix: identity fingerprint artık provider-level tek anahtar değil; state anahtarı provider+account+source üçlüsünden türetiliyor.
- Cache policy: `snapshots` map'i artık `stateKey` ile tutuluyor, önceki account/source snapshot'ı yeni kimlikte authoritative kabul edilmiyor.
- Refresh sonucu: identity değişimi restore edilmezse metricler invalid ediliyor ve bir sonraki fetch cycle yeni identity ile bağlanıyor.
- Doğrulama:
  - `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_identity_multi_account.py tests/test_popup_vm.py tests/test_collector.py` => `32 passed`
  - `PYTHONPATH=. ./.venv/bin/pytest -q` => `94 passed`

## 2026-03-07 - Reliable Account/Source Switch Refresh

- [x] Refresh pipeline'ı fingerprint switch durumunda zorunlu 2. faz refetch yapacak şekilde güncelle
- [x] popup-vm switching state'ini account/source ayrımını taşıyacak şekilde genişlet
- [x] KDE/GNOME renderer’da mismatch map kaynaklı yanlış/boş switching render riskini kaldır
- [x] Switching metric copy’sini popup-vm’den üret ve 0% fallback kullanmadan loading state göster
- [x] Collector + popup-vm testlerini yeni lifecycle’a göre güncelle
- [x] Full test + UI syntax doğrulamasını çalıştır

### Review

- Collector artık `identity_switched` durumunda da force refetch yapıyor; böylece fingerprint değiştiğinde usage ikinci fazda yeniden resolve ediliyor.
- popup-vm `switchingState` artık `kind` + account/source-specific title/message taşıyor:
  - `account`
  - `source`
  - `account_source`
  - `identity` (fallback)
- KDE ve GNOME detay render’ı switching kararı için `provider.switchingState.active` kullanıyor; mismatch map sadece refresh tetikleyicisi olarak kaldı.
- Doğrulama:
  - `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_collector.py tests/test_popup_vm.py tests/test_identity_multi_account.py` => `33 passed`
  - `PYTHONPATH=. ./.venv/bin/pytest -q` => `95 passed`
  - `node --check gnome-extension/aiusagemonitor@aimonitor/extension.js`
  - `qmllint com.aiusagemonitor/contents/ui/FullRepresentation.qml com.aiusagemonitor/contents/ui/ProviderDetailSection.qml`

## 2026-03-07 - Settings Section Reorganization (KDE + GNOME)

- [x] Settings bilgi mimarisini `General / Overview / Providers / Footer actions` yapısına hizala
- [x] KDE settings'te footer action butonlarını provider bölümünden ayırıp ayrı section'a taşı
- [x] Provider row contract'ını `preferred source + active source + source status + configure + enabled` görünürlüğüyle güçlendir
- [x] GNOME provider expander satırında source badge katmanını (mode/preferred/active/status) görünür hale getir
- [x] Overview açıklama metnini normal enabled tabs'ten bağımsızlık vurgusuyla düzelt
- [x] Syntax ve regresyon doğrulamalarını çalıştır

### Review

- KDE:
  - `configGeneral.qml` içinde `Footer actions` ayrı `GroupBox` olarak eklendi.
  - `Providers` section copy daha net hale getirildi.
  - `SettingsProviderRow` satırına `preferredSourceLabel` chip'i eklendi.
- GNOME:
  - Group başlıkları istenen yapıya çekildi (`General`, `Overview`, `Providers`, `Footer actions`).
  - `Panel tool` satır etiketi güncellendi.
  - Provider row suffix alanına `preferred`, `active`, `status` source badge'leri eklendi.
  - Overview açıklaması enabled tabs ile ayrımı net anlatacak şekilde güncellendi.
- Doğrulama:
  - `node --check gnome-extension/aiusagemonitor@aimonitor/prefs.js`
  - `qmllint com.aiusagemonitor/contents/ui/configGeneral.qml com.aiusagemonitor/contents/ui/SettingsProviderRow.qml`
  - `PYTHONPATH=. ./.venv/bin/pytest -q` => `95 passed`

## 2026-03-07 - Source-Aware Provider Product Rows

- [x] KDE provider row’da source-aware satır contract’ını netleştir (name/subtitle/enabled/preferred/active/status/configure)
- [x] KDE status görünümünü küçük, okunabilir tek satır status text’e indir
- [x] GNOME provider expander row’da full-name + short subtitle + preferred/active/status/source-mode + enabled/configure hizasını düzenle
- [x] Overview/Providers copy’lerini source-aware product panel semantiğiyle uyumlu tut
- [x] Syntax ve test doğrulamasını çalıştır

### Review

- KDE:
  - Provider adı full display name’e çekildi.
  - `preferred source` chip’i + `active source` chip’i korunup `status` küçük tek satıra alındı.
  - Subtitle daha kısa/product tonuna çekildi (`<mode> · ready|needs attention|unavailable`).
- GNOME:
  - Provider title full name oldu.
  - Row suffix’te source mode + preferred + active + status badge korunarak hızlı tarama sağlandı.
  - Enabled state için text label (`Enabled/Disabled`) switch yanında görünür hale getirildi.
  - Subtitle debug detayı yerine kısa product subtitle oldu.
- Doğrulama:
  - `qmllint com.aiusagemonitor/contents/ui/configGeneral.qml com.aiusagemonitor/contents/ui/SettingsProviderRow.qml`
  - `node --check gnome-extension/aiusagemonitor@aimonitor/prefs.js`
  - `PYTHONPATH=. ./.venv/bin/pytest -q` => `95 passed`

## 2026-03-07 - Popup Header Source-Awareness

- [x] popup-vm source presentation etiketlerini canonical hale getir (`Local CLI / API / Hybrid / Fallback / Unavailable`)
- [x] Header badge/subtitle tarafında mevcut sourcePresentation contract’ı ile aynı semantiği koru (KDE/GNOME)
- [x] Source reason metinlerini kısa ve anlamlı hale getir (fallback / unavailable / auto)
- [x] Missing-data/error-state reason metinlerinin source-aware kalmasını doğrula
- [x] popup-vm regresyon testlerini güncelle ve doğrula

### Review

- `core/ai_usage_monitor/presentation/popup_vm.py`:
  - `activeSourceLabel` artık renderer’dan bağımsız canonical değer üretiyor.
  - Fallback/unavailable durumları badge seviyesinde açık görünüyor.
  - Source reason metinleri kısaltıldı ve popup yoğunluğu azaltıldı.
  - Provider subtitle source tekrarından arındırıldı (header badge + reason ana kaynak oldu).
- Doğrulama:
  - `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_popup_vm.py` => `19 passed`
  - `PYTHONPATH=. ./.venv/bin/pytest -q` => `96 passed`
  - `node --check gnome-extension/aiusagemonitor@aimonitor/extension.js`
  - `qmllint com.aiusagemonitor/contents/ui/PopupHeader.qml`

## 2026-03-07 - Provider Status/Incident Polling in Popup VM + UI

- [x] Provider status page URL çözümünü provider state/popup-vm contract’ında canonical hale getir
- [x] Incident bilgisini provider state’e taşı ve source sorunlarından ayrı modelle
- [x] `stale` / `refresh failed` / `incident` durumlarını popup-vm içinde ayrıştır
- [x] KDE popup header’da source satırından bağımsız provider status badge/details göster
- [x] GNOME popup header’da source satırından bağımsız provider status pill/details göster
- [x] Compact indicator’da incident tonu (warn/error) gösterimini ekle
- [x] popup-vm + full test suite + syntax doğrulamalarını çalıştır

### Review

- Root cause:
  - `build_popup_view_model` içinde status patch’ten kalan hatalı satır (`effective_status_url = status_state...`) undefined değişken nedeniyle kırılma üretiyordu.
  - Incident default’u `unknown` kaldığı için incident verisi olmayan provider’larda yanlışlıkla `incidentActive=true` hesaplanıyordu.
- Çözüm:
  - Hatalı top-level satır kaldırıldı.
  - Incident default davranışı düzeltildi: incident payload yoksa indicator `none`, payload var ama indicator yoksa `unknown`.
  - popup-vm provider contract’ı `statusState` + `statusPresentation` ile incident/sources ayrımını koruyacak şekilde finalize edildi.
  - KDE/GNOME header tarafında source ve provider-status ayrı katmanlar olarak gösterildi; compact indicator incident tonunu tüketiyor.
- Doğrulama:
  - `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_popup_vm.py` => `21 passed`
  - `PYTHONPATH=. ./.venv/bin/pytest -q` => `98 passed`
  - `node --check gnome-extension/aiusagemonitor@aimonitor/extension.js`
  - `qmllint com.aiusagemonitor/contents/ui/PopupHeader.qml com.aiusagemonitor/contents/ui/CompactRepresentation.qml`

## 2026-03-07 - Parity Hardening (KDE + GNOME)

- [x] KDE selected provider identity mismatch anında force switching state render’ını etkinleştir
- [x] KDE switching state fallback title/message ekleyip boş ara durum riskini kaldır
- [x] GNOME enabled-provider tab görünürlüğünü tab payload eksik olsa da provider payload ile fallback çalışacak şekilde sertleştir
- [x] GNOME provider tab fallback mini-metric/icon/badge üretimini ekle
- [x] GNOME identity mismatch durumunda provider detail’i switching state ile güvene al
- [x] KDE settings provider row’da source reason satırını compact secondary text olarak görünür kıl
- [x] KDE/GNOME popup header source reason satırını compact tek satır ellide davranışına hizala
- [x] Syntax ve full test doğrulamasını çalıştır

### Review

- `enabled vs overview` ayrımı contract düzeyinde korunurken GNOME’da tab payload eksikliği yüzünden görünürlük kaybı oluşabilecek nokta fallback ile kapatıldı.
- `account/source switch` güvenliği iki renderer’da da güçlendirildi:
  - KDE: identity mismatch artık `forceSwitchingState` ile detay render’ı güvenli ara duruma alıyor.
  - GNOME: identity mismatch doğrudan switching state tetikliyor ve fallback metinle boş blok oluşmuyor.
- Source-aware settings row parity için KDE provider satırına kısa `sourceReasonText` eklendi.
- Popup header source reason satırı KDE/GNOME’da tek satır-ellide davranışına çekildi; compact utility hissi korundu.
- Doğrulama:
  - `node --check gnome-extension/aiusagemonitor@aimonitor/extension.js`
  - `qmllint com.aiusagemonitor/contents/ui/FullRepresentation.qml com.aiusagemonitor/contents/ui/ProviderDetailSection.qml com.aiusagemonitor/contents/ui/SettingsProviderRow.qml`
  - `PYTHONPATH=. ./.venv/bin/pytest -q` => `98 passed`

## 2026-03-07 - Project Health Hardening (Incremental)

- [x] Hardening planını kalite-kapıları -> cleanup -> regression sırasında netleştir
- [x] JS syntax gate’de `.pragma library` false-positive durumunu düzelt
- [x] Shell script quality gate ihlallerini düzelt (`SC2181`)
- [x] Type-ish signature gate ekle (core public contract fonksiyonları)
- [x] Python function complexity gate ekle (max function line budget)
- [x] Health contract sabitlerini shared module’a taşı (tool/test drift önleme)
- [x] Popup VM için fixture tabanlı contract projection testi ekle
- [x] Doğrulama komutlarını çalıştır ve sonuçları kaydet

### Review

- Quality gates:
  - `tools/project_health_check.py` artık QML `.pragma` içeren JS dosyaları sanitize ederek `node --check` çalıştırıyor; yanlış syntax fail engellendi.
  - `typeish-signatures` kapısı eklendi: core sınırındaki kritik fonksiyonların arg/return annotation’ları zorunlu.
  - `function-budgets` kapısı eklendi: büyük core dosyalarında fonksiyon seviyesinde satır bütçesi ile complexity drift engelleniyor.
- Cleanup:
  - Health contract sabitleri `tools/project_health_contracts.py` dosyasına taşındı.
  - `tools/project_health_check.py` ve `tests/test_project_health_contracts.py` artık aynı contract kaynağını kullanıyor.
- Regression:
  - `tests/fixtures/popup_vm_contract_projection.json` ve `tests/test_popup_vm_fixtures.py` eklendi.
  - Fixture test, popup VM’de tab/provider/switching/action contract’ını projection seviyesinde kilitliyor.
- Script fixes:
  - `com.aiusagemonitor/install.sh` ve `com.aiusagemonitor/upgrade.sh` dosyalarında shellcheck uyumlu doğrudan command-check yapıldı.
- Doğrulama:
  - `python3 tools/project_health_check.py --mode quick` => `0 failed`
  - `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_project_health_contracts.py tests/test_popup_vm_fixtures.py` => `5 passed`
  - `PYTHONPATH=. ./.venv/bin/pytest -q tests/test_popup_vm.py` => `21 passed`

## 2026-03-07 - Base Quality Gates (Python + KDE/QML + GNOME/GJS)

- [x] Root `package.json` ekle (`check/lint/format/test` script komutları)
- [x] GNOME/GJS için ESLint yapılandırmasını ekle (`.eslintrc.cjs`)
- [x] Health check pipeline’a `gjs-lint` kapısı ekle
- [x] `tools/project_health_check.py` içinde `.venv` tool çözümleme desteği ekle
- [x] Makefile’a ortak komutları ekle (`check/lint/format/format-check/test/typecheck`)
- [x] CI workflow’a Node dependency kurulumu (`npm ci`) ekle
- [x] Pre-commit hook’u `.venv` Python ile sabitle
- [x] README’a kalite kapıları çalıştırma adımlarını ekle
- [x] Yeni kalite kapılarını komutlarla doğrula

### Review

- Eklenen konfigurasyonlar:
  - `package.json`: ortak script komutları + `eslint` devDependency
  - `.eslintrc.cjs`: GNOME JS lint kuralları
- Health gate güncellemeleri:
  - `gjs-lint` kapısı (ESLint)
  - Tool resolver: `.venv/bin` + `node_modules/.bin` fallback
  - Python syntax/lint/test komutları `.venv` ile çalışabilecek hale getirildi
- CI/pre-commit:
  - `.github/workflows/quality-gates.yml` Node deps kuruyor ve health check koşuyor
  - `.pre-commit-config.yaml` hook entry `.venv` Python’a taşındı
- Doğrulama:
  - `python3 tools/project_health_check.py --mode quick` => `0 failed`
  - `npm run lint:gjs` => `PASS`
  - `npm run check` => `PASS` (`ruff-format` drift şu an `WARN`)
  - `npm run test` => `103 passed`
  - `./.venv/bin/pre-commit run --all-files` => `PASS`

## 2026-03-07 - KDE Plasmoid Health Hardening (QML-only)

- [x] KDE için `qmllint` entegrasyonunu net script/config ile sağlamlaştır
- [x] `main.qml` lifecycle güvenliğini artır (timer/runner cleanup, command overlap guard)
- [x] `FullRepresentation.qml` içindeki tab model/policy hesaplarını yardımcı modüle ayır
- [x] `configGeneral.qml` içindeki source/presentation helper yığınını modüle ayır
- [x] Popup QML bileşenlerinde hardcoded spacing/shape kararlarını `PopupTokens` üzerinden merkezileştir
- [x] `qmllint` çalıştır, anti-pattern/syntax durumunu doğrula ve değişen dosyaları raporla

### Review

- `qmllint` entegrasyonu:
  - `tools/run_qmllint.sh` eklendi (repo kökünden deterministik `qmllint` çağrısı).
  - `tools/qmllint_targets.txt` eklendi (KDE QML lint kapsamı).
  - `tools/project_health_check.py` `qml-syntax` adımı bu runner üzerinden çalışacak şekilde güncellendi.
  - `package.json` içine `lint:qml`, `Makefile` içine `lint-qml` komutu eklendi.
- Lifecycle risk azaltımları:
  - `main.qml`: `activeRunnerCommand` + `disconnectRunnerSources()` ile command overlap temizlendi.
  - `main.qml`: `Component.onDestruction` ile timer ve runner kaynakları explicit temizleniyor.
  - `configGeneral.qml`: `stateFetchInFlight` non-state komutlarda ve disconnect akışında güvenli sıfırlanıyor.
  - `configGeneral.qml`: `Component.onDestruction` ile pending command/state cleanup eklendi.
- Component/boundary cleanup:
  - `FullRepresentation.qml` tab policy hesapları `PopupTabModel.js` içine taşındı.
  - `configGeneral.qml` source/presentation helper hesapları `ConfigPresentation.js` içine taşındı.
  - `configGeneral.qml` 995 satırdan 845 satıra indi.
  - `FullRepresentation.qml` 323 satırdan 172 satıra indi.
- Token merkezileştirme:
  - `PopupTokens.qml` yeni tokenlar: chip ölçüleri, action padding/icon, divider, mini-line kalınlığı, metric gap.
  - `PopupHeader.qml`, `ProviderTabsRow.qml`, `MetricRow.qml`, `CostSection.qml`, `ActionRow.qml`, `SectionDivider.qml` bu tokenlara geçirildi.
- Action list boundary sadeleştirme:
  - `ActionList.qml` içindeki görünürlük filtresi kaldırıldı; filtreleme tek kaynağa (`ActionDispatcher`) bırakıldı.
- Doğrulama:
  - `tools/run_qmllint.sh` => `PASS`
  - `python3 tools/project_health_check.py --mode quick` => `0 failed` (`ruff-format` mevcut repo drift nedeniyle `WARN`)

## 2026-03-07 - Function Budget Gate Cleanup

- [x] `collect_all()` fonksiyonunu küçük yardımcı adımlara böl
- [x] `apply_identity_to_provider()` fonksiyonunu behavior koruyarak yardımcı fonksiyonlara ayır
- [x] `_provider_vm()` fonksiyonunda metric/error derleme bloklarını ayrıştır
- [x] `project_health_check --mode quick` ile `function-budgets` kapısını tekrar doğrula
- [x] collector/identity/popup VM test subset’ini çalıştır

### Review

- `function-budgets` fail nedenleri (popup_vm/collector/identity) helper extraction ile çözüldü.
- Kalite kapıları: `python3 tools/project_health_check.py --mode quick` => `0 failed, 0 warnings`.
- Regresyon kontrolü: `tests/test_collector.py`, `tests/test_identity_multi_account.py`, `tests/test_popup_vm.py` => `36 passed`.

## 2026-03-07 - GNOME/GTK Extension Health Hardening (Renderer-only)

- [x] ESLint konfigürasyonunu GNOME GJS için sıkılaştır
- [x] Mümkün olan noktada JSDoc/type-aware lint kontrolü ekle
- [x] `extension.js` lifecycle güvenliğini artır (signal/timeout/cancellable cleanup)
- [x] Popup tab selection/policy akışını modüle ayır (monolit azalt)
- [x] Header/detail builder fonksiyonlarını net küçük parçalara böl
- [x] CSS sınıf adlarını builder/component sınırlarıyla hizala (geriye uyumlu)
- [x] Lint + health check çalıştır ve lifecycle risk listesini belgeleyerek raporla

### Review

- ESLint/JSDoc:
  - `.eslintrc.cjs` `jsdoc` plugin + `jsdoc/check-types`, `jsdoc/valid-types` kuralları eklendi.
  - `popupSelection.js` için public function JSDoc/type zorunluluğu eklendi.
  - `package.json` `lint:gjs` hedefi `popupSelection.js` içerecek şekilde güncellendi.
- Lifecycle cleanup:
  - `extension.js` refresh akışına `refreshGeneration` guard eklendi; stale async response overwrite riski azaltıldı.
  - Teardown-safe koruma eklendi (`_destroyed`, `_finalizeRefreshRequest`, `_disconnectSignal`).
  - `menu`/`panel ring` long-lived signal id’leri explicit track+disconnect ediliyor.
  - `refresh-interval` güvenli alt limit (`Math.max(20, ...)`) eklendi.
  - `destroy()` içinde active subprocess force-exit ve timeout temizliği standartlaştırıldı.
- Modüler builder/policy:
  - `popupSelection.js` ile tab/provider selection-policy modüle ayrıldı.
  - `extension.js` tab/panel tone kararları bu modüle delegasyonla sadeleştirildi.
  - Header ve provider-detail builder akışı küçük yardımcı fonksiyonlara bölündü.
- CSS hizalama:
  - `stylesheet.css` içinde yeni builder alias class’ları eklendi (`ai-usage-tabs-row`, `ai-usage-tab-button`, `ai-usage-provider-header*`).
  - Eski class adları korunarak geriye uyumluluk sürdürüldü.
- Doğrulama:
  - `npm run lint:gjs` => `PASS`
  - `python3 tools/project_health_check.py --mode quick` => `0 failed, 0 warnings`

## 2026-03-07 - Renderer Lifecycle / Memory First Cleanup

- [x] KDE lifecycle checklist oluştur
- [x] GNOME lifecycle checklist oluştur
- [x] Kodda ilk tur lifecycle risklerini tespit et
- [x] Düşük riskli cleanup patchlerini uygula (KDE + GNOME)
- [x] Kısa bakım notu dokümanı ekle

### Review

- Dokümanlar:
  - `docs/renderer-lifecycle-checklist.md`
  - `docs/renderer-lifecycle-maintenance-note.md`
- Uygulanan cleanup:
  - KDE `main.qml`: identity cache prune + error/collapse/destruction cleanup
  - GNOME `extension.js` + `indicatorLifecycleMixin.js`: close cleanup + cache prune + closed-state rebuild guard
- Doğrulama:
  - `node --check gnome-extension/aiusagemonitor@aimonitor/extension.js gnome-extension/aiusagemonitor@aimonitor/indicatorLifecycleMixin.js`
  - `qmllint com.aiusagemonitor/contents/ui/main.qml com.aiusagemonitor/contents/ui/configGeneral.qml`
  - `python3 tools/project_health_check.py --mode quick` => `13 passed/warned, 0 failed, 0 warnings`

## 2026-03-08 - Size/Complexity Debt Reduction Round 2 (Faz 21-23)

- [x] Faz 21: `build_provider_source_model` bir tur daha küçültüldü (input/runtime/payload helper ayrımı)
- [x] Faz 22: `collect_kilo` sorumluluklara bölündü (input/source, auth, fetch fallback, parse dispatch, state build)
- [x] Faz 23: `collect_gemini` split planı çıkarıldı ve güvenli helper ayrımıyla uygulandı
- [x] Baseline/complexity doğrulaması: kalan debt yalnız gerekli alanlarda görünür
- [x] Doğrulamalar: `make lint`, `make typecheck`, ilgili pytest setleri

### Review

- `legacy_locked = 0` korundu.
- `BASELINE_TIGHTEN_DUE` temizlendi.
- Kalan debt: yalnız `collect_gemini` / `collect_kilo` büyük orchestrator fonksiyonları.

## 2026-03-08 - Post-Debt Sustainability Guardrails

- [x] CI strict gate warning-fail moduna geçirildi (`make health-ci` => `--mode ci --fail-on-warn`)
- [x] Debt guardrail check eklendi:
  - baseline lock count policy
  - mypy `ignore_errors = True` yasağı
- [x] Baseline lock configleri sıfırlandı:
  - `FILE_SIZE_BASELINE_REDUCTION_PLAN = {}`
  - `PYTHON_FUNCTION_COMPLEXITY_BASELINES = {}`
- [x] Lifecycle contract kapsamı sıkılaştırıldı (GNOME + KDE + FullRepresentation)
- [x] Settings presentation için fixture-based regression testi eklendi
- [x] CONTRIBUTING ve health hardening dokümanı güncellendi

### Review

- `make lint`: PASS (0 warning)
- `make typecheck`: PASS
- `make health-ci`: PASS
- hedefli regression testleri: PASS

## 2026-03-09 - Skill Audit Fix Round (Security + Validation + Runtime Cost)

- [x] Runtime cache ve identity store yazımlarını atomik + dar izinli hale getir
- [x] Cookie cache'te plaintext header persist riskini kaldır; sadece negative miss cache bırak
- [x] Config boundary doğrulamasını sıkılaştır (payload tipi, provider/field whitelist, unknown key drop)
- [x] CLI config akışında secret field argv taşımasını engelle ve UI payload'ını sanitize et
- [x] KDE stale-state reset davranışını GNOME parity ile hizala ve command quote kırılganlığını düzelt
- [x] Status payload shape guard'larını ekle (malformed payload crash önleme)
- [x] Codex/OpenCode local scan pathlerinde gereksiz tekrar taramayı azalt
- [x] Health tool observability ve contract kapsamını genişlet
- [x] Regresyon testlerini güncelle/ekle ve CI health gate ile doğrula

### Review

- Uygulanan ana düzeltme alanları:
  - `core/ai_usage_monitor/runtime_cache.py`
  - `core/ai_usage_monitor/identity_snapshot.py`
  - `core/ai_usage_monitor/browser_cookies.py`
  - `core/ai_usage_monitor/config.py`
  - `core/ai_usage_monitor/cli.py`
  - `core/ai_usage_monitor/providers/registry.py`
  - `core/ai_usage_monitor/providers/codex.py`
  - `core/ai_usage_monitor/providers/minimax.py`
  - `core/ai_usage_monitor/local_usage.py`
  - `core/ai_usage_monitor/provider_freshness.py`
  - `core/ai_usage_monitor/status.py`
  - `com.aiusagemonitor/contents/ui/main.qml`
  - `tools/project_health_check.py`
  - `tools/project_health_contracts.py`
- Eklenen/güncellenen test odakları:
  - `tests/test_runtime_cache.py`
  - `tests/test_cli_config.py`
  - `tests/test_config.py`
  - `tests/test_browser_cookies.py`
  - `tests/test_status.py`
  - `tests/test_codex_normalization.py`
  - `tests/test_collector.py`
  - `tests/test_project_health_contracts.py`
  - `tests/test_settings_presentation_matrix.py`
- Doğrulama çıktıları:
- `make health-ci PYTHON=python` => `17 passed/warned, 0 failed, 0 warnings`
- `pytest` toplamı => `178 passed, 23 subtests passed`

## 2026-03-09 - Source Semantics Audit Follow-up (api/web/cli/remote)

- [x] `providerCapabilities` hesaplamasında `source_modes=('auto',)` provider'larda yanlış negatifleri düzelt
- [x] `remote` değerini legacy alias olarak `web`e canonical normalize et
- [x] Ollama için web-only semantiğini test ve dokümanla netleştir
- [x] Hedefli pytest + `make health-ci PYTHON=python` ile doğrula
- [x] Review ve lessons kayıtlarını güncelle

### Review

- Uygulanan kod değişiklikleri:
  - `core/ai_usage_monitor/providers/registry.py`
    - `providerCapabilities` artık yalnız `source_modes` değil; `usageDashboardBySource` sinyalleri + policy fallback ile türetiliyor.
    - `source_modes=('auto',)` descriptor'larda false-negative capability üretimi kapatıldı.
  - `core/ai_usage_monitor/sources/common.py`
  - `core/ai_usage_monitor/sources/strategy.py`
  - `core/ai_usage_monitor/config.py`
  - `core/ai_usage_monitor/identity_fingerprint.py`
  - `core/ai_usage_monitor/presentation/popup_vm_source_presentation.py`
  - `core/ai_usage_monitor/presentation/popup_vm_source_model.py`
    - Legacy `remote` inputları canonical olarak `web`e normalize edildi (backward compatible alias).
- Uygulanan test/doküman değişiklikleri:
  - `tests/test_provider_registry_shape.py`
  - `tests/test_descriptor_payload_parse.py`
  - `tests/test_source_strategy.py`
  - `tests/test_config.py`
  - `docs/reference/codexbar/providers.md` (Ollama web-only/cloud kapsamı netleştirildi)
- Doğrulama:
  - `PYTHONPATH=. ./.venv/bin/python -m pytest -q tests/test_provider_registry_shape.py tests/test_descriptor_payload_parse.py tests/test_source_strategy.py tests/test_config.py` PASS (`21 passed, 12 subtests passed`)
  - `make health-ci PYTHON=python` PASS (`17 passed/warned, 0 failed, 0 warnings`; `182 passed, 23 subtests passed`)

## 2026-03-09 - Full Skill-Suite Audit

- [x] Tüm proje skill başlıklarını audit kapsamına eşle (`project-architecture` ... `observability`)
- [x] Mimari/contract/desktop/provider/identity lens’i ile boundary ve drift risklerini tara
- [x] Security/error/data-validation/config-runtime lens’i ile güvenlik ve doğrulama risklerini tara
- [x] Testing/performance/dependency/observability lens’i ile kalite kapıları ve maliyet sinyallerini tara
- [x] Documentation/git-workflow lens’i ile dokümantasyon ve süreç uyumunu tara
- [x] Tüm bulguları severity + dosya referansı + öneriyle tek raporda birleştir
- [x] Review bölümüne kullanılan komutları, ajan kapsamlarını ve doğrulama çıktısını yaz

### Review

- Audit kapsamı tüm proje yerel skill zinciriyle yürütüldü:
  - `project-architecture`, `desktop-integration-patterns`, `presentation-contracts`, `identity-state-management`, `provider-patterns`
  - `security-hardening`, `data-validation`, `error-handling`, `config-and-runtime-state`, `python-standards`
  - `performance-optimization`, `observability`, `testing-strategy`, `dependency-management`
  - `documentation-standards`, `git-workflow`
- Paralel alt-ajanlar:
  - `019cd381-05ca-7b42-9c1a-a786cd702a9e` (mimari/desktop/presentation/provider/identity)
  - `019cd381-0bb9-7150-85de-d357cf4479c7` (security/validation/error/config-runtime/python)
  - `019cd381-11a3-76e1-a0a2-9b51677d677e` (performance/observability/testing/dependency)
  - `019cd381-17ca-7da3-8862-6bdc87c89d27` (documentation/git-workflow)
- Ana doğrulama komutları:
  - `rg --files .codex/skills`
  - `nl -ba README.md | sed -n '210,260p'`
  - `nl -ba core/ai_usage_monitor/config.py | sed -n '220,260p'`
  - `nl -ba core/ai_usage_monitor/provider_freshness.py | sed -n '1,220p'`
  - `nl -ba core/ai_usage_monitor/status.py | sed -n '1,220p'`
  - `nl -ba core/ai_usage_monitor/providers/openrouter.py | sed -n '1,150p'`
  - `nl -ba core/ai_usage_monitor/providers/zai.py | sed -n '1,140p'`
  - `nl -ba core/ai_usage_monitor/presentation/popup_vm_source_presentation.py | sed -n '1,280p'`
  - `rg -n "For Claude|superpowers:executing-plans|tests/core/" docs/plans`
- Öne çıkan bulgular:
  - Provider freshness TTL tablosu boş olduğu için cache devre dışı.
  - Status fetch hata yolunda negatif cache/backoff yok.
  - OpenRouter/z.ai custom API URL değerleri `https/allowlist` doğrulaması olmadan kullanılıyor.
  - `opencode` için explicit `web` seçimi normalize aşamasında `auto`ya zorlanıyor.
  - Popup source presentation `web` kaynağını `activeSourceLabel=API` olarak gösterebiliyor.
  - README/docs kaynak semantiği ve plan yürütme metinlerinde Codex-merkezli akışa aykırı drift var.

## 2026-03-09 - OpenCode Config Save False-Positive + Explicit Web Source Fix

- [x] `config-save-json` sensitive field kontrolündeki `cookieSource` false-positive kök nedenini düzelt
- [x] OpenCode `source=web` seçimini normalize/collector katmanında koru
- [x] Regresyon testlerini ekle/güncelle (`config`, `cli_config`, `opencode_provider`)
- [x] Hedefli pytest ve `make health-ci PYTHON=python` ile doğrula

### Review

- Uygulanan değişiklikler:
  - `core/ai_usage_monitor/config.py`
    - `is_sensitive_provider_field(...)` artık descriptor biliniyorsa önce secret-field listesine bakıyor; bilinen non-secret provider field’ları (`cookieSource` gibi) regex fallback ile yanlış bloklamıyor.
    - `normalize_config(...)` içinde `opencode source=web -> auto` zorlaması kaldırıldı.
  - `core/ai_usage_monitor/providers/opencode.py`
    - `_configured_source(...)` artık explicit `web` seçimini `auto`ya çevirmiyor.
- Eklenen/güncellenen testler:
  - `tests/test_config.py`
    - `opencode` explicit `web` kaynağını koruma testi
    - `cookieSource` alanının sensitive sayılmama testi
  - `tests/test_cli_config.py`
    - `config-save-json` için `opencode.cookieSource` kabul testi
    - normalize sonrası `opencode.source == "web"` assertion
  - `tests/test_opencode_provider.py`
    - explicit `source=web` + cookie yokken local CLI fallback yapılmaması testi
- Doğrulama:
  - `PYTHONPATH=. ./.venv/bin/python -m pytest -q tests/test_config.py tests/test_cli_config.py tests/test_opencode_provider.py` PASS (`38 passed`)
  - `make health-ci PYTHON=python` PASS (`17 passed/warned, 0 failed, 0 warnings`; `189 passed, 23 subtests passed`)
  - Ad-hoc doğrulama: `config-save-json` payload’ında `opencode.cookieSource=off` artık hata vermeden kaydediliyor.

## 2026-03-09 - OpenCode Unavailable + Enabled Provider Visibility Bugfix

- [x] `opencode` local install tespitini GUI PATH drift’e dayanıklı hale getir
- [x] Config save response’ta secret field geri-taşıma döngüsünü kır (UI follow-up save blokajını önle)
- [x] İlgili regresyon testlerini ekle/güncelle
- [x] `make health-ci PYTHON=python` ile final doğrulama yap
- [x] Review ve lessons kaydını güncelle

### Review

- Uygulanan düzeltmeler:
  - `core/ai_usage_monitor/cli_detect.py`
    - System bin fallback dizinleri genişletildi (`/usr/local/bin`, `/usr/bin`, `/bin`, `/snap/bin`).
    - Login shell `command -v` fallback eklendi (safe binary-name guard ile).
    - Amaç: KDE/GNOME GUI PATH drift durumlarında `opencode` false-unavailable riskini azaltmak.
  - `core/ai_usage_monitor/cli.py`
    - `config-save` ve `config-save-json` çıktı payload’ı `sanitize_config_for_ui(...)` ile döndürülüyor.
    - Amaç: UI staged config’e secret field geri taşınıp sonraki save’leri bloke eden döngüyü kırmak.
- Eklenen/güncellenen regresyon testleri:
  - `tests/test_cli_detect.py`
    - login shell fallback testi
    - unsafe binary-name shell fallback bloklama testi
  - `tests/test_cli_config.py`
    - `config-save-json` sonrası dönen payload’ın sanitize kalmasını ve takip eden save’in fail olmamasını kilitleyen test
- Doğrulama:
  - `PYTHONPATH=. ./.venv/bin/python -m pytest -q tests/test_cli_detect.py tests/test_cli_config.py tests/test_opencode_provider.py` PASS (`28 passed`)
  - `make health-ci PYTHON=python` PASS (`17 passed/warned, 0 failed, 0 warnings`; `185 passed, 23 subtests passed`)

## 2026-03-09 - Skill Audit Risk Fix Round (High + Medium)

- [x] Provider freshness cache TTL matrisini aç ve cache davranışını testte kilitle
- [x] OpenRouter/z.ai custom API URL doğrulamasını secure-by-default yap (unsafe override env ile)
- [x] Popup source presentation içinde `web` kaynağını `API` yerine doğru etiketle
- [x] Status fetch için failure backoff/negative cache ve timezone-aware incident sort düzeltmesi uygula
- [x] Local usage token parse akışını bozuk kayıtta kırılmayacak hale getir
- [x] Codex identity state yolunu runtime state dir ile hizala ve güvenli yazım izinlerini zorla
- [x] Config save yazımını atomik hale getir
- [x] README + plan başlıklarındaki dokümantasyon drift’ini güncelle
- [x] Hedefli pytest seti + `make health-ci PYTHON=python` ile doğrula
- [x] Review ve lessons kaydını güncelle

### Review

- Uygulanan yüksek/orta risk düzeltmeleri:
  - `core/ai_usage_monitor/provider_freshness.py`
    - TTL matrisi aktif edildi (`copilot/openrouter/zai/vertexai/ollama/amp/minimax`).
  - `core/ai_usage_monitor/providers/openrouter.py`
  - `core/ai_usage_monitor/providers/zai.py`
  - `core/ai_usage_monitor/shared/url_safety.py`
    - Custom API URL’ler için secure-by-default doğrulama eklendi (`https` + allowlist host); explicit unsafe override için env kapısı eklendi.
  - `core/ai_usage_monitor/presentation/popup_vm_source_presentation.py`
    - `resolvedSource=web` için `activeSourceLabel` artık `Web` üretiyor (`API` değil).
  - `core/ai_usage_monitor/status.py`
    - Failure backoff için kısa TTL negative cache eklendi.
    - Google Workspace incident sort fallback timezone-aware hale getirildi.
  - `core/ai_usage_monitor/local_usage.py`
    - Token parse akışı bozuk alanlarda crash etmeyecek şekilde safe-coercion ile sertleştirildi.
  - `core/ai_usage_monitor/providers/codex.py`
    - Identity state path runtime state dir’e (`runtime_cache_path`) taşındı.
    - Identity state write path’i runtime cache atomic write + `0600` izni ile hizalandı.
  - `core/ai_usage_monitor/config.py`
    - `save_config` atomik yazım (`NamedTemporaryFile` + `os.replace`) ile güncellendi.
  - `README.md`
    - OpenCode source semantiği (`auto/cli/web`) ve örnek config source değeri (`local_cli`) güncellendi.
  - `docs/plans/*.md` (8 dosya)
    - `For Claude / superpowers` başlıkları Codex merkezli başlıkla değiştirildi.
- Eklenen/güncellenen testler:
  - `tests/test_collector.py`
  - `tests/test_api_providers.py`
  - `tests/test_status.py`
  - `tests/test_local_usage.py`
  - `tests/test_codex_normalization.py`
  - `tests/test_popup_vm.py`
  - `tests/test_config.py`
- Doğrulama:
  - `PYTHONPATH=. ./.venv/bin/python -m pytest -q tests/test_collector.py tests/test_api_providers.py tests/test_status.py tests/test_local_usage.py tests/test_codex_normalization.py tests/test_popup_vm.py tests/test_config.py` PASS (`83 passed`)
  - `make health-ci PYTHON=python` PASS (`17 passed/warned, 0 failed, 0 warnings`; `199 passed, 23 subtests passed`)

## 2026-03-09 - Enabled Provider Auto-Expand (KDE + GNOME)

- [x] Kök neden: enable toggle sonrası provider satırı/expander’ın açılmamasını doğrula
- [x] KDE settings provider row’da `enabled=true` anında auto-expand davranışı ekle
- [x] GNOME prefs provider expander’da aynı davranışı parity olacak şekilde ekle
- [x] Hedefli doğrulama (health gate + ilgili test seti) çalıştır
- [x] Review ve lessons kaydını güncelle

### Review

- Kök neden:
  - KDE ve GNOME settings yüzeylerinde `enabled` switch’i state’i kaydediyor, fakat aynı anda expander/expanded state’i güncellemiyordu.
  - Sonuç olarak kullanıcı provider’ı açsa bile detay alanı kapalı kaldığı için “ana UI’da genişlemiyor” semptomu oluşuyordu.
- Uygulanan düzeltmeler:
  - `com.aiusagemonitor/contents/ui/ConfigProvidersSection.qml`
    - `onEnabledChanged` içinde:
      - `enabled=true` ise `expandedProviderId = descriptor.id` (anında expand)
      - `enabled=false` ve row açıksa `expandedProviderId = ""` (collapse)
  - `gnome-extension/aiusagemonitor@aimonitor/prefsProviderExpander.js`
    - `notify::active` handler içinde:
      - `enabled=true` ise `expander.set_expanded(true)`
      - `enabled=false` ve açıksa `expander.set_expanded(false)`
- Doğrulama:
  - `make health-ci PYTHON=python` PASS (`17 passed/warned, 0 failed, 0 warnings`; `199 passed, 23 subtests passed`)

## 2026-03-09 - KDE Native Apply + Provider Toggle Propagation Latency Fix

- [x] Kök neden analizi: autosave + polling akışı nedeniyle enable/disable gecikmesini doğrula
- [x] KDE config tarafında provider değişikliklerini autosave yerine native Apply akışına bağla
- [x] Ana widget’ta `sharedConfigPayload` apply değişimini yakalayıp shared config save + force refresh tetikle
- [x] Health gate ile doğrula
- [x] Review ve lessons kaydını güncelle

### Review

- Kök neden:
  - KDE settings ekranı provider değişikliklerinde `config-save-json` komutunu anında çalıştırıyordu; bu native Apply semantiğini bypass ediyordu.
  - Ana widget tarafı provider görünürlüğünü polling döngüsünde güncellediği için enable/disable etkisi bir sonraki döngüye kalıyordu.
- Uygulanan düzeltmeler:
  - `com.aiusagemonitor/contents/ui/configGeneral.qml`
    - `setProviderField(...)` ve `toggleOverviewProvider(...)` içinde autosave kaldırıldı.
    - Provider değişiklikleri artık yalnız `cfg_sharedConfigPayload` üzerinden staged kalıyor; KDE Apply ile commit ediliyor.
  - `com.aiusagemonitor/contents/ui/main.qml`
    - `Plasmoid.configuration.sharedConfigPayload` değişimi dinleniyor.
    - Apply sonrası değişen payload için `config-save-json` backend çağrısı yapılıyor.
    - Save başarılı olunca `refresh(true)` tetiklenerek popup-vm anında güncelleniyor (polling beklemiyor).
    - Save runner cleanup/destruction yolu eklendi.
- Doğrulama:
  - `make health-ci PYTHON=python` PASS (`17 passed/warned, 0 failed, 0 warnings`; `199 passed, 23 subtests passed`)

## 2026-03-09 - OpenCode Unavailable Etiketi (Disabled vs Unavailable) Düzeltmesi

- [x] OpenCode `Unavailable` semptomunu canlı state + config payload üzerinden doğrula
- [x] `disabled` provider durumunda settings presentation etiketlerini `Unavailable` yerine `Disabled` yap
- [x] Settings presentation matrix’e `disabled` regresyon senaryosu ekle
- [x] Hedefli pytest + health gate ile doğrula
- [x] Review ve lessons kaydını güncelle

### Review

- Kök neden:
  - OpenCode CLI kurulu ve algılanıyor olsa bile provider `disabled` durumda iken state `installed=false` olduğu için settings presentation “Unavailable” üretiyordu.
  - Bu etiket, gerçek semptomu (kapalı provider) gizleyip “CLI bulunamadı” algısı yaratıyordu.
- Uygulanan değişiklikler:
  - `core/ai_usage_monitor/sources/settings_presentation.py`
    - `disabled` sinyali (`provider.enabled == false` veya `status == disabled`) presentation kararına eklendi.
    - `sourceStatusLabel`: `Status: Disabled`
    - `availabilityLabel`: `Disabled`
    - `sourceReasonLabel`: `Provider disabled`
    - `subtitle`: `… · disabled`
    - `statusTags`: `["Disabled"]`
  - `tests/test_settings_presentation_matrix.py`
    - Fixture provider payload’ından `enabled` ve `status` alanlarını modele taşıma eklendi.
  - `tests/fixtures/settings_presentation_matrix.json`
    - `provider_disabled_status` senaryosu eklendi (`Status: Disabled` beklentisi).
- Doğrulama:
  - `PYTHONPATH=. ./.venv/bin/python -m pytest -q tests/test_settings_presentation_matrix.py` PASS (`1 passed, 4 subtests passed`)
  - `make health-ci PYTHON=python` PASS (`17 passed/warned, 0 failed, 0 warnings`; `199 passed, 24 subtests passed`)

## 2026-03-09 - Auto-First Source Policy (Default + Settings UX)

- [x] Config normalize/default akışında hybrid provider default source’u `auto` yap
- [x] KDE settings source seçeneklerinde `auto`yu önerilen ve birinci seçenek olarak sabitle
- [x] GNOME settings source seçeneklerinde `auto`yu önerilen ve birinci seçenek olarak sabitle
- [x] Regresyon testlerini güncelle (`test_config`)
- [x] Hedefli test + health gate ile doğrula
- [x] Review ve lessons kaydını güncelle

### Review

- Kök neden:
  - Hybrid provider’larda default source `local_cli` olduğu için kullanıcılar source override davranışını “sistem kararsız” olarak algılıyordu.
  - Settings yüzeyinde source option sırası `local_cli` öne çıktığı için `auto-first` niyet yansımıyordu.
- Uygulanan değişiklikler:
  - `core/ai_usage_monitor/config.py`
    - `_default_source_for_descriptor(...)` artık descriptor `auto` destekliyorsa default olarak her zaman `auto` dönüyor.
  - `com.aiusagemonitor/contents/ui/ConfigPresentation.js`
    - Source seçenekleri unique normalize edildi.
    - `auto` seçenekler içinde varsa her zaman ilk sıraya taşınıyor.
    - `auto` label: `Auto (recommended)`.
    - `defaultPreferredSource(...)` `auto`yu önceliyor.
  - `gnome-extension/aiusagemonitor@aimonitor/prefsProviderPresentation.js`
    - Source seçeneklerinde `auto` ilk sıraya alındı.
    - `sourceModeDisplayLabel('auto')` → `AUTO (RECOMMENDED)`.
    - Default source label seçiminde `auto` öncelendi.
  - `gnome-extension/aiusagemonitor@aimonitor/prefsProviderExpander.js`
    - `normalizedProviderSettings(...)` default source seçiminde `auto` önceliği eklendi.
  - `tests/test_config.py`
    - Opencode default source beklentisi `local_cli` → `auto` güncellendi.
    - Hybrid provider default-source regression testi eklendi.
- Doğrulama:
  - `PYTHONPATH=. ./.venv/bin/python -m pytest -q tests/test_config.py tests/test_cli_config.py` PASS (`31 passed`)
  - `make health-ci PYTHON=python` PASS (`17 passed/warned, 0 failed, 0 warnings`; `200 passed, 24 subtests passed`)

## 2026-03-09 - Cross-Desktop Provider Toggle Reactivity (KDE + GNOME)

- [x] Tüm provider setinde enable/disable -> `popup-vm` yansımasını backend seviyesinde doğrula
- [x] GNOME extension tarafında config değişimini event-driven izle ve force refresh ile gecikmeyi kaldır
- [x] Lifecycle cleanup ekle (monitor + debounce timeout) ve teardown güvenliğini koru
- [x] KDE/GNOME parity için hedefli regresyon testleri çalıştır
- [x] Health gate ve review/lessons kaydını güncelle

### Review

- Kök neden:
  - Backend tarafında provider enable/disable anında uygulanıyor; gecikme UI katmanında, özellikle GNOME extension’ın yalnız periyodik refresh ile (`min 20s`) güncellenmesinden kaynaklanıyordu.
  - Bu yüzden settings’te toggle sonrası ana panel/popup görünümü bir sonraki polling turuna kadar eski provider listesini gösterebiliyordu.
- Uygulanan değişiklikler:
  - `gnome-extension/aiusagemonitor@aimonitor/indicatorLifecycleMixin.js`
    - `~/.config/ai-usage-monitor/` dizini için file monitor eklendi.
    - `config.json` değişim olayları (`changed/moved/replace` akışları) yakalanıp debounced `refresh(true)` tetikleniyor.
    - Yeni cleanup yolları eklendi:
      - `_clearConfigRefreshTimeout()`
      - `_clearConfigMonitor()`
  - `gnome-extension/aiusagemonitor@aimonitor/extension.js`
    - Indicator init’te config monitor state alanları başlatıldı.
    - `_startConfigMonitor()` çağrısı eklendi.
    - `destroy()` içinde config monitor + debounce timeout temizliği eklendi.
- Doğrulama:
  - `python3 .../fetch_all_usage.py config-save-json` + `popup-vm --force` ile tüm provider’lar tek tek enable edilip doğrulandı: `tested=12`, `mismatches=[]`.
  - `PYTHONPATH=. ./.venv/bin/python -m pytest -q tests/test_config.py tests/test_cli_config.py tests/test_popup_vm.py tests/test_settings_presentation_matrix.py` PASS (`57 passed, 4 subtests passed`)
  - `make health-ci PYTHON=python` PASS (`17 passed/warned, 0 failed, 0 warnings`; `200 passed, 24 subtests passed`)

## 2026-03-09 - Gemini OAuth Credential Format Uyumluluğu

- [x] Kök neden doğrulaması: `~/.gemini/oauth_creds.json` formatı ile refresh akışındaki alan beklentisini karşılaştır
- [x] `refresh_gemini_token` içinde modern Gemini credential şemasını destekle (`id_token` tabanlı client id fallback + optional client secret)
- [x] Refresh sonrası credential persist alanlarını (`expiry_date`) geriye uyumlu şekilde yaz
- [x] Regresyon testi ekle (id_token -> client id fallback, secret olmadan refresh payload)
- [x] Hedefli pytest + health gate + canlı `popup-vm` doğrulamasını çalıştır

### Review

- Kök neden:
  - Gemini provider refresh akışı yalnız credential dosyasındaki alanlara bakıyordu.
  - Gerçek dosya formatı (`~/.gemini/oauth_creds.json`) çoğu kurulumda `client_id/client_secret` taşımıyor; `id_token` + CLI install içindeki `oauth2.js` üzerinden türetme gerekiyor.
  - Bu fallback olmadığı için 401 sonrası auth state yanlış negatife düşüyordu.
- Uygulanan değişiklikler:
  - `core/ai_usage_monitor/shared/oauth.py`
    - `id_token` JWT payload’ından `aud/azp` ile `client_id` fallback eklendi.
    - Gemini CLI kurulumundaki `oauth2.js` dosyasından (`OAUTH_CLIENT_ID`, `OAUTH_CLIENT_SECRET`) credential extraction eklendi.
    - 400 hata sınıflaması iyileştirildi (`client_secret is missing` ayrı raporlanıyor).
    - Refresh sonrası `expiry` yanında `expiry_date` da (ms) yazılıyor (Gemini CLI formatıyla uyum).
  - `tests/test_shared_helpers.py`
    - `id_token` üzerinden `client_id` çözümleme testi.
    - CLI `oauth2.js` içinden `client_id/client_secret` extraction testi.
    - `client_id` çözülemiyorsa net hata döndürme testi.
- Doğrulama:
  - `PYTHONPATH=. ./.venv/bin/python -m pytest -q tests/test_shared_helpers.py tests/test_gemini_provider.py` PASS (`12 passed`)
  - `make health-ci PYTHON=python` PASS (`17 passed/warned, 0 failed, 0 warnings`; `203 passed, 24 subtests passed`)
  - Canlı kontrol:
    - `state` çıktısında Gemini artık `authenticated=True`, `status=ok`, metric payload dolu.

## 2026-03-09 - Tray Paneli Seçili Provider ile Senkronla (KDE + GNOME)

- [x] KDE popup tab seçimini runtime state olarak sakla
- [x] KDE backend refresh çağrısında persisted panel-tool yerine runtime seçimi önceliklendir
- [x] GNOME refresh çağrısında `_selectedPopupProvider` varsa backend’e bu id’yi geçir
- [x] GNOME tab seçimi değiştiğinde force refresh tetikle
- [x] Health gate ile doğrula
- [x] Review ve lessons kaydını güncelle

### Review

- Kök neden:
  - Tray/panel metrik sağlayıcısı backend `popup-vm` çağrısında yalnız persisted `panel-tool` değerinden türetiliyordu.
  - Popup içinde anlık provider sekmesi değişse bile bu seçim backend’e taşınmadığı için panel, kullanıcı seçiminden kopuk kalıyordu.
- Uygulanan değişiklikler:
  - `com.aiusagemonitor/contents/ui/FullRepresentation.qml`
    - Yeni `providerSelected(providerId)` sinyali eklendi; sekme seçimi değişince emit ediliyor.
  - `com.aiusagemonitor/contents/ui/main.qml`
    - `runtimeSelectedProviderId` eklendi.
    - `FullRepresentation.onProviderSelected` ile runtime seçim set edilip `refresh(true)` tetikleniyor.
    - `refresh(...)` içinde backend’e gönderilen preferred provider id artık `runtimeSelectedProviderId || panelTool`.
    - Runtime seçimin payload’da artık görünmeyen provider’a işaret etmesi durumunda otomatik temizleme eklendi.
  - `gnome-extension/aiusagemonitor@aimonitor/indicatorLifecycleMixin.js`
    - `_preferredRefreshProviderId()` eklendi (`_selectedPopupProvider` öncelikli, sonra persisted panel-tool fallback).
    - `_refresh(...)` artık bu resolver’ı kullanıyor.
    - `_selectProvider(...)` değişimde `refresh(true)` tetikliyor.
- Doğrulama:
  - `make health-ci PYTHON=python` PASS (`17 passed/warned, 0 failed, 0 warnings`; `203 passed, 24 subtests passed`)

## 2026-03-09 - Gemini Model Listesini Aktif Modelle Sınırla

- [x] Gemini popup metriklerindeki model satırlarının üretim noktasını doğrula
- [x] Gemini için bucket listeden yalnız aktif modeli gösteren filtreyi uygula
- [x] Regresyon testi ekle (`test_popup_vm`)
- [x] Hedefli pytest + health gate ile doğrula
- [x] Review ve lessons kaydını güncelle

### Review

- Kök neden:
  - `provider_metrics_vm` içindeki `bucket_metrics_vm(...)` tüm `extras.buckets` girdilerini UI metric satırına dönüştürüyordu.
  - Gemini API çoklu model kotası döndürdüğü için popup diğer provider’lardan farklı olarak kalabalık model listesi gösteriyordu.
- Uygulanan değişiklikler:
  - `core/ai_usage_monitor/presentation/popup_vm_metrics_core.py`
    - Gemini için `_visible_buckets_for_provider(...)` eklendi.
    - Filtreleme önceliği: `extras.model` -> `extras.primaryModel` -> fallback `ilk bucket`.
    - `models/<id>` ve `<id>` karşılaştırmalarını uyumlu yapmak için `_normalized_model_id(...)` eklendi.
  - `tests/test_popup_vm.py`
    - `test_gemini_bucket_metrics_only_show_active_model` eklendi; çoklu bucket payload’ında tek model satırına düştüğü kilitlendi.
- Doğrulama:
  - `PYTHONPATH=. ./.venv/bin/python -m pytest -q tests/test_popup_vm.py tests/test_gemini_provider.py` PASS (`31 passed`)
  - `make health-ci PYTHON=python` PASS (`17 passed/warned, 0 failed, 0 warnings`; `204 passed, 24 subtests passed`)

## 2026-03-09 - Gemini Source Etiketini OAuth Semantiğiyle Hizala

- [x] Gemini provider descriptor/source kimliğinde API yerine OAuth semantiğini uygula
- [x] Usage dashboard source map’ine `oauth` anahtarını ekle
- [x] Gemini provider test beklentilerini güncelle
- [x] Hedefli pytest + health gate ile doğrula
- [x] Review ve lessons kaydını güncelle

### Review

- Kök neden:
  - Gemini collector OAuth token ile çalışmasına rağmen `ProviderState.source="api"` ürettiği için popup source badge “API” görünüyordu.
  - Bu, gerçek çalışma modunu yanlış yansıtıp kullanıcıda auth/config karışıklığı üretiyordu.
- Uygulanan değişiklikler:
  - `core/ai_usage_monitor/providers/gemini.py`
    - Descriptor `source_modes` alanına `oauth` eklendi (`("auto", "oauth")`).
    - `usage_dashboard_by_source` içine `oauth` map’i eklendi.
    - Tüm Gemini state çıktılarında source `oauth` olacak şekilde tek sabit (`_GEMINI_SOURCE_ID`) tanımlandı.
  - `tests/test_gemini_provider.py`
    - `state.source` beklentileri `api` -> `oauth` güncellendi.
- Doğrulama:
  - `PYTHONPATH=. ./.venv/bin/python -m pytest -q tests/test_gemini_provider.py tests/test_popup_vm.py tests/test_provider_registry_shape.py` PASS (`36 passed`)
  - `make health-ci PYTHON=python` PASS (`17 passed/warned, 0 failed, 0 warnings`; `204 passed, 24 subtests passed`)
