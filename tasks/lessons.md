# Lessons

## 2026-03-09 - OAuth Tabanlı Provider'ı `api` Source ile Etiketleme UI Semantik Hatası Üretir

- Provider gerçek çağrıyı HTTP endpoint’e yapsa bile kimlik doğrulama modeli OAuth ise `source` alanı `api` yerine `oauth` olmalıdır.
- `source` alanı yalnız transport’u değil kullanıcıya gösterilen çalışma modunu da sürer; yanlış source etiketi popup badge’lerinde “API configured” gibi yanıltıcı sinyal üretir.
- Descriptor seviyesinde `source_modes` ile runtime `ProviderState.source` birlikte hizalanmazsa source model fallback/availability metinleri drift eder.
- Bu sınıf düzeltmelerde en kısa regresyon kilidi: provider unit testinde `state.source` + popup/state smoke test seti.

## 2026-03-09 - Gemini Çoklu Quota Buckets UI'da Gürültü Üretiyor

- Provider `extras.buckets` alanını doğrudan listelemek Gemini gibi çoklu model quota döndüren sağlayıcılarda popup okunabilirliğini bozuyor.
- Tasarım parity’si için model satırları sağlayıcı semantiğine göre filtrelenmeli; Gemini’de `extras.model` veya `primaryModel` önceliklendirilip tek satır gösterilmeli.
- Model id karşılaştırmalarında `models/<id>` ve çıplak `<id>` format farkı normalize edilmezse yanlış bucket seçilir.
- Bu tip UI sadeleştirmeleri regresyon testine bağlanmalı; aksi halde yeni provider payload değişimleri model satırı gürültüsünü geri getirir.

## 2026-03-09 - Tray Provider Seçimi Persisted Ayardan Ayrı Runtime Kanal İster

- Panel/tray metriğini yalnız persisted `panel-tool` ayarına bağlamak, popup içi anlık provider seçimini yansıtmaz; runtime seçimin backend çağrısına taşınması gerekir.
- KDE/GNOME parity için aynı kural izlenmeli: “seçim değişti -> backend `popup-vm <providerId> --force`”.
- Runtime seçim stale kalabilir; payload’da provider artık yoksa seçim otomatik temizlenmeli, aksi halde panel sürekli fallback davranışı üretir.
- Popup sekme seçimi ile panel göstergesi farklı kanallardan gidiyorsa kullanıcı bunu “yanlış provider gösteriyor” olarak algılar; bu iki kanal tek resolver’da birleşmelidir.

## 2026-03-09 - Gemini OAuth Şema Drift’i Auth Hatası Gibi Görünebilir

- `~/.gemini/oauth_creds.json` dosyası `client_id/client_secret` içermeyebilir; refresh akışında önce `id_token` (`aud/azp`) fallback’i, sonra Gemini CLI kurulumundaki `oauth2.js` (`OAUTH_CLIENT_ID`, `OAUTH_CLIENT_SECRET`) fallback’i uygulanmalıdır.
- `id_token` içindeki `aud/azp` alanı güvenli bir `client_id` fallback kaynağıdır; bu yoksa hata metni “auth invalid” yerine kök nedeni net söylemelidir (`Missing OAuth client id`).
- Google token endpoint 400 yanıtını tek tipe indirgemek yanlıştır; `client_secret is missing` gibi açıklamalar ayrı sınıflanmalıdır.
- Kullanıcı “auth yaptım” dediğinde sadece `installed/authenticated` bayrağına bakmak yeterli değil; canlı API 401 + refresh sonucu birlikte okunmalı.
- Refresh başarılı olsa bile `expiry_date` (ms) alanını korumamak CLI format drift’ine yol açabilir; yazımda hem `expiry` hem `expiry_date` tutmak daha dayanıklıdır.

## 2026-03-09 - Enable/Disable Gecikmesi İçin Polling Değil Event-Driven Tetikleyici Gerekir

- Backend doğrulaması temizse (`config-save-json` sonrası `popup-vm --force` anında doğruysa) gecikmenin kaynağı çoğunlukla desktop lifecycle/polling katmanıdır; kök neden burada aranmalı.
- GNOME extension’da yalnız `refresh-interval` ile yenilemek provider toggle UX’ini bozar; `config.json` file monitor + kısa debounce + `refresh(true)` zinciri gecikmeyi deterministik kaldırır.
- Lifecycle patch’lerinde watcher/timer eklemek tek başına yeterli değildir; `destroy()` akışına explicit monitor disconnect + timeout cleanup eklenmeden iş tamamlanmış sayılmamalı.

## 2026-03-09 - Source Politikası Varsayılanı UX’i Doğrudan Belirler

- Hybrid provider’larda defaultu `local_cli` yapmak, kullanıcı müdahalesi yokken bile override hissi yaratıyor; güvenilir temel için `auto-first` daha doğru.
- Aynı politika backend’de uygulanıp settings option sırası güncellenmezse kullanıcı hâlâ eski davranışı görür; config default + KDE/GNOME option sırası birlikte değişmelidir.
- “Recommended” etiketinin seçenek sırasıyla tutarlı olması gerekir; aksi halde öneri metni ve gerçek seçim ayrışır.

## 2026-03-09 - Disabled Durumu Unavailable ile Karıştırılmamalı

- Provider kapalı (`enabled=false`) olduğunda “Unavailable” etiketi kullanıcıyı yanlış kök nedene götürür; bu durumda etiket açıkça “Disabled” olmalı.
- `installed=false` tek başına “CLI yok” anlamına gelmez; disabled state ile availability state ayrıştırılmadan sunum katmanı yanıltıcı olur.
- Settings presentation için durum etiketleri operasyonel teşhis metni olduğu için (`Disabled`, `Unavailable`, `Auth required`) semantik olarak ayrık tutulmalı.

## 2026-03-09 - KDE Settings İçin Autosave Native Apply’ı Bozar

- KDE plasmoid config akışında `cfg_*` alanlarını değiştirirken backend autosave çağrısı yapmak native Apply semantiğini fiilen bypass eder.
- Provider görünürlüğü gibi kullanıcı etkisi yüksek ayarlar staged kalmalı; commit anı Apply olmalı.
- Apply sonrası ana widgetta config değişimini dinleyip force refresh tetiklenmezse kullanıcı “enable/disable geç uygulanıyor” semptomu görür.

## 2026-03-09 - Enable Eylemi UI Affordance ile Tamamlanmalı

- Provider settings’te `enabled=true` sadece persist edilirse kullanıcı geri bildirimini yarım bırakır; aynı etkileşimde detay panelinin auto-expand olması gerekir.
- KDE ve GNOME yüzeyleri aynı kullanım semantiğini vermeli; birinde expand diğerinde kapalı kalırsa davranış drift’i kullanıcıya “ayar uygulanmadı” olarak yansır.
- Benzer UI sorunlarında sadece veri/state katmanını değil, eylemin görsel affordance zincirini (toggle -> expanded state) birlikte doğrulamak gerekir.

## 2026-03-09 - Security Guard ve Source Semantiği Birlikte Fixlenmeli

- Audit bulgularında yalnız tek semptoma odaklanmak yetersiz kalıyor; `config-save` boundary, provider source normalization ve popup presentation alanları birlikte ele alınmazsa kullanıcı görünümünde “fixlenmedi” hissi devam ediyor.
- Secret-field guard’larda regex fallback ancak descriptor bilinmiyorsa çalışmalı; descriptor tarafından açıkça izinli field’lar (`cookieSource`) yanlış pozitiften korunmalı.
- Provider source tercihi (`web/auto`) normalize katmanında zorla çevriliyorsa UI ve runtime drift üretiyor; explicit user choice korunmalı, fallback yalnız `auto` yoluna bağlı kalmalı.
- Runtime maliyet fixlerinde cache/buffer eklemek tek başına yeterli değil; davranışın testte kilitlenmesi ve health gate ile doğrulanması şart.

