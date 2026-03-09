# Polling Cost Optimization Round 2 Design

**Goal:** Subprocess-per-refresh mimarisi korunurken gereksiz tekrar toplama maliyetini düşürmek; etkileşimli doğruluk (menu open / identity switch) bozulmamalı.

**Scope:** KDE `main.qml`, GNOME `indicatorLifecycleMixin.js`, backend `cli.py` + `collector.py` + `config.py` ve mevcut `runtime_cache.py` üzerinde düşük riskli değişiklikler.

## 1) En Düşük Riskli TTL/Cache Tasarımı

### Önerilen yaklaşım: Popup-VM payload sınırında kısa TTL cache

- Cache noktası provider içinde değil, `collect_popup_vm_payload(...)` çıkışı.
- Cache anahtarı:
  - `preferred_provider_id`
  - normalize config hash (`load_config()` sonucu)
  - payload mode (`popup-vm`)
- Cache TTL:
  - `pollingCacheSeconds` (varsayılan `10`, min `0`, max `60`).
- Bypass (`force=true`) koşulları:
  - UI menu açılış refresh'i
  - identity mismatch/refetch timer refresh'i
- Timer-driven background poll `force=false` çalışır; TTL içinde cached payload döner.

### Neden provider-level cache değil?

- `collect_provider(...)` akışında source fallback + identity apply + changed-provider refetch zinciri var.
- Provider-level cache bu zincirin semantiğini kırma riski taşır (özellikle account switch ve source fallback).
- Payload-level cache bu iç davranışlara dokunmadan sadece kısa aralıklı tekrar subprocess hesaplamasını azaltır.

## 2) Dokunulacak Dosyalar

- `core/ai_usage_monitor/config.py`
  - `pollingCacheSeconds` alanını default/normalize/validate et.
- `core/ai_usage_monitor/collector.py`
  - `collect_popup_vm_payload(...)` için TTL cache read/write katmanı.
  - `force` parametresi ekle.
- `core/ai_usage_monitor/cli.py`
  - `popup-vm` moduna `--force` argümanı ekle.
- `com.aiusagemonitor/contents/ui/main.qml`
  - timer refresh `popup-vm` (cache'e uygun).
  - `onExpandedChanged` ve identity refresh için `popup-vm --force`.
- `gnome-extension/aiusagemonitor@aimonitor/indicatorLifecycleMixin.js`
  - `_refresh({force})` benzeri düşük etkili parametre.
  - periodic path `force=false`, menu open + identity refresh path `force=true`.
- `core/ai_usage_monitor/runtime_cache.py`
  - mevcut helper yeterli; gerekirse küçük yardımcı fonksiyon (opsiyonel).

## 3) Davranış Riskleri

- Stale payload riski:
  - Timer poll TTL içinde eski veri dönebilir (beklenen davranış).
  - Etkileşimli path `--force` ile bypass edilmezse kullanıcı tazelik algısı bozulur.
- Argüman uyumluluğu riski:
  - `popup-vm` arg parse yanlış olursa `preferred_provider_id` ile çakışabilir.
- KDE/GNOME parity riski:
  - Sadece bir frontend `--force` geçirirse platformlar arası davranış drift'i olur.
- Identity akışı riski:
  - identity refresh timer force bypass yapmazsa mismatch çözümü gecikebilir.

## 4) Eklenmesi Gereken Testler

- `tests/test_config.py`
  - `pollingCacheSeconds` default, clamp ve normalize testleri.
- `tests/test_collector.py`
  - `collect_popup_vm_payload(force=False)` aynı TTL içinde ikinci çağrıda `collect_all()` tekrar çalışmıyor.
  - `force=True` cache bypass ediyor.
  - farklı `preferred_provider_id` cache key ayrımı.
- `tests/test_cli_config.py`
  - `popup-vm --force` ve `popup-vm <provider> --force` parse doğruluğu.
- `tests/test_project_health_contracts.py` + `tools/project_health_contracts.py`
  - KDE/GNOME lifecycle token setine `popup-vm --force` wire-up tokenları eklenir.
- Opsiyonel entegrasyon:
  - kısa süreli subprocess tekrarlarında payload tutarlılığı (stale değil, son cached payload).

## Kabul Kriteri

- `make health-ci PYTHON=python` temiz geçer.
- `menu open` ve `identity refresh` yollarında force bypass çalışır.
- Timer-driven poll path TTL içinde backend hesaplamayı tekrar etmez.
- Provider descriptor/registry/fetch-strategy yüzeyinde davranış değişikliği olmaz.
