# TODO

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
