## Summary

- What changed?
- Why was it needed?
- Which desktop surfaces are affected: KDE, GNOME, or both?

## Reviewer Focus

Please review this as a behavior and product-surface change, not as a cosmetic-only update.

- `ProviderRegistry` / backend surface
  Confirm the visible provider list matches product policy.
- Shared config behavior
  Confirm config normalization and provider settings behave correctly with existing user configs.
- KDE / GNOME parity
  Confirm both desktops follow the same provider/config rules.
- Panel behavior
  Confirm panel tool selection, short labels, and fallback behavior are correct.
- Popup behavior
  Confirm current values, reset timers, and error/auth states render correctly.
- Icon policy
  Confirm only approved provider icons are used and no legacy asset leakage remains.
- Data accuracy
  Confirm desktop UI values match backend/CLI values where applicable.

## Files Worth Reviewing

- `core/ai_usage_monitor/providers/registry.py`
- `core/ai_usage_monitor/collector.py`
- `core/ai_usage_monitor/config.py`
- `com.aiusagemonitor/contents/ui/CompactRepresentation.qml`
- `com.aiusagemonitor/contents/ui/FullRepresentation.qml`
- `com.aiusagemonitor/contents/ui/configGeneral.qml`
- `gnome-extension/aiusagemonitor@aimonitor/extension.js`
- `gnome-extension/aiusagemonitor@aimonitor/prefs.js`

## Manual QA Checklist

- KDE widget installs and opens correctly
- KDE settings open without layout regressions
- KDE panel tool selection behaves correctly
- KDE popup refreshes and shows current values
- GNOME extension installs and preferences open correctly
- GNOME panel indicator behaves correctly
- GNOME popup/provider list matches KDE behavior
- Existing config file upgrades without broken provider entries

## Validation

- [ ] Unit tests passed locally
- [ ] KDE checked manually
- [ ] GNOME checked manually
- [ ] Existing config migration checked

## Risks / Notes

- Call out any config migration behavior
- Call out removed providers or hidden providers
- Call out icon-source policy changes
- Call out any manual verification that still needs reviewer attention