## 2026-03-09 - Sensitive Field Guard’da Pattern Fallback, Descriptor Bilgisini Ezmemeli

- `config-save-json` boundary’sinde secret alan engeli yalnız regex tabanlı olursa `cookieSource` gibi bilinen non-secret field’lar yanlış pozitif üretip ayar kaydını bloke edebilir.
- Doğru sıra: descriptor varsa önce explicit secret-field listesi; descriptor tarafından tanınan diğer alanları güvenli kabul et; regex fallback sadece descriptor bilinmiyorsa çalışmalı.
- Provider source semantiğinde explicit kullanıcı tercihini (`source=web`) normalize katmanında implicit `auto`ya çevirmek, UI niyeti ile runtime davranışını ayrıştırır; böyle coercion varsa descriptor/UI seçenekleriyle birebir hizalanmalıdır.
- Bu sınıf hatalarda en hızlı smoke-check: CLI ile minimal `config-save-json` payload’ı (`opencode + cookieSource`) çalıştırıp boundary davranışını doğrudan doğrulamak.

## 2026-03-09 - GUI PATH Drift ve UI Save Döngüsü Hataları Birlikte Düşünülmeli

- Desktop entegrasyonlarında CLI kurulu olsa bile GUI process PATH’i farklı olabildiği için sadece `shutil.which(...)` yeterli değil; sistem dizinleri + güvenli login-shell fallback kombinasyonu gerekli.
- Config UI boundary’sinde save yanıtına secret field geri basmak, bir sonraki save çağrısında boundary validator ile çarpışıp sessiz “ayar uygulanmıyor” semptomu üretebilir; UI’ye dönen config her zaman sanitize olmalı.
- “Provider açtım ama ana ekrana gelmedi” türü semptomlarda yalnız render tarafına bakmak yerine config-save pipeline ve follow-up state refresh zinciri birlikte doğrulanmalı.

## 2026-03-09 - Source Capability Doğrulamasında `source_modes` Tek Başına Yeterli Değil

- `providerCapabilities` alanını yalnız `source_modes` üzerinden türetmek `source_modes=('auto',)` descriptor'larda yanlış negatif üretiyor; capability türetimi dashboard source mapping ve policy sinyallerini de içermeli.
- `remote` gibi legacy source tokenları kod tabanında aile üyesi olarak dağınık taşımak yerine tek canonical dönüşüm kuralıyla (`remote -> web`) normalize edilmelidir.
- Dış dokümantasyonla drift riski olan providerlarda (örn. Ollama) scope netliği kod + test + doküman üçlüsünde birlikte kilitlenmelidir; sadece kod değişikliği yeterli değildir.

## 2026-03-09 - Bootstrap Çıktısında Araç Varsayımı Yapma

- Kullanıcı hangi ajanı kullandığını açıkça söylemeden bootstrap çıktısını `.claude` merkezli varsaymamak gerekir; önce aktif ajan/skill dizini bağlamı doğrulanmalı.
- Skill bootstrap çıktısı araç-özel olmalı: Codex için proje içi öncelikli hedef `.codex/skills` ve ilgili `AGENTS.md` kurallarıdır.
- Prompt veya skill referansından gelen örnek path'leri proje gerçeği sanmak risklidir; repo bağlamındaki gerçek workflow ile hizalanmadan dosya yapısı önerilmemeli.
- Kullanıcı araç tercihini düzelttiğinde yalnız cevap dili değil, üretilen dizin yapısı, manifest ve handoff metni de aynı anda güncellenmelidir.

## 2026-03-09 - Bootstrap'ta Skill Suite AGENTS İçine Bağlanmalı

- Proje içine skill üretmek tek başına yeterli değildir; `AGENTS.md` bu skill’leri isimleriyle ve tetiklenme alanlarıyla bağlamalıdır.
- Yerel `.codex/skills/*` üretildiyse ajan talimatı, hangi işte hangi local skill’in kullanılacağını açıkça söylemelidir; aksi halde suite pasif kalır.
- Scope kilidi ile skill haritası aynı belgede birlikte yer almalı: önce repo dışına taşmama kuralı, hemen ardından proje-özel skill aktivasyon listesi verilmelidir.
- Bootstrap teslimi ancak üçlü birlikte tamam sayılır: local skills, manifest, ve `AGENTS.md` içi activation wiring.

## 2026-03-08 - CI Fail Kök Nedenini Logdan Ayır

- Review yorumları kapanmış olsa bile CI kırığı bağımsız olabilir; önce en güncel failing run logu okunmalı, varsayım yapılmamalı.
- `qmllint` gibi Qt araçlarında sadece `command -v` yetmez; CI için `qtpaths6 --query QT_HOST_BINS` ve `/usr/lib/qt6/bin` fallback’i eklenmeli.
- `qmllint` CI’da Plasma modülleri eksikken import-resolution warning ile dönebilir; syntax gate bu warning’leri parse/syntax error’dan ayırarak değerlendirmeli.
- Shell scriptlerde `A && B || true` kalıbı shellcheck SC2015 üretir; davranışı koruyan açık `if` bloğuna çevirmek daha güvenli ve okunabilir.

## 2026-03-08 - Lint Coverage ve Baseline Guard Dürüstlüğü

- GNOME lint target listesini elle yönetmek yerine extension klasöründen otomatik keşfetmek, yeni mixin/helper dosyalarının sessizce kapsam dışı kalmasını engelliyor.
- ESLint ve contract test globları aynı kapsama (`**/*.js`) hizalanmazsa CI ile local sonuçları drift ediyor; ikisi birlikte güncellenmeli.
- Baseline lock yalnızca `legacy locked` etiketi verince debt algısı zayıflıyor; `next-baseline` eşiğine gelen dosyaları ayrı `BASELINE_TIGHTEN_DUE` sinyaliyle göstermek daha dürüst.
- Settings tarafında canonical `settingsPresentation` varken renderer’da fallback policy üretmek (status/fallback/availability) semantik drift kaynağı; fallback’ler minimal tutulmalı.

## 2026-03-08 - Quarantine Sıfırlama İçin Son İki Provider Deseni

- `None in (...)` kontrolü mypy daraltması için yeterli olmayabiliyor; `assert ... is not None` ile açık daraltma yapmak güvenli ve küçük etkili.
- `json.loads(...)` çıktısı provider parserlarında her zaman `dict[str, Any]`e normalize edilmeli; bu yapılmadığında hem `union-attr` hem `no-any-return` zinciri oluşuyor.
- `ProviderState.error` alanına `legacy.get("error")` doğrudan taşımak yerine `str(...) if ... is not None else None` normalizasyonu, provider modüllerinde tekrarlayan tip kırılmalarını hızlı kapatıyor.
- Typing-only turunda davranışı korumak için en güvenli yaklaşım: imza ekleme + daraltma + dönüş tipi netleştirme; akış/iş kuralı refactor’ına girmemek.

## 2026-03-08 - Provider Quarantine Eritirken Sıralama Kritik

