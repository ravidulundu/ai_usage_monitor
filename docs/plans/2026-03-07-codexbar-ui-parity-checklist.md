# CodexBar UI Parity Checklist (Linux)

Date: 2026-03-07  
Scope: KDE plasmoid + GNOME extension popup and panel behavior parity against CodexBar docs.

## Reference Sources

- `docs/reference/codexbar/ui.md`
- `docs/reference/codexbar/widgets.md`
- `docs/reference/codexbar/icon.md`
- `docs/reference/codexbar/configuration.md`
- `docs/reference/codexbar/providers.md`

## Status Legend

- `done`: Implemented and validated in current Linux codebase.
- `partial`: Exists but differs from reference behavior/copy or is incomplete.
- `todo`: Not implemented yet.

## Checklist

| Area | Requirement | KDE | GNOME | Notes |
| --- | --- | --- | --- | --- |
| Top switcher | Provider tabs shown horizontally, clickable | done | done | Both popups now use provider tabs and selected detail view. |
| Top switcher | Overview tab with up to 3 providers | done | done | Shared `overviewProviderIds` config wired to KDE + GNOME switchers (`max=3`). |
| Top switcher | Hide Overview when no providers selected | done | done | Both UIs hide Overview tab when selection list is empty. |
| Panel behavior | Single panel item with selected or auto provider | done | done | `panelTool=auto` support added. |
| Panel icon | 18x18 critter bars (5h top + weekly hairline) | todo | todo | Current Linux panel uses ring/percent style. |
| Panel icon | Show used vs remaining toggle | todo | todo | No UI toggle yet; percent currently shown as used. |
| Panel icon | Dim on refresh failure + incident overlay behavior | partial | partial | Error coloring exists; dim/overlay parity not exact. |
| Menu card | Session + Weekly rows with reset countdown | done | done | Core rows and countdown are present. |
| Menu card | Optional absolute reset clock display | todo | todo | No display mode for absolute reset yet. |
| Pace | Codex/Claude weekly pace model from docs | done | done | Deficit/reserve + runs out/lasts logic implemented. |
| Pace | Hide pace if <3% elapsed in weekly window | done | done | Implemented in both frontends. |
| Codex card | Credits row + "Buy Credits..." action | todo | todo | Requires provider-specific card section + action. |
| Web extras | OpenAI web-only rows (code review, breakdown submenu) | todo | todo | Not implemented in Linux UI yet. |
| Accounts | Token account switcher/stacked cards (up to 6) | todo | todo | Backend model support needed first. |
| Preferences | Overview tab providers (up to 3) setting | done | done | Shared config UI added on KDE and GNOME prefs; enforced to 3 selections. |
| Preferences | Global "Disable Keychain access" behavior | partial | partial | Per-provider cookie source exists; no global kill switch. |
| Preferences | Claude keychain prompt policy | todo | todo | Not present in Linux settings yet. |
| Provider links | Usage/status actions by source/auth mode | partial | partial | Improved for core providers; needs complete provider matrix. |
| Theme fidelity | Native desktop theme compliance | partial | partial | KDE uses Kirigami theme roles; GNOME popup still custom CSS heavy. |
| Icons | Unified provider icon source (`@lobehub/icons`) | done | done | Synced static SVG assets to both frontends. |

## Priority Work Queue

1. Add Codex credits row and `Buy Credits...` action in provider detail card.
2. Add reset display preference (`countdown` vs `absolute`) and wire to both frontends.
3. Finish provider action matrix (usage URLs/source-aware handling for all supported providers).
4. Decide panel icon parity strategy: keep Linux ring style or add optional CodexBar critter-bar mode.
5. Add GNOME prefs live-state fetch parity (`config-ui-state`) so provider subtitles/status can mirror KDE behavior.

## Acceptance Criteria

1. A single shared config can drive switcher behavior and overview-provider selection on KDE and GNOME.
2. Popup structure and copy are behaviorally equivalent to CodexBar `ui.md` for all supported providers.
3. Provider-specific sections degrade gracefully when data is missing (`error`, `auth required`, `not installed`).
4. No polling regressions or leaked subprocesses in popup refresh loops.
