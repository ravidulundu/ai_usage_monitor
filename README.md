# AI Usage Monitor

[![KDE Store](https://img.shields.io/badge/KDE_Store-Available-1D99F3?style=for-the-badge&logo=kde&logoColor=white)](https://www.pling.com/p/2348728/)

Linux desktop usage monitor for AI coding tools.

It ships as:

- a KDE Plasma widget
- a GNOME Shell extension
- a shared Python backend used by both UIs

The project shows a compact panel indicator and a popup with usage windows, reset timers, auth errors, and provider-specific details.

## Current Scope

This repo uses a shared cross-desktop backend and a descriptor-driven provider registry. KDE and GNOME read the same normalized JSON state instead of maintaining separate provider logic.

Only providers that currently have approved `@lobehub/icons` support are exposed in the product UI.

## Supported Providers

| Provider | Short Name | Source Modes | Notes |
| --- | --- | --- | --- |
| Amp | `Amp` | `web` | Cookie-based web usage parsing |
| Claude Code | `Claude` | `auto` | OAuth/local usage + status |
| OpenAI Codex | `Codex` | `auto` | Local session logs + rate limit windows |
| Gemini CLI | `Gemini` | `auto` | Local Gemini auth/settings + model-aware windows |
| GitHub Copilot | `Copilot` | `api` | GitHub API token |
| Vertex AI | `Vertex` | `oauth` | Google ADC / OAuth |
| OpenRouter | `OpenRouter` | `api` | API key |
| Ollama | `Ollama` | `web` | Cookie-based web usage parsing |
| OpenCode | `OpenCode` | `auto`, `cli`, `web` | Local-first (`auto`) with optional explicit web quota path |
| z.ai | `z.ai` | `api` | API-based usage |
| Kilo Code | `Kilo` | `auto`, `api`, `cli` | API or local auth file |
| MiniMax | `MiniMax` | `auto`, `web`, `api` | API or cookie-based web usage |

Currently hidden from the active UI surface:

- `Kiro`
- `JetBrains AI`
- `Warp`
- `Kimi K2`

They are intentionally not surfaced in the shipped UI because the current rule is: if a provider does not have an allowed icon source in the chosen icon system, it is not exposed in the desktop product.

These dormant providers are treated as archived implementations, not active runtime features. They are excluded from the shipped provider registry and fetch strategy surface.

## Platform Support

| Platform | Status | Notes |
| --- | --- | --- |
| KDE Plasma 6+ | Working | Primary desktop target |
| GNOME Shell 45+ | Working | Uses the same shared backend |

## Architecture

High-level layout:

- `core/ai_usage_monitor/`
  Shared backend, provider registry, normalized state model, config handling.
- `com.aiusagemonitor/`
  KDE Plasma widget.
- `gnome-extension/aiusagemonitor@aimonitor/`
  GNOME Shell extension.
- `docs/`
  Internal reference notes and planning documents.

Runtime flow:

1. KDE or GNOME requests data.
2. The Python backend reads local files, CLI output, API endpoints, or web/cookie sources.
3. The backend emits normalized JSON state.
4. The desktop UI renders panel and popup views from that state.

Shared config file:

- `~/.config/ai-usage-monitor/config.json`

Shared backend install location:

- `~/.local/share/ai-usage-monitor/core`

## Features

- Shared backend for KDE and GNOME
- Multi-provider normalized state model
- Compact panel indicator with selectable panel tool
- Popup usage cards with reset countdowns
- Provider-specific config in desktop settings
- Shared config between KDE and GNOME
- Status, auth, and error state rendering
- Local-first operation

## Development Quality Gates

For developer onboarding and concise engineering rules:

- [`CONTRIBUTING.md`](CONTRIBUTING.md)

Install dev dependencies once:

```bash
make setup
```

Root commands:

```bash
make check        # full checks + tests
make lint         # fast quality gates
make health-ci    # strict CI gates (fails on warnings)
make typecheck    # mypy static type check for core
make format       # apply Python formatting
make format-check # formatting validation only
make test         # pytest
make hooks-install
make hooks-run
```

Equivalent npm scripts:

```bash
npm run check
npm run lint
npm run typecheck
npm run format
npm run test
```

Pre-commit:

```bash
./.venv/bin/pre-commit install
./.venv/bin/pre-commit run --all-files
```

CI runs the strict gate:

```bash
make health-ci PYTHON=python
```

This gate includes syntax/lint/typecheck/test plus KDE/GNOME contracts and debt guardrails.

## Installation

### KDE Plasma 6

From this repo:

```bash
cd com.aiusagemonitor
./install.sh
```

Manual install:

```bash
kpackagetool6 --type Plasma/Applet --install /full/path/to/com.aiusagemonitor
```

Upgrade after changes:

```bash
kpackagetool6 --type Plasma/Applet --upgrade /full/path/to/com.aiusagemonitor
```

Restart Plasma shell if the widget does not refresh:

```bash
kquitapp6 plasmashell || true
nohup plasmashell --replace >/tmp/aiusagemonitor-plasmashell.log 2>&1 &
```

Add the widget:

1. Right-click the panel
2. `Add Widgets...`
3. Search for `AI Usage Monitor`
4. Add it to the panel

Preview in a separate window:

```bash
plasmawindowed com.aiusagemonitor
```

### GNOME Shell

From this repo:

```bash
cd gnome-extension/aiusagemonitor@aimonitor
bash install.sh
```

Then log out and back in.

Open GNOME preferences:

```bash
gnome-extensions prefs aiusagemonitor@aimonitor
```

## Configuration

Both desktops use the same shared config file:

```json
{
  "version": 1,
  "refreshInterval": 60,
  "providers": [
    { "id": "amp", "enabled": true, "source": "web" },
    { "id": "claude", "enabled": true, "source": "auto" },
    { "id": "codex", "enabled": true, "source": "auto" },
    { "id": "gemini", "enabled": true, "source": "auto" },
    { "id": "copilot", "enabled": true, "source": "api", "apiKey": "" },
    { "id": "vertexai", "enabled": true, "source": "oauth", "projectId": "" },
    { "id": "openrouter", "enabled": true, "source": "api", "apiKey": "" },
    { "id": "ollama", "enabled": true, "source": "web" },
    { "id": "opencode", "enabled": true, "source": "local_cli" },
    { "id": "zai", "enabled": true, "source": "api", "apiKey": "" },
    { "id": "kilo", "enabled": true, "source": "auto", "apiKey": "" },
    { "id": "minimax", "enabled": true, "source": "auto", "apiKey": "" }
  ]
}
```

Desktop settings expose:

- refresh interval
- panel tool
- panel display mode
- provider enable/disable
- provider source mode
- provider-specific fields such as API key, cookie source, or project ID

## CLI / Debugging

Legacy payload:

```bash
python3 com.aiusagemonitor/contents/scripts/fetch_all_usage.py
```

Normalized state payload:

```bash
python3 com.aiusagemonitor/contents/scripts/fetch_all_usage.py state | python3 -m json.tool
```

Shared config UI payload:

```bash
python3 com.aiusagemonitor/contents/scripts/fetch_all_usage.py config-ui | python3 -m json.tool
```

The standalone helper script also exists here:

- `bin/ai-usage-monitor-state`

## KDE Settings

KDE settings currently control:

- refresh interval
- panel tool
- display mode
- shared provider config

Panel tool labels intentionally use short names:

- `Claude`
- `Codex`
- `Gemini`
- `Copilot`
- `Vertex`

Provider-specific settings are shared with GNOME because they write to the same config file.

## Provider Sources

Broad source types used in the backend:

- `auto`
  Tries the provider's preferred local/API flow.
- `api`
  Uses an API key or token.
- `oauth`
  Uses local OAuth/ADC credentials.
- `web`
  Uses web usage pages and cookie-based access.
- `cli`
  Uses local CLI output.

## Troubleshooting

### KDE widget shows stale values

Open the popup once. The widget refreshes on popup open and on interval.

Manual restart:

```bash
kquitapp6 plasmashell || true
nohup plasmashell --replace >/tmp/aiusagemonitor-plasmashell.log 2>&1 &
```

### KDE widget not visible after install

```bash
kpackagetool6 --type Plasma/Applet --list | grep com.aiusagemonitor
```

### GNOME extension not visible

```bash
gnome-extensions list | grep aiusagemonitor
```

### Inspect backend output directly

```bash
python3 com.aiusagemonitor/contents/scripts/fetch_all_usage.py state | python3 -m json.tool
```

### qml-syntax fails in CI

Run the same command locally:

```bash
tools/run_qmllint.sh
```

The qml gate fails on real syntax/parse errors.  
Environment-only import-resolution warnings (common on headless CI images without full Plasma QML modules) are logged but not treated as syntax failures.

### Inspect current normalized provider list

```bash
python3 - <<'PY'
from core.ai_usage_monitor.providers.registry import ProviderRegistry
print(ProviderRegistry().list_ids())
PY
```

## Development Notes

- `README.md` should reflect the actual `ProviderRegistry`, not historical providers.
- Provider icons are sourced from `@lobehub/icons` / `@lobehub/icons-static-svg`.
- Providers without an allowed icon source are intentionally not surfaced in the UI.

## License

GPL-3.0-or-later