- En güvenli sıra: `copilot/claude` gibi daha kompakt modüller, ardından `codex/gemini`; bu sırayla giderken her faz sonunda `make typecheck` çalıştırmak geri dönüş maliyetini düşürüyor.
- Provider dosyalarında en sık kırılan noktalar: `legacy` sözlüğünün bool’a daralması, `settings.get(...).strip()` union hataları ve `ProviderState.error` alanına `Any` geçişi.
- `refresh_*` benzeri yardımcılardan dönen `dict | None` sonuçlarını doğrudan atamak yerine `is not None` daraltması yapılmalı; aksi halde güvenli retry akışı bile typecheck’i kırıyor.
- Quarantine’de kalan modüller için önce overridesiz envanter çıkarmak (`--config-file` geçici kopya) gerçek iş yükünü netleştiriyor; “hepsini bir turda temizleyelim” yaklaşımını engelliyor.

## 2026-03-08 - Quarantine Debt Azaltımında Önce Core Sonra Düşük-Churn Provider

- `ignore_errors` debt azaltımında önce core-adjacent modülleri (`local_usage`, `browser_cookies`, `presentation.identity_vm`) temizlemek, provider parser karmaşıklığına girmeden sağlam ilerleme sağlıyor.
- Provider tarafında en az riskli tur için `settings.get(...).strip()` kalıplarını önce güvenli daraltma (`isinstance`) ile düzeltmek gerekir; no-any-return ve union-attr hatalarının büyük kısmı buradan geliyor.
- Error payload’ı `dict[str, Any]` iken `ProviderState.error` alanına doğrudan geçirmek yerine `str | None` normalize etmek, typed geçişlerde tekrarlayan kırılmaları engelliyor.
- Carve-out kapanışı (`providers.kilo`) ve quarantine azaltımı aynı turda yapılabiliyor, ama her faz sonunda zorunlu `make typecheck` koşmadan ilerlemek hataları katmanlayıp geri dönüş maliyeti artırıyor.

## 2026-03-08 - Provider Debt Erişiminde Kontrollü Geri Adım Normaldir

- Aynı turda çok sayıda provider override kaldırınca gürültü patlayabiliyor; kontrollü debt reduction için düşük-churn modülleri kalıcı olarak çıkarıp yüksek gürültülü modülleri tekrar quarantine’e almak kabul edilebilir.
- `disallow_untyped_calls` scoped açıldığında beklenmedik tek hata bile (ör. untyped `__init__`) tüm fazı bloke edebilir; önce minimal tip imzası ekleyip strictness’i korumak daha doğru.
- Carve-out azaltımı ile override azaltımı ayrı borç türleri; ikisini ayrı metrikle takip etmek ilerlemeyi daha dürüst gösteriyor.
- Kilo gibi yüksek borçlu modül için önce “eksik annotation envanteri” çıkarmak, tek turda kırmadan ilerlemek için şart.

## 2026-03-08 - Strictness Artırımı İçin Global Bayrak + Scoped Carve-Out Dengesi

- `disallow_incomplete_defs` global açılınca provider modüllerinden gürültü gelebilir; hedef dışı alanları geçici carve-out ile izole edip planlanan modüllerde gerçek kalite artışı sağlamak daha güvenli.
- `ignore_errors` kaldırma turu en verimli haliyle “önce küçük ve iyi sınırlı modüller”de yapılmalı (`popup_vm_usage_blocks`, `identity_*` gibi), provider parser’larına ilk turda girmemek teslimat riskini düşürüyor.
- mypy wildcard pattern’leri segment bazlı olmalı; `popup_vm_source*` gibi desenler geçersiz, explicit modül isimleri daha güvenli.
- `make typecheck`’i faz sonunda zorunlu koşmak, ara adımda oluşan config-syntax veya tip eşleşme drift’ini hemen yakalıyor.

## 2026-03-08 - Lifecycle Guard Must Be Multi-File And Platform-Symmetric

- Lifecycle health’i tek dosyada token aramakla ölçmek yetersiz; GNOME tarafında lifecycle sorumluluğu mixin’lere dağıldıysa contract da çok dosyalı olmalı.
- KDE lifecycle riskleri syntax ile görünmez kalıyor; `main.qml` ve `configGeneral.qml` için timer/DataSource/destruction token kontratı ayrı check olarak zorunlu.
- “Syntax geçti” ile “lifecycle healthy” karışmasın diye health check’te lifecycle kontrolleri ayrı isimlerle raporlanmalı.
- Contract check modelinde `required/forbidden/warn` ayrımı pratik: kritik cleanup eksikleri fail olur, riskli desenler warning-first kalır.

## 2026-03-07 - Settings Presentation Must Be Core-Canonical And Complexity-Safe

- KDE/GNOME settings tarafında source/status metni ayrı helper’larda üretildiğinde semantic drift kaçınılmaz; canonical kaynak `sourceModel.settingsPresentation` olmalı.
- GNOME prefs yalnız `config-ui` çekerse `sourceModel` boş kalır ve renderer fallback policy’ye geri düşer; settings purity için `config-ui-full` gibi state-inclusive payload zorunlu.
- Core’a yeni presentation alanı eklerken tek fonksiyona yığmak (`build_provider_source_model`) health guard’da baseline breach üretir; aynı patch içinde helper ayrımı yapılmalı.
- Kalite kapısı doğrulamasında sadece `0 failed` yeterli değil; yeni `BASELINE_BREACH` ve `ruff-format drift` aynı turda temizlenmeden iş tamamlandı sayılmamalı.

## 2026-03-07 - Canonical Local-First Needs Strategy + Collector Cooperation

- `preferredSource=local_cli` yalnız strategy katmanında tanımlanırsa yetmez; collector aday zincirini gerçekten denemediği sürece fallback davranışı uygulanmaz.
- Kullanıcı tercihi (`configuredSource`) ile aktif kaynak (`resolvedSource`) ayrı taşınmalı; aksi halde source switch sessizce olur ve UI yanıltır.
- Local-first fallback için ayrı reason kodu (`local_unavailable`) gerekli; generic `fallback_selected` kullanıcıya neden geçiş olduğunu anlatmıyor.
- Settings dropdown’ı descriptor `sourceModes` ile sınırlı kalırsa canonical preference seçilemez; local+remote destekleyen provider’larda `local_cli` opsiyonu explicit eklenmeli.

## 2026-03-07 - Canonical Source Fields Need Flat + Nested Exposure

- Source-aware contract yalnız `sourceModel` nested map’te bırakılmamalı; popup-vm provider düzeyinde flat canonical alanlar da yayınlanmalı (`preferred/resolved/available/fallback/local/api/auth`).
- `apiConfigured` yalnız top-level kalırsa settings/popup consumer’ları drift ediyor; `availability` içinde de canonical olarak taşınmalı.
- Settings satırlarında source strateji metni `availableSources` olmadan eksik kalıyor; kullanıcı “neden bu source seçildi / başka ne var” sorusunu yanıtlayamıyor.
- Source availability kararlarında `apiKeyPresent` tek başına yeterli değil; `apiConfigured` öncelikli kontrol olmalı.

## 2026-03-07 - Pace Tracking Belongs In Presentation VM

- Pace metni renderer’da üretilmemeli; metric secondaryText olarak popup-vm’de hazırlanmalı ve KDE/GNOME aynı contract’ı tüketmeli.
- Pace hesaplaması provider-id hardcode yerine metric-window (label + reset) tabanlı olmalı; session ve weekly aynı semantiği paylaşmalı.
- Pace görünürlüğü için pencere başlangıcı gürültü filtresi presentation katmanında olmalı; renderer gizleme kuralı taşımasın.
- Kullanıcıya anlamlı pace çıktısı için tek format korunmalı: `deficit/reserve/on-pace` + `lasts until reset/runout`.

## 2026-03-07 - Popup Anatomy Contract Must Be Renderer-Enforced

