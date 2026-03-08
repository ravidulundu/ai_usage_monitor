# Size/Complexity Baseline Policy (Tightened)

## Problem

Eski modelde baseline lock şu davranışa sahipti:

- `line_count <= baseline => skip`

Bu, legacy debt'i görünmez yapıyordu ve `0 warnings` çıktısı yanlış şekilde "debt yok" algısı yaratabiliyordu.

## Yeni Policy

Baseline artık **skip** etmez, sadece sınıflandırır:

1. `HEALTHY`
- Dosya/fonksiyon warning eşiğinin altında.

2. `LEGACY_DEBT_LOCKED`
- Warning/Alarm eşiğini aşıyor.
- Ama geçici baseline tavanını aşmamış.
- Debt görünür kalır (WARN olarak raporlanır).

3. `BASELINE_BREACH`
- Geçici baseline tavanı da aşılmış.
- Bu yeni kötüleşme sinyalidir (WARN/ALARM etiketiyle).

4. `NEW_DEBT`
- Baseline olmayan alanda eşik aşımı.

## Health Check Raporlama

`size-complexity-warnings` çıktısı artık şunları ayrı verir:

- `DEBT_SUMMARY`
- `[FILES LEGACY_DEBT_LOCKED]`
- `[FILES BASELINE_BREACH]`
- `[FILES NEW_DEBT]`
- `[FUNCTIONS LEGACY_DEBT_LOCKED]`
- `[FUNCTIONS BASELINE_BREACH]`
- `[FUNCTIONS NEW_DEBT]`
- `[FUNCTIONS STALE_BASELINES]`

Önemli not:

- `0 warnings` artık gerçekten "görünür debt yok" anlamına gelir.
- Legacy debt, baseline altında olsa bile uyarı olarak görünür.

## Kategori Bazlı Azaltım Planı (Dosya Bazı)

Aşağıdaki tablo geçici baseline toleransını ve hedefleri gösterir.

| File | Current Lines | Target | Temporary Baseline | Next Baseline | Plan |
|---|---:|---:|---:|---:|---|
| `gnome-extension/aiusagemonitor@aimonitor/extension.js` | 203 | 180 | 230 | 210 | panel/popup orchestration ayrıştırma |
| `gnome-extension/aiusagemonitor@aimonitor/prefs.js` | 220 | 180 | 240 | 220 | prefs helper/build split tamamlanması |
| `core/ai_usage_monitor/presentation/popup_vm.py` | 153 | 180 | 220 | 200 | VM assembly helper ayrışması |
| `core/ai_usage_monitor/identity.py` | 41 | 120 | 160 | 140 | facade inceltme, branch helper modüllere taşıma |
| `core/ai_usage_monitor/collector.py` | 61 | 140 | 180 | 160 | collector facade-only yaklaşımı |
| `com.aiusagemonitor/contents/ui/FullRepresentation.qml` | 119 | 130 | 150 | 140 | conditional loader parçalama |
| `com.aiusagemonitor/contents/ui/CompactRepresentation.qml` | 157 | 140 | 165 | 155 | ring/icon alt bileşen ayrımı |
| `com.aiusagemonitor/contents/ui/ProviderDetailSection.qml` | 151 | 140 | 160 | 150 | metric/cost/actions section split |
| `com.aiusagemonitor/contents/ui/PopupHeader.qml` | 79 | 120 | 140 | 130 | header row boundaries korunması |
| `com.aiusagemonitor/contents/ui/configGeneral.qml` | 162 | 150 | 190 | 175 | config orchestration delegation |

Not:

- `Current Lines` snapshot değerdir (2026-03-07).
- Baseline kalıcı değildir; `Next Baseline` adımına çekilerek düşürülmelidir.
