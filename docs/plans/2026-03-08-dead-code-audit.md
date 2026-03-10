# Dead Code Audit Implementation Plan

> **For Codex:** Bu plan Codex workflow'u ile adım adım uygulanır.

**Goal:** Tüm kod tabanında dead code, dead control flow ve phantom dependency alanlarını düşük yanlış-pozitif oranıyla envanterlemek.

**Architecture:** Audit üç katmanda ilerler: önce repo kapsamı ve entrypoint'ler doğrulanır, sonra Python ve UI yüzeyleri ayrı taranır, son aşamada yanlış pozitif kaynakları elenip risk seviyesi atanır. Bulgular yalnız statik “bulundu” mantığıyla değil, testler, import zinciri ve framework yaşam döngüsü bağlamıyla triage edilir.

**Tech Stack:** Python, pytest, mypy, ESLint, GNOME Shell JS, KDE Plasma QML/JS, ripgrep

---

### Task 1: Scope ve entrypoint doğrulama

**Files:**
- Modify: `tasks/todo.md`
- Review: `package.json`
- Review: `README.md`
- Review: `core/ai_usage_monitor/cli.py`
- Review: `gnome-extension/aiusagemonitor@aimonitor/extension.js`
- Review: `com.aiusagemonitor/contents/ui/main.qml`

**Step 1: Audit görevini görünür yap**

`tasks/todo.md` içine audit checklist’i ekle.

**Step 2: Entry point’leri doğrula**

Run: `rg -n "if __name__ == ['\\\"]__main__['\\\"]|entry_points|main\\(" core gnome-extension com.aiusagemonitor`

Expected: Python CLI, GNOME extension ve KDE plasmoid başlangıç yüzeyleri görünür olur.

**Step 3: Manifestleri doğrula**

Run: `sed -n '1,220p' package.json`

Expected: Kullanılan Node araçları ve package-level dependency yüzeyi netleşir.

### Task 2: Python dead-code adayları

**Files:**
- Review: `core/**/*.py`
- Review: `tests/**/*.py`

**Step 1: Kullanılmayan tanım adaylarını çıkar**

Run: `vulture core tests tools bin`

Expected: İlk aday listesi çıkar; test yardımcıları ve public API yüzeyi ayrı not edilir.

**Step 2: Statik doğrulama ile adayları daralt**

Run: `PYTHONPATH=. ./.venv/bin/python -m mypy --warn-unreachable --config-file mypy.ini`

Expected: unreachable control flow ve tip kaynaklı ölü dallar görünür olur.

**Step 3: Çağrı zincirini elle doğrula**

Run: `rg -n "<symbol_name>" core tests gnome-extension com.aiusagemonitor`

Expected: Dinamik kullanım yoksa aday güven kazanır.

### Task 3: JS ve QML dead-code adayları

**Files:**
- Review: `gnome-extension/aiusagemonitor@aimonitor/**/*.js`
- Review: `com.aiusagemonitor/contents/ui/**/*.{qml,js}`

**Step 1: Unused import ve unused symbol sinyallerini topla**

Run: `npm run -s lint:gjs`

Expected: GNOME JS tarafındaki bariz kullanılmayan import/symbol sinyalleri görülür.

**Step 2: QML/JS import zincirini doğrula**

Run: `rg -n "import .*ConfigPresentation|import .*PopupVmSelection|Qt\\.include|Loader|Component" com.aiusagemonitor/contents/ui`

Expected: QML tarafında config-driven veya loader tabanlı dinamik kullanım alanları ayrılır.

**Step 3: Dosya erişimlerini tara**

Run: `rg -n "prefsBackend|prefsCommonRows|PopupVmSelection|ConfigBackend|ConfigPresentation" .`

Expected: Tam dosya dead olabilecek modüller ile framework tarafından kullanılan modüller ayrılır.

### Task 4: Phantom dependency ve triage

**Files:**
- Review: `package.json`
- Review: `package-lock.json`

**Step 1: Paket kullanımlarını doğrula**

Run: `rg -n "eslint|jsdoc" .`

Expected: `package.json` içindeki dependency’lerin repo içi kullanım izi görünür olur.

**Step 2: Risk seviyesine göre grupla**

Elle tablo oluştur:
- `HIGH`: doğrudan silinebilir
- `MEDIUM`: manuel doğrulama gerekir
- `LOW`: public API / framework / config-driven kullanım şüphesi var

**Step 3: Final raporu yaz**

İstenen üç bölümde Türkçe raporla ve satır/dosya referansları ver.