- Popup-vm çoğu durumda sıralı metric verse de renderer katmanında sabit anatomy contract ayrıca enforce edilmeli.
- Güvenli desen: renderer metric sırasını normalize et (`session -> weekly -> custom/model`), geri kalan section sırası sabit kalsın.
- KDE ve GNOME’da aynı hierarchy korunmadığında kullanıcı tarafında parity bozuluyor; iki renderer’da aynı sıra tek tek kilitlenmeli.
- Compact utility hissi için spacing/progress tokenları korunmalı; palette temelli değişiklik yerine hierarchy düzeltmesi tercih edilmeli.

## 2026-03-07 - Tabs Row Must Be Driven By Enabled Providers

- Popup renderer tarafında tab görünürlüğü `popup.tabs` dizisinin incidental içeriğine bırakılmamalı; canonical kaynak `enabledProviderIds` olmalı.
- `overview` tabı normal provider tablarından ayrı bir kavramdır; aynı top row içinde ayrı tab olarak eklenmeli ve içerik akışı ona göre render edilmelidir.
- Overview seçimi ile normal tab görünürlüğü kesin ayrılmalı; settings copy bu ayrımı açıkça anlatmalıdır.
- KDE ve GNOME aynı semantiği paylaşmalı: header’dan önce top tabs row, enabled provider tabs zorunlu, overview varsa ayrı.

## 2026-03-07 - Enabled vs Overview Must Be Separate Contracts

- `enabled` ve `overview` aynı payload alanına sıkıştırılmamalı; popup-vm’de ayrı listeler (`enabledProviderIds`, `overviewProviderIds`) zorunlu.
- `hasOverview` kart doluluğuna bağlı olursa kullanıcı seçimi görünmez hale gelebiliyor; seçim varlığına bağlamak daha doğru.
- Settings metinleri ayrımı açık söylemezse kullanıcı “overview seçtim, neden tab kapandı/açıldı?” diye yanlış çıkarım yapıyor.
- KDE overview seçiminde enabled/detected kısıtı kavramsal ayrımı bozuyor; seçim UI’sı bağımsız olmalı, status yalnız bilgilendirme amaçlı gösterilmeli.

## 2026-03-07 - Source Resolution Must Be Explicit In Core

- Provider fetch stratejisi ile source resolution aynı yerde kalınca davranış opaklaşıyor; `source_strategy` katmanı ayrı olmalı.
- `preferredSource` ve `resolvedSourceHint` collector öncesi üretilmeli; gerçek `resolvedSource` ise fetch sonrası provider state’ten doğrulanmalı.
- Fallback zinciri (`fallbackChain`) ve `supportsProbe` alanları source model contract’ında yoksa UI source kararını açıklayamıyor.
- Testlerde strategy/fetch ayrımı korunmalı: collector testleri patch ederken callable map geriye uyumlu kalmalı.

## 2026-03-07 - Descriptor-Driven Provider Contract

- Provider metadata popup içinde statik map ile tutulduğunda drift kaçınılmaz oluyor; `status/usage/sources/policy` descriptor’da canonical olmalı.
- Fetch strategy descriptor’dan ayrılmalı; collector descriptor listesini sürmeli, fetch mapping ayrı katmanda kalmalı.
- Renderer linkleri ve label seçimleri descriptor payload’dan dolaylı beslendiğinde KDE/GNOME/CLI kontratı tek yerden yönetilebilir oluyor.
- Geçişte dinamik provider URL istisnaları (ör. workspace bazlı link) tek bir yardımcı fonksiyonda tutulmalı; renderer veya statik map içine kaçmamalı.

## 2026-03-07 - Popup Source Semantics Must Be VM-First

- Popup renderer tarafında source metni üretmek yerine `popup-vm` içinde tek `sourcePresentation` sözleşmesi tutmak KDE ve GNOME eşleşmesini ciddi şekilde kolaylaştırır.
- Source durumu popup'ta boğmadan vermek için iyi denge: `mode pill + active source pill + kısa status pills`; detay neden metni tek satır olmalı.
- Missing usage kopyası generic kalırsa kullanıcı yanlış yorumluyor; source-aware nedenler (`CLI not installed`, `API not configured`, `Auth invalid`, `Local usage unavailable`, `Source switched`) ayrı ayrı verilmelidir.
- Source/account refresh ara durumunda metric metninin `Source switched` olarak normalize edilmesi, stale data gösteriminden daha güvenli ve anlaşılır.

## 2026-03-07 - Source-Aware Settings Row Hierarchy

- Provider satırında source şeffaflığı için en iyi denge: `source mode badge + active source chip + kısa status chips`; uzun teknik metinler expand bölümünde kalmalı.
- “Neden bu source seçildi?” bilgisi row subtitle'a gömülmemeli; ayrı `Why this source` satırı daha taranabilir ve daha az gürültülü.
- GNOME `ExpanderRow` başlığında source görünürlüğü için suffix badge + kısa subtitle kombinasyonu, native görünümü bozmadan gerekli netliği sağlıyor.
- KDE tarafında satırda çoklu metin yerine chip kullanımı, provider listesinde hizayı ve hızlı taranabilirliği belirgin şekilde iyileştiriyor.

## 2026-03-07 - Capability/Strategy/Avalability Contract Clarity

- `sourceModel` içinde sadece `sourceLabel/sourceDetails` taşımak yeterli değil; renderer ve settings için machine-readable bloklar (`providerCapabilities`, `sourceStrategy`, `availability`) zorunlu.
- Settings fallback senaryosunda live state boş gelebilir; bu yüzden descriptor payload da capability bilgisini taşımalı.
- `resolvedSource` ve `resolutionReason` birlikte verilmezse “neden bu kaynak seçildi?” sorusu UI’da yanıtlanamıyor.
- `authValid`/`apiKeyPresent`/`localToolInstalled` ayrımı yapılmadan tek bir “configured” alanı kullanıcıya yanıltıcı geliyor.

## 2026-03-07 - Settings Screen Productization

- Settings ekranında “çalışıyor” yeterli değil; utility-form hissini kırmak için section grouping ve hierarchy explicit tasarlanmalı.
- Genel ayarlar ve provider yönetimi aynı yüzeyde bırakılmamalı, ayrı grup ve farklı ritimle sunulmalı.
- Provider satırında kritik kontrol seti sabit olmalı: icon + name/subtitle + configure + enabled; geri kalan advanced alanlar expand altında kalmalı.
- Native görünüm için sabit palet yerine tema tabanlı yüzey/opaklık tonlarıyla kart ayrımı yapılmalı.

## 2026-03-07 - Multi-Account Snapshot Isolation

- Provider bazlı tek aktif fingerprint tutmak yeterli değil; aynı provider altında hesaplar arası hızlı dönüş için fingerprint->snapshot map tutulmalı.
- Account switch algısında `switched` ile `changed` ayrılmalı: snapshot restore varsa `switched=true` kalırken `changed=false` olmalı (gereksiz force-refresh engellenir).
- Renderer güvenliği için backend `identity.known/scope/confidence` alanlarını açıkça taşımalı; identity bulunamayan durumda cache reuse yapılmamalı.
- `providerStateKey` ve `accountStateKey` gibi açık state key alanları debug ve UI contract doğrulamasını ciddi şekilde kolaylaştırır.
- Regression set sadece mutlu yol olmamalı: rapid account switch, identity missing, session-only switch ve stale UI guard senaryoları birlikte testlenmeli.

## 2026-03-07 - Renderer Identity Mismatch Guard

