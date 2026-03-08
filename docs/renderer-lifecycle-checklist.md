# Renderer Lifecycle / Memory Checklist

## KDE Plasmoid Checklist

- [ ] `P5Support.DataSource` çağrılarında stale source kalmıyor (`disconnectSource` + teardown temizliği)
- [ ] `Timer` objeleri destroy ve collapse anında durduruluyor
- [ ] Popup refresh sırasında identity/mismatch cache map'leri aktif provider setine prune ediliyor
- [ ] Parse/output hatası durumunda pending refresh timer zinciri iptal ediliyor
- [ ] `Component.onDestruction` içinde büyük state payload'ları sıfırlanıyor
- [ ] Expand/collapse döngüsünde gereksiz refresh timer birikimi olmuyor

## GNOME Extension Checklist

- [ ] `open-state-changed` kapanışında identity-refresh timeout temizleniyor
- [ ] Popup kapalıyken gereksiz content rebuild yapılmıyor
- [ ] Refresh sonrası identity cache map'leri aktif provider setine prune ediliyor
- [ ] `destroy()` içinde cancellable/process/signal/timer temizliği tamamlanıyor
- [ ] `destroy()` içinde cached gicon/popup state map'leri sıfırlanıyor
- [ ] Rebuild edilen actor subtree'ler close sırasında `destroy_all_children` ile boşaltılıyor

## İlk Cleanup Turu (Uygulandı)

- KDE `main.qml`
  - `pruneIdentityCaches()` eklendi.
  - Parse/unsupported payload hata akışında `identityRefreshPending=false` ve `identityRefreshTimer.stop()` eklendi.
  - `Component.onDestruction` içinde popup/cache state reset eklendi.
  - Collapse (`onExpandedChanged`) durumunda identity refresh timer stop eklendi.

- GNOME `extension.js` + `indicatorLifecycleMixin.js`
  - Menu close anında identity timeout temizliği ve popup actor subtree boşaltma eklendi.
  - Menu closed iken `_updateContent()` rebuild'i engellendi.
  - `_setPopupData()` içinde identity cache prune eklendi.
  - `destroy()` içinde gicon cache ve popup state map reset eklendi.
