# CodexBar Linux Port Design

**Date:** 2026-03-07

**Goal:** Port the core CodexBar experience to Linux by expanding AI Usage Monitor from a 3-provider widget into a multi-provider Linux product with a shared backend and thin KDE/GNOME frontends.

## Problem

The current repository is a small cross-desktop monitor:

- KDE Plasma plasmoid in `com.aiusagemonitor/`
- GNOME Shell extension in `gnome-extension/`
- Duplicated Python fetch logic in both platform folders

This structure is workable for three providers, but it will not scale to CodexBar-level scope:

- many providers
- multiple auth strategies per provider
- richer state such as incidents, stale data, overview, pace, credits, and provider-specific extras
- shared configuration across desktops

## Chosen Approach

Adopt a shared Linux core with thin UI clients.

### Rejected approach: grow each frontend independently

Keeping most logic inside the KDE and GNOME frontends would be faster in the short term, but provider logic, config handling, cache behavior, and error states would diverge quickly.

### Rejected approach: replace the repo with a single standalone tray app

That would discard the repo's current strength: native KDE and GNOME integration.

### Selected approach: shared backend plus thin frontends

Move provider fetching, configuration, normalization, and refresh scheduling into a shared Linux backend. KDE and GNOME will read normalized state and render it using platform-native UI.

## Target Architecture

### Shared backend

A shared backend layer owns:

- provider registry
- provider detection
- config loading and validation
- auth source selection
- refresh scheduling
- normalized state generation
- cache and stale-state handling
- debug and CLI output

### Frontend clients

KDE and GNOME become thin clients:

- request or read the latest normalized state
- render provider cards, overview, and panel summary
- send simple user actions such as refresh, provider selection, or opening settings

### Suggested repo evolution

Target layout:

- `core/`
- `providers/`
- `daemon/`
- `tests/`
- `com.aiusagemonitor/`
- `gnome-extension/`
- `docs/plans/`

The existing platform folders stay in place, but their data layer becomes a consumer of the shared backend instead of owning provider logic directly.

## Data Model

The backend produces one normalized state document.

```json
{
  "version": 1,
  "updatedAt": "2026-03-07T12:00:00Z",
  "providers": [
    {
      "id": "codex",
      "enabled": true,
      "installed": true,
      "authenticated": true,
      "status": "ok",
      "source": "cli",
      "displayName": "OpenAI Codex",
      "primaryMetric": {
        "kind": "window",
        "label": "5h",
        "usedPct": 42,
        "resetAt": "2026-03-07T15:00:00Z"
      },
      "secondaryMetric": {
        "kind": "window",
        "label": "7d",
        "usedPct": 61,
        "resetAt": "2026-03-10T00:00:00Z"
      },
      "extras": {
        "plan": "pro",
        "model": "gpt-5-codex"
      },
      "error": null,
      "incident": null
    }
  ]
}
```

### Why this model

- frontends can render all providers through a common contract
- provider-specific detail lives in `extras`
- future metric types such as `credits`, `monthly`, or `breakdown` can fit without breaking the UI contract
- auth, stale, and incident states become uniform across providers

## Provider Interface

Each provider should implement the same backend interface:

- `detect()` checks whether the provider can run on the machine
- `fetch(config, context)` retrieves raw source data
- `normalize(raw)` converts raw source data into the shared state format
- `get_actions()` exposes refresh/login/dashboard actions
- `get_status()` reports provider incident or health information

This avoids turning the shared backend into a large `if/else` script.

## Provider Rollout

The Linux port should not try to ship every CodexBar provider immediately.

### Wave 1

- `claude`
- `codex`
- `gemini`

These already exist in the repo and are the foundation for the backend extraction.

### Wave 2

- `openrouter`
- `kiro`
- `copilot`
- `vertexai`

These are relatively more Linux-friendly because they are CLI, OAuth, or API-key oriented.

### Wave 3

- `cursor`
- `augment`
- `amp`
- `factory`
- `opencode`

These involve browser cookies, session reuse, or web-account flows and need more Linux-specific handling.

## Configuration

Use one shared config file:

- `~/.config/ai-usage-monitor/config.json`

This file should contain:

- enabled providers
- preferred provider source (`auto|cli|oauth|api|web`)
- provider-specific fields such as API keys, cookie headers, workspace IDs, and regions
- refresh interval
- display mode
- overview provider selection
- notification thresholds

The backend should own config parsing and validation. Frontends should edit or consume this config, not define their own incompatible schemas.

## UI Direction

The Linux UI should preserve native desktop patterns while matching CodexBar functionality where it matters.

### KDE and GNOME should gain

- provider switcher
- overview mode
- richer provider cards
- shared error/auth/stale presentation
- countdown reset display
- optional absolute reset display later

### Linux-specific adaptation

Not every macOS behavior should be copied literally. Linux should aim for equivalent function, not pixel-for-pixel parity:

- no WidgetKit
- no macOS Keychain behavior
- browser-cookie features must use Linux-appropriate storage or manual cookie input
- menu bar behavior should map to KDE panel and GNOME top bar patterns

## Migration Plan

### Phase 1: backend extraction

Replace duplicated Python fetch scripts with a shared backend while preserving the current three providers.

### Phase 2: UI contract upgrade

Move KDE and GNOME to the normalized backend state and add switcher, overview, and unified card rendering.

### Phase 3: provider expansion

Add CodexBar-inspired providers in waves, starting with Linux-friendly integrations and leaving complex web-session providers for later.

## Risks

- browser-cookie providers will be more fragile on Linux than on macOS
- GNOME extensions are a poor place for complex provider logic, which is why the backend split is mandatory
- multi-provider growth will make observability critical; a CLI/debug path must exist from the start

## Success Criteria

The Linux port is successful when:

- KDE and GNOME read from one shared backend state
- the first three providers are fully migrated without regressions
- the UI supports provider switching and overview mode
- new providers can be added without duplicating frontend logic
- the project can grow toward CodexBar-level breadth without architecture drift