- Account-aware backend invalidation tek başına yeterli değil; renderer da son-render fingerprint ile gelen VM fingerprint'ini karşılaştırmalı.
- Identity mismatch anında eski metrics/extra/cost bloklarını render etmek yerine VM kaynaklı `switchingState` ara durumu gösterilmeli.
- Switching metinleri renderer'da hardcode edilmemeli; presentation katmanından (`popup-vm`) taşınmalı.
- Mismatch tespitinde kısa gecikmeli force-refresh korunmalı; bir çevrim sonra fingerprint stabilize olunca tam render geri açılmalı.

## 2026-03-07 - Theme Native UI Passes

- Yapısal referans alınırken renk referansı alınmamalı; KDE/GNOME renderer kendi tema tokenlarından beslenmeli.
- `warn/success/error` gibi semantik tonlar accent türevi yerine platform semantik tokenlarıyla bağlanmalı.
- Compact popup yoğunluğu artırılırken separator ritmi tekilleştirilmeli; ardışık çift separator bırakılmamalı.
- Görsel revizyon sonrası zorunlu doğrulama: hardcoded renk taraması + popup-vm komutu + ilgili test seti.

## 2026-03-07 - Scope Lock (KDE-only UI Correction)

- Kullanıcı kapsamı tek platforma daralttığında (örn. sadece KDE), diğer platform dosyalarına dokunmadan patch üret.
- KDE popup compactlaştırmasında en güvenli kaldıraç `PopupTokens.qml`; yoğunluk değişikliklerini önce token seviyesinde yap.
- Tabs row kontratını bozmadan zorunlu provider sırası uygulanacaksa `FullRepresentation` içinde canonical tab modeli üretmek en düşük riskli yol.
- Yapısal referans istenirken renk referansı istenmiyorsa tek doğrulama ölçütü: Kirigami theme binding + hardcoded renk taraması.

## 2026-03-07 - Scope Lock (GNOME-only UI Correction)

- Kullanıcı sadece GNOME istediğinde KDE/QML tarafına hiç dokunma; değişiklikleri `extension.js` + `stylesheet.css` ile sınırla.
- Referans anatomisi isteniyorsa GNOME popup'ta top-level sıra: tabs row -> provider header -> metrics -> extra/cost -> actions olmalı.
- Tabs row davranışı karmaşıklaşınca tek fonksiyonda bırakma; tab buton üretimini helper fonksiyonlara bölmek bakım maliyetini düşürüyor.
- Compact popup hissinde en etkili kaldıraçlar: üst header satırını kaldırmak, progress kalınlığını düşürmek, content/action paddings'i sıkılaştırmak.
- Theme-native güvence için final kontrolde hardcoded renk taraması koş; yalnızca `@theme_*` türevlerini kabul et.

## 2026-03-07 - Tabs Visibility Regression Fix

- KDE/QML'de `Flickable` implicit height'a güvenip container implicitHeight bağlama; row görünmez olabilir.
- Tabs bileşenlerinde güvenli yaklaşım: `implicitHeight = max(rowHeightToken, contentRow.implicitHeight)`.
- Kullanıcı tab listesini net verdiğinde aynı anda tüm platformlarda (KDE + GNOME) tek kaynak setiyle eşitle.
- "Tabs görünmüyor" geri bildirimi geldiğinde ilk kontrol: render sırası değil, önce container height/clip davranışı.

## 2026-03-07 - Installed-Only Tabs Requirement

- Kullanıcı "sistemde yüklü olanlar görünsün" dediğinde disabled/grayed tab göstermek doğru değil; tab datası render öncesi filtrelenmeli.
- "Canonical tab list" yalnızca sıralama kaynağı olmalı; görünürlük kararı runtime provider availability ile verilmeli.
- Tabs görünürlüğü için hem data filtresi hem layout yüksekliği kritik: sadece birini düzeltmek yetmez.
- GNOME ve KDE'de aynı davranış kontratı korunmalı: installed-only tabs + selected tab state + header'dan önce yerleşim.

## 2026-03-07 - Avoid Over-Compaction On Tabs

- Tabs row compactlaştırılırken `rowHeight` + `vertical padding` aşırı düşürülmemeli; icon+label+mini-line kombinasyonunda clip oluşur.
- Kesilme şikayetinde ilk bakılacaklar: `rowHeight`, button `min-height`, `padding`, ve container `implicitHeight`.
- Görsel kalite için güvenli alt sınır: tabs button en az 21px yükseklik (bu projedeki tipografi/ikon setinde).

## 2026-03-07 - Tab Pill Clipping Root Cause

- Tabs içeriği (icon + label + mini-line) varken buton yüksekliğini sabit token'a kilitleme; özellikle farklı font metriklerinde clipping kaçınılmaz olur.
- Güvenli desen: `implicitHeight = max(baseRowHeight, contentImplicit + verticalPaddings)`.
- UI bug tekrarında önce spacing/token artırmak yerine layout constraint'i (sabit yükseklik) kaldır.

## 2026-03-07 - Account-Aware Provider State (Codex)

- Provider state key'lerini sadece provider-id bazında tutmak account switch bug'ı üretir; account identity (`account_id`) state'e dahil edilmek zorunda.
- `refresh` sadece usage çekmemeli; her poll'da active identity de yeniden resolve edilmeli (`~/.codex/auth.json`).
- Account switch anında eski session snapshot'ını göstermek yerine cutoff sonrası event beklemek daha güvenli: yanlış "limit dolu" göstermektense geçici "usage unavailable" doğru davranıştır.
- Local usage hesapları da aynı invalidation cutoff'una bağlanmalı; aksi halde ana metrik temizlenip alt metrikte eski account verisi kalır.

## 2026-03-07 - Provider-Genel Identity Fingerprint Katmanı

- Account switch bug'ı tek provider fix'i ile sınırlı bırakılmamalı; collector seviyesinde provider/account/source/session identity normalize edilip fingerprint üretilmeli.
- `metadata.identity` alanı UI/debug için tek güvenilir kaynak olmalı; popup-vm bu identity payload'ı doğrudan taşımalı.
- Identity fingerprint değişiminde güvenli varsayım: ilk çevrimde metrikleri invalidate et, ikinci çevrimde yeni identity verisini göster.
- Identity state dosyası testlerde izole edilmezse flaky yan etki üretir; `AI_USAGE_MONITOR_STATE_DIR` gibi override ile test izolasyonu zorunlu.

## 2026-03-07 - Cache Invalidation > TTL

- Account switch problemi TTL artırarak çözülmez; provider aynı kalsa bile account/source/session fingerprint değişimi ayrı invalidation olayıdır.
- UI polling cache'i (GNOME/KDE son popup payload) identity change sinyalini aldıktan sonra kısa gecikmeli force-refresh tetiklemeli.
- Refresh sırasında eski metrikleri ekranda tutmak yerine açık "Refreshing account..." copy'siyle geçici unavailable state gösterilmelidir.
- Invalidation sırasında model-bucket gibi türetilmiş alanlar da temizlenmeli; aksi halde ana metrik temizlenip alt satırda stale data kalır.

## 2026-03-07 - Two-Phase Refresh Pipeline

- Account-aware sistemde tek fazlı `collect -> render` akışı yetersiz kalabilir; güvenli yaklaşım `identity detect` ve `usage refetch` fazlarını ayırmaktır.
- Collector seviyesinde identity değişimi tespit edilince aynı cycle içinde sadece etkilenen provider için ikinci fetch yapılmalı (global double-fetch değil).
- UI tarafında force-refresh fallback tutulmalı; backend phase-2 başarısızsa kullanıcıya stale yerine kısa refresh state gösterilir.

## 2026-03-07 - CLI Detection Must Be Shell-Independent

