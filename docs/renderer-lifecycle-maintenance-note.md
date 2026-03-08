# Renderer Lifecycle Maintenance Note

- Yeni timer/signal eklerken aynı dosyada açık bir "cleanup point" bırak:
  - KDE: `Component.onDestruction` ve gerekiyorsa collapse akışı (`onExpandedChanged`).
  - GNOME: `destroy()` ve `open-state-changed` close dalı.
- Cache map/object tutuyorsan her refresh sonrasında aktif provider seti dışını prune et.
- Popup kapalıyken pahalı UI rebuild yapma; sadece state güncelle, UI build'i open anına bırak.
- Parse/backend hata akışlarında "pending refresh" flag/timer zincirini mutlaka kır.
- Kod review'da lifecycle diff kontrolü zorunlu: `connect/timeout_add/connectSource` eklendiyse karşılık `disconnect/source_remove/disconnectSource` da aynı PR'da olmalı.