- Extension/plasmoid süreçleri kullanıcı terminal PATH'ini birebir taşımayabilir; `shutil.which` tek başına install detection için yeterli değil.
- CLI provider detection için ortak resolver kullanılmalı: `PATH + kullanıcı bin fallback dizinleri + env override`.
- Aynı kurulumda auth/usage verisi `~/.local/share/...` veya `~/.config/...` altında olabilir; tek path'e kilitlenmek provider'ı yanlışlıkla `installed=false` yapar.
- Tabs görünürlüğü backend `installed && enabled` filtresine bağlı olduğu için detection bug'ı doğrudan UI'da "provider hiç yok" semptomu üretir; fix mutlaka provider katmanında yapılmalı.

## 2026-03-07 - KDE Settings Structure Cleanup

- Settings ekranında hizalama kalitesi için label/control sütunları açıkça tanımlanmalı; serbest RowLayout zamanla dağınık görünüm üretiyor.
- Provider listelerinde tekrar eden satır yapısı ayrı bir component'e taşınmalı; aksi halde spacing ve kolon hizası satırlar arasında drift eder.
- Expand içeriğinde form alanları da ana satır ile aynı grid mantığında tutulmalı, yoksa “debug form” hissi geri geliyor.
- Compact his için en güvenli yol: section arası boşlukları azaltıp component içi paddings’i korumak; padding’i agresif azaltmak native hissi bozar.

## 2026-03-07 - Enable/Disable Must Drive Visibility

- Kullanıcı açısından settings `enabled` ana görünürlük anahtarıdır; `installed` ile birlikte filtrelemek "enable ettim ama görünmüyor" hatası üretir.
- Kurulu olmayan ama enabled provider'lar gösterilecekse sıralamada sona atılmalı, aktif çalışan provider'ların önüne geçmemeli.
- Overview gibi özet bloklar kurulu provider'larla sınırlandırılmalı; aksi halde boş/yarım kart gürültüsü oluşur.
- Bu davranış için popup-vm seviyesinde test kilidi şart: `enabled & !installed => visible`, `disabled & installed => hidden`.

## 2026-03-07 - GNOME Prefs Readability Pass

- GNOME prefs'te çok sayıda `SwitchRow` lineer akışı yerine kompakt grid seçim alanı, çok provider senaryosunda taranabilirliği ciddi artırır.
- Provider satırlarını tek helper fonksiyonunda üretmek (`createProviderConfigExpander`) hizalama ve spacing drift'ini azaltır.
- Settings için popup stylesheet'i ile karışmamak adına ayrı `prefs.css` kullanmak güvenli; yalnız margin/padding ince ayarlarını burada yapmak gerekir.
- Alt action alanı ayrı group olarak verildiğinde sayfa hiyerarşisi netleşiyor; reload gibi bakım aksiyonları form kontrolleriyle karışmıyor.

## 2026-03-07 - Canonical Source Model Contract

- Provider source bilgisini yalnız `source` string'i ile taşımak UI'da belirsizlik üretir; canonical source model (`preferred/active/available/fallback/auth`) şart.
- `renderer string üretmesin` kuralı için `sourceLabel` ve `sourceDetails` presentation katmanında (popup-vm/state) üretilmeli.
- Source mode netliği için `canonicalMode` alanı kullanılmalı: `local_cli | api | hybrid | unavailable`.
- Settings ve popup aynı source contract'ı kullanmalı; ayrı ayrı string birleştirmek drift ve tutarsızlık oluşturur.

## 2026-03-07 - Snapshot Kimliği Provider+Account+Source Olmalı

- Snapshot key sadece provider veya tek fingerprint üstünden tutulursa aynı provider içindeki account/source switch senaryosunda stale veri sızar.
- Güvenli model: `stateKey = providerId + accountFingerprint + sourceMode`; restore/invalidation kararları bu state kimliğine bağlanmalı.
- `accountFingerprint` ayrı alan olarak yayınlanmalı; `identityFingerprint` state fingerprint olarak kalabilir (UI mismatch detection bozulmaz).
- popup-vm contract'ı yeni kimliği düz alanlarda da taşımalı (`accountFingerprint`, `sourceMode`, `stateIdentityKey`) ki renderer policy kararı presentation katmanından alsın.

## 2026-03-07 - Switch Sonrası Re-fetch Kuralı

- `identityChanged` tek başına re-fetch tetiklemek için yetersiz; fingerprint switch olup snapshot restore edilen akışlarda da zorunlu re-fetch gerekebilir.
- Güvenli policy: identity fingerprint değiştiyse (`switched`) ikinci faz fetch çalışmalı; yanlış account/source state riski performanstan daha kritik.
- Renderer’da mismatch map ile force-switching yapmak UI’da boş/yanıltıcı blok üretebilir; switching görünümü yalnız popup-vm `switchingState` contract’ından sürülmeli.
- Switching copy generic kalmamalı; account/source ayrımını VM katmanında üretmek KDE/GNOME semantik parity’sini korur.

## 2026-03-07 - Provider Status Incident Semantics

- Provider status incident durumu source/auth problemlerinden ayrı tutulmalı; aksi halde kullanıcı “limit/source” ile “provider outage” durumlarını karıştırıyor.
- Incident payload yoksa varsayılan indicator `unknown` olmamalı; `none` seçilmezse false-positive incident badge üretiliyor.
- Popup VM tarafında `statusState` (machine) ve `statusPresentation` (render-ready) ayrımı KDE/GNOME parity’sini korumayı kolaylaştırıyor.
- Compact indicator sadece usage tonuna bakmamalı; aktif incident varsa warn/error tonu usage yüzdesini override etmeli.

## 2026-03-07 - Settings Bilgi Mimarisi Netliği

- Settings ekranında section isimleri generic/debug kokuyorsa kullanıcı mental modeli bozuluyor; `General / Overview / Providers / Footer actions` gibi sabit hiyerarşi daha anlaşılır.
- Overview açıklaması mutlaka “overview seçimi normal enabled tabs’ten bağımsızdır” mesajını açık vermeli; aksi halde enable/overview kavramları karışıyor.
- Provider satırında source farkı gizli kalmamalı: en az `preferred + active + status` satır üstünde görünmeli, detay satırına gömülmemeli.
- Footer action butonları provider listesi içinde bırakılırsa form/debug hissi artıyor; ayrı section native settings algısını güçlendiriyor.

## 2026-03-07 - Provider Rows Productized

- Provider row’da `sourceDetails` gibi uzun/debug içerik subtitle’a direkt basılmamalı; kısa “readiness” subtitle ve ayrı source/status katmanı daha taranabilir.
- Full provider name ve küçük status text birlikte kullanılınca kullanıcı “hangi provider + hangi source” bilgisini tek bakışta alabiliyor.
- Status bilgisini chip yağmuruna çevirmek yerine tek satır kısa text (KDE) veya tek summary badge (GNOME) yoğunluğu düşürüyor.
- Enabled state switch yanında text label ile verilirse row semantics’i güçleniyor; sadece switch ikonuna bırakmak zayıf kalıyor.

## 2026-03-07 - Popup Header Source Semantics

- Header’da source bilgisi renderer’da string birleştirilmemeli; canonical `sourcePresentation` alanları VM’den gelmeli.
- `activeSourceLabel` için teknik tokenlar (`cli/api/web`) yerine kullanıcı semantiği (`Local CLI/API/Hybrid/Fallback/Unavailable`) daha doğru.
- Source reason satırı kısa kalmalı; uzun strategy debug metni popup’ı utility panel hissinden çıkarıyor.
- Subtitle’da source bilgisini ikinci kez tekrar etmek kalabalık yapar; source badge + kısa reason tek authoritative katman olmalı.

## 2026-03-07 - Parity Hardening Requires Fallback Paths

- Renderer tarafında `enabledProviderIds` varken tab payload eksik gelebilir; provider payload tab fallback’i olmadan enabled provider görünürlüğü kırılır.
- Identity mismatch sadece refresh timer’a bırakılırsa kısa sürede stale detail render görülebilir; mismatch anında force-switching state daha güvenli.
- Force switching UI’sı fallback title/message üretmezse boş blok riski var; ara durum copy’si her zaman garanti edilmeli.
- Settings parity için source-aware bilgi yalnız expand içine saklanmamalı; satırda kısa reason text görünürlüğü taranabilirliği artırıyor.
- Popup header source reason satırı wrap olursa compact utility hissi bozuluyor; iki renderer’da da tek satır + ellide davranışı parity için daha güvenli.

## 2026-03-07 - Health Gates Need Runtime-Aware Syntax Adapters

- `node --check` tek başına QML JS dosyalarını (`.pragma library`) yanlış negatifle kırabiliyor; gate içinde küçük bir sanitize adımı şart.
- Quality contract sabitleri test ve script içinde ayrı kopyalanırsa drift kaçınılmaz; tek shared contract modülü daha güvenli.
- Type-ish kapıyı tüm repo’ya bir anda zorlamak riskli; önce core sınırındaki kritik public fonksiyonlar üzerinde incremental zorunluluk en düşük riskli yaklaşım.
- Complexity kontrolünü sadece file line budget ile bırakmak yetersiz; function-level budget eklemek monolith fonksiyon büyümesini erken yakalıyor.
- Regression fixture’ı tam payload snapshot yerine projection bazında tutulursa hem stabil hem davranış odaklı oluyor.

## 2026-03-07 - Cross-Stack Quality Gates Need Tool Discovery

- Python tooling komutları sistem Python’a bağlanırsa PEP668 ortamlarında kırılıyor; repo-local `.venv/bin` öncelikli tool çözümleme daha güvenli.
- GNOME tarafı için `node --check` yeterli değil; `eslint` kapısı eklenmeden JS kalite standardı Python/QML ile eşitlenmiyor.
- `npm ci` adımı olmadan CI’da JS lint gate güvenilmez; Node bağımlılığı explicit install edilmeli.
- Pre-commit hook entry’leri ortam varsayımına bırakılmamalı; `.venv` Python’a pin etmek local tutarlılığı artırıyor.
- Eski kod tabanında formatter check’i bir anda strict yapmak büyük churn yaratabiliyor; incremental geçişte önce görünür warning, sonra kademeli strictleşme daha pratik.

## 2026-03-07 - Core Boundary Hardening With Compatibility Shims

- Büyük core dosyaları bölünürken en düşük riskli yol: yeni modülleri çıkarıp eski import yollarını shim ile canlı tutmak.
- `util.py` gibi çok amaçlı helper dosyaları tek seferde silmek yerine `shared/*` modüllerine taşıyıp shim ile kademeli geçmek regression riskini düşürüyor.
- `popup_vm.py` içindeki helper kümeleri (identity/status/pace) ayrı modüllere alınca testlerde davranış parity’si kolay doğrulanıyor ve dosya zihinsel yükü düşüyor.
- Public API sınırını `api.py` ile explicit yapmak, iç modül refactor’larında dış bağımlılıkları kırmadan ilerlemeyi kolaylaştırıyor.
- Type-ish gate kullanan repoda shim dosyaları sadece `import ... as ...` olmamalı; gerekli fonksiyonlar typed wrapper olarak tanımlanmalı.

## 2026-03-07 - KDE QML Health Hardening Execution Pattern

- KDE-only sağlık iyileştirmesinde en güvenli sıra: `qmllint` entegrasyonu -> lifecycle cleanup -> helper extraction -> token merkezileştirme.
- `P5Support.DataSource` kullanan QML dosyalarında `connectedSources` için explicit disconnect + `Component.onDestruction` cleanup eklenmeden lifecycle işi tamamlanmış sayılmamalı.
- Büyük QML dosyalarını davranış bozmadan küçültmenin düşük riskli yolu: saf hesaplama bloklarını `.js` helper modüllerine ayırıp QML tarafını declarative binding odaklı bırakmak.
- Hardcoded spacing/shape değerleri reusable bileşenlerde kaldıkça görsel drift oluşuyor; `PopupTokens.qml` genişletilip satır/simge/chip/divider kararları tek kaynağa çekilmeli.

## 2026-03-07 - Function Budget Gate Means More Than Formatting

- `ruff-format` temiz olsa bile `health_check` summary fail verebilir; `function-budgets` ayrı bir gate olarak ayrıca takip edilmeli.
- Uzayan orchestrator fonksiyonlarında en düşük riskli split deseni: mevcut hesaplama bloklarını pure helper’lara ayırıp public return contract’ı değiştirmemek.
- `budget` kaynaklı refactor sonrası minimum güvence seti: `project_health_check --mode quick` + modül odaklı test subset’i.

## 2026-03-07 - GNOME Extension Lifecycle Hardening

- GJS async refresh akışında `cancel` tek başına yeterli değil; stale callback overwrite riskine karşı request generation guard zorunlu.
- `PanelMenu.Button` yaşam döngüsünde uzun ömürlü signal id’leri (`menu`, `drawing area`, `settings`) explicit track+disconnect edilirse teardown audit’i kolaylaşıyor.
- Monolit tab/selection policy en düşük riskle ayrı modüle taşınabilir; renderer sınıfı sadece state + dispatch + actor compose sorumluluğunda kalmalı.
- CSS sınıf isimlerini builder bileşenleriyle alias ederek hizalamak, davranış bozmadan modüler refactor için güvenli bir ara adım sağlıyor.

## 2026-03-07 - Renderer Purity Requires VM-First Contracts

- Tab/switcher fallback policy renderer’da kalınca her platform kendi kuralını üretmeye başlıyor; `switcherTabs + selectableProviderIds` core contract olarak yayınlanmalı.
- Panel tone/percent/tooltip hesapları renderer’da tekrarlandığında drift kaçınılmaz; `popup.panel` gibi render-ready alanla tek kaynak yaklaşımı daha güvenli.
- Metric sıralamasını renderer’da yeniden üretmek (session/weekly/custom ayrıştırma) purity ihlalidir; core `provider.metrics` sırası authoritative olmalı.
- Helper dosyaları sadece “inceltmek” yetmez; kullanılmayan policy helperları repo’dan kaldırılmalı ki geri sızıntı olmasın.

## 2026-03-07 - Warning-First Complexity Guarding

- Complexity guard ilk aşamada fail yerine `WARN` üretmeli; aksi halde büyük mevcut dosyalar migration öncesi geliştirici akışını kilitler.
- Dosya boyutu eşiği tek tip olmamalı; orchestration, UI component ve config ekranları için ayrı sürdürülebilir eşikler gerekir.
- Fonksiyon karmaşıklığı ölçümü basit tutulabilir: `line count + branch points` kombinasyonu erken risk sinyali için yeterli.
- Gürültüyü kontrol etmek için complexity taraması önce hedef hotspot dosyalara sınırlandırılmalı, sonra kademeli genişletilmeli.

## 2026-03-07 - Safe-Boundary Calibration vs Rewrite

- Tüm alarm dosyalarını aynı gün parçalamak yerine warning-first guard eşiklerini mevcut mimari borcunu kilitleyecek seviyeye çekmek, delivery riskini düşürür.
- “Hepsini güvenli sınıra çek” isteğinde en güvenli incremental adım: mevcut boyutu aşmayacak sınırları tanımlayıp yeni büyümeyi erken yakalamaktır.
- Bu kalibrasyon geçici bir son durum değil; sonraki adımda dosyalar küçüldükçe eşikler tekrar aşağı çekilmelidir.

## 2026-03-07 - Thresholds Must Reflect Intended Design, Not Current Debt

- Guard eşiklerini mevcut büyük dosyalara göre fazla yukarı çekmek teknik borcu görünmez yapar.
- Kullanıcı hedefi net verdiğinde (`UI 80–200`, `orchestration 250+ alarm`) policy bu profile dönmelidir.
- Warning-first yaklaşımın amacı uyarıları kapatmak değil, kırmadan görünür hale getirmektir.
- İlk adımda alarm çok çıkması normaldir; bu liste doğrudan parçalama backlog’una dönüştürülmelidir.

## 2026-03-07 - Strict Threshold + Baseline Lock Strategy

- Büyük legacy dosyaları bir gecede parçalamadan “hata istemiyorum” hedefi için doğru model: strict eşikleri koruyup baseline lock ile sadece büyümeyi uyarılamak.
- Eşikleri yükseltmek yerine baseline map tutmak, hem teknik borcu görünür bırakır hem de yeni spagetti büyümesini engeller.
- Baseline doğrulaması testlerle kilitlenmeli (dosya varlığı + anahtar tutarlılığı), yoksa guard sessizce drift eder.

## 2026-03-07 - Baseline Lock + Real Refactor Together

- Baseline lock tek başına "done" sayılmamalı; teknik borç dosyaları fiilen sorumluluk modüllerine bölünmeden bakım riski düşmüyor.
- Guard token kontrolleri (örn. `gnome-lifecycle`, `typeish-signatures`) dosya içi imza/token aradığı için façade/mixin refactor sonrası bu kontratlar korunmalı.
- Güvenli pattern: önce monolit dosyayı orchestration façade haline indir, sonra iş kurallarını küçük modüllere taşı ve her modülü threshold altında tut.
- Refactor turu sonunda `ruff format` zorunlu; aksi halde health gate "format drift" ile tekrar kırılıyor.

## 2026-03-07 - Lifecycle Cleanup Must Cover Open/Close, Not Only Destroy

- Yalnız destroy cleanup yeterli değil; popup close anında da timer/rebuild zinciri kontrol edilmeli.
- Identity mismatch/fingerprint map'leri prune edilmezse provider seti değişimlerinde stale cache büyümesi oluşuyor.
- Parse/backend hata yolunda pending refresh timer'ı durdurulmazsa gereksiz refresh döngüsü devam ediyor.
- Güvenli ilk tur: davranış değiştirmeden lifecycle guard ekle (stop/prune/reset), sonra daha derin refactor'a geç.

## 2026-03-07 - Fixture Regression Must Track Live Contract

- Fixture sözleşmesi canlı popup-vm davranışından koparsa testler yanlış alarm verir; fixture beklentileri contract değişimiyle birlikte güncellenmeli.
- Descriptor parse testinde `usageDashboardBySource` anahtarları için sadece birebir `sourceModes` eşleşmesi zorlanmamalı; `auto` policy bu map’i genişletebilir.
- Cache invalidation davranışı sadece collector entegrasyon testlerinde dolaylı kalmamalı; helper düzeyinde (`changed_provider_ids`, `refresh_changed_provider_records`) doğrudan kilitlenmeli.
- Strateji dokümanı risk->test eşleşmesini açık tuttuğunda yeni provider/source davranışları eklenirken kapsam boşluğu daha erken yakalanıyor.

## 2026-03-07 - Ergonomic Dev Commands Reduce Drift

- Geliştirici onboarding için en düşük sürtünme: tek komut `make setup` (venv + deps + hooks).
- Hook entry doğrudan script çağırmak yerine `make lint` kullanınca local/CI komutları aynı kalıyor.
- `CONTRIBUTING.md` içinde kısa, zorunlu mimari kurallar (renderer purity, boundaries, state model) yazılı olmadığında aynı presentation logic tekrarları geri geliyor.
- README’de contribution rehberi linki görünür değilse ekip günlük komutları farklı yorumluyor; tek kaynağa referans şart.

## 2026-03-07 - Lint Coverage Must Follow File Growth

- GNOME tarafında dosyalar modüllere bölündükten sonra lint target listesi güncellenmezse health gate yeşil görünse bile dosyaların çoğu koruma dışında kalır.
- En güvenli model: lint/syntax hedeflerinde tek kaynak liste kullanmak (`GNOME_EXTENSION_JS_TARGETS`) ve diğer hedefleri bundan türetmek.
- Coverage drift’ini testle kilitlemek gerekir; yeni `*.js` dosyası eklenince target listesi güncellenmediyse test fail etmeli.
- `gjs-lint checked N files` çıktısı build log’unda görünür bir coverage sinyali olarak korunmalı.

## 2026-03-07 - Fake Typecheck Alias Is Not Acceptable

- `typecheck` komutunun health alias olması gerçek static sinyal üretmez; doğrudan mypy/pyright çalıştırması zorunlu.
- İlk geçişte tüm hataları bir günde çözmek yerine, `mypy.ini` içinde açık ve sınırlı typed-debt quarantine listesiyle incremental ilerlemek daha güvenli.
- Quarantine modülleri gizli kalmamalı; config dosyasında tek tek listelenip azaltma planına açık olmalı.
- CI ve pre-commit akışında typecheck ayrı bir kapı olarak görünmeli; yalnız lint içine gömülü kalmamalı.

## 2026-03-07 - Baseline Lock Must Not Hide Debt

- `line_count <= baseline => skip` yaklaşımı debt’i görünmez yapar; baseline yalnız sınıflandırma için kullanılmalı, görünürlüğü kapatmamalı.
- Doğru model: `LEGACY_DEBT_LOCKED`, `BASELINE_BREACH`, `NEW_DEBT` ayrımını aynı raporda açıkça vermek.
- “0 warnings” çıktısı ancak gerçekten görünür debt yoksa üretilmeli; aksi halde false-green algısı oluşur.
- Baseline değerleri monolit tarihsel tepe değerlerinde tutulmamalı; geçici tolerans + bir sonraki düşüş adımı birlikte tanımlanmalı.

## 2026-03-08 - Debt Reduction Turlarında Güvenli Split Kalıbı

- Büyük orchestrator fonksiyonlarını küçültmenin en güvenli yolu: `input normalization` + `runtime computation` + `payload assembly` katmanlarını ayrı helper’lara ayırmak.
- Baseline debt gerçekten ödendiğinde lock kaydını taşımak yerine kaldırmak/sıkılaştırmak gerekir; aksi halde ölçüm sinyali zayıflar.
- Refactor turunda `mypy` ile hızlı tip sinyali zorunlu; küçük annotation hataları (özellikle `incident` ve `error` tipleri) erken yakalanır.
- Faz bazlı doğrulama (lint + typecheck + hedef test) yapılmadan bir sonraki debt hedefinə geçmek regresyon riskini artırır.

## 2026-03-08 - Debt-Sıfır Durumu İçin Kalıcılık Politikası

- Debt sıfırlandıktan sonra baseline lock mekanizmasını boşaltmak, gelecekteki borcu “geçici lock” ile gizleme riskini keser.
- CI’da warning-fail (`--fail-on-warn`) açılmadan warning-first guard gerçek koruma üretmez; özellikle size/complexity sinyali için bu kritik.
- `mypy.ini` içinde `ignore_errors=True` satırı policy check ile yasaklanmalı; aksi halde quarantine borcu sessizce geri döner.
- Popup/settings regression için fixture tabanlı test eklemek, renderer semantic drift’ini lint/typecheck’in yakalayamadığı alanlarda erken tespit sağlar.
