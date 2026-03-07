# CodexBar Linux Port Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor AI Usage Monitor into a Linux-native CodexBar-style product with a shared backend, unified state model, and thin KDE/GNOME frontends.

**Architecture:** Move provider logic out of the KDE and GNOME folders into a shared Python backend that owns provider discovery, normalization, config, and refresh. Frontends read one normalized state payload and focus on rendering, settings, and lightweight actions.

**Tech Stack:** Python 3, JSON, KDE QML/Plasma, GNOME Shell JavaScript, pytest

---

### Task 1: Create the shared backend package skeleton

**Files:**
- Create: `core/ai_usage_monitor/__init__.py`
- Create: `core/ai_usage_monitor/models.py`
- Create: `core/ai_usage_monitor/config.py`
- Create: `core/ai_usage_monitor/state.py`
- Create: `tests/core/test_state_models.py`

**Step 1: Write the failing test**

```python
from ai_usage_monitor.models import ProviderState, MetricWindow


def test_provider_state_serializes_with_primary_and_secondary_metrics():
    state = ProviderState(
        id="codex",
        display_name="OpenAI Codex",
        enabled=True,
        installed=True,
        authenticated=True,
        status="ok",
        source="cli",
        primary_metric=MetricWindow(label="5h", used_pct=42, reset_at="2026-03-07T15:00:00Z"),
        secondary_metric=MetricWindow(label="7d", used_pct=61, reset_at="2026-03-10T00:00:00Z"),
    )

    data = state.to_dict()

    assert data["id"] == "codex"
    assert data["primaryMetric"]["label"] == "5h"
    assert data["secondaryMetric"]["label"] == "7d"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/core/test_state_models.py -v`
Expected: FAIL with import or attribute errors because the shared backend package does not exist yet.

**Step 3: Write minimal implementation**

```python
from dataclasses import dataclass


@dataclass
class MetricWindow:
    label: str
    used_pct: int
    reset_at: str | None

    def to_dict(self):
        return {
            "kind": "window",
            "label": self.label,
            "usedPct": self.used_pct,
            "resetAt": self.reset_at,
        }


@dataclass
class ProviderState:
    id: str
    display_name: str
    enabled: bool
    installed: bool
    authenticated: bool
    status: str
    source: str
    primary_metric: MetricWindow | None = None
    secondary_metric: MetricWindow | None = None

    def to_dict(self):
        return {
            "id": self.id,
            "displayName": self.display_name,
            "enabled": self.enabled,
            "installed": self.installed,
            "authenticated": self.authenticated,
            "status": self.status,
            "source": self.source,
            "primaryMetric": self.primary_metric.to_dict() if self.primary_metric else None,
            "secondaryMetric": self.secondary_metric.to_dict() if self.secondary_metric else None,
        }
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/core/test_state_models.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add core/ai_usage_monitor/__init__.py core/ai_usage_monitor/models.py core/ai_usage_monitor/config.py core/ai_usage_monitor/state.py tests/core/test_state_models.py
git commit -m "feat: add shared backend state models"
```

### Task 2: Build the provider interface and registry

**Files:**
- Create: `core/ai_usage_monitor/providers/__init__.py`
- Create: `core/ai_usage_monitor/providers/base.py`
- Create: `core/ai_usage_monitor/providers/registry.py`
- Test: `tests/core/test_provider_registry.py`

**Step 1: Write the failing test**

```python
from ai_usage_monitor.providers.registry import ProviderRegistry


def test_registry_returns_known_provider_ids():
    registry = ProviderRegistry()
    ids = registry.list_ids()

    assert "claude" in ids
    assert "codex" in ids
    assert "gemini" in ids
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/core/test_provider_registry.py -v`
Expected: FAIL because the provider registry does not exist yet.

**Step 3: Write minimal implementation**

```python
from dataclasses import dataclass


@dataclass
class ProviderDescriptor:
    id: str
    display_name: str


class ProviderRegistry:
    def __init__(self):
        self._providers = {
            "claude": ProviderDescriptor("claude", "Claude Code"),
            "codex": ProviderDescriptor("codex", "OpenAI Codex"),
            "gemini": ProviderDescriptor("gemini", "Gemini CLI"),
        }

    def list_ids(self):
        return list(self._providers.keys())
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/core/test_provider_registry.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add core/ai_usage_monitor/providers/__init__.py core/ai_usage_monitor/providers/base.py core/ai_usage_monitor/providers/registry.py tests/core/test_provider_registry.py
git commit -m "feat: add provider registry"
```

### Task 3: Move the current three providers into backend modules

**Files:**
- Create: `core/ai_usage_monitor/providers/claude.py`
- Create: `core/ai_usage_monitor/providers/codex.py`
- Create: `core/ai_usage_monitor/providers/gemini.py`
- Modify: `com.aiusagemonitor/contents/scripts/fetch_all_usage.py`
- Modify: `gnome-extension/aiusagemonitor@aimonitor/scripts/fetch_all_usage.py`
- Test: `tests/core/providers/test_claude_provider.py`
- Test: `tests/core/providers/test_codex_provider.py`
- Test: `tests/core/providers/test_gemini_provider.py`

**Step 1: Write the failing tests**

```python
from ai_usage_monitor.providers.codex import normalize_codex_rate_limits


def test_codex_normalization_returns_primary_and_secondary_windows():
    raw = {
        "rate_limits": {
            "primary": {"used_percent": 20, "resets_at": 1700000000},
            "secondary": {"used_percent": 55, "resets_at": 1700100000},
            "plan_type": "pro",
        }
    }

    state = normalize_codex_rate_limits(raw, model="gpt-5-codex")

    assert state.primary_metric.label == "5h"
    assert state.secondary_metric.label == "7d"
    assert state.source == "cli"
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/core/providers -v`
Expected: FAIL because provider modules do not exist yet.

**Step 3: Write minimal implementation**

Implement provider-specific modules for:

- reading Claude credentials and usage
- parsing Codex session JSONL files
- calling Gemini quota endpoints and token refresh logic

Update both platform wrapper scripts so they import the shared backend instead of duplicating provider logic.

**Step 4: Run tests to verify they pass**

Run: `pytest tests/core/providers -v`
Expected: PASS

**Step 5: Commit**

```bash
git add core/ai_usage_monitor/providers/claude.py core/ai_usage_monitor/providers/codex.py core/ai_usage_monitor/providers/gemini.py com.aiusagemonitor/contents/scripts/fetch_all_usage.py gnome-extension/aiusagemonitor@aimonitor/scripts/fetch_all_usage.py tests/core/providers
git commit -m "refactor: move existing providers into shared backend"
```

### Task 4: Add a shared state CLI entrypoint

**Files:**
- Create: `core/ai_usage_monitor/cli.py`
- Create: `bin/ai-usage-monitor-state`
- Test: `tests/core/test_cli_state_output.py`

**Step 1: Write the failing test**

```python
from ai_usage_monitor.cli import build_state_payload


def test_build_state_payload_includes_version_and_providers():
    payload = build_state_payload([])

    assert payload["version"] == 1
    assert payload["providers"] == []
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/core/test_cli_state_output.py -v`
Expected: FAIL because the CLI module does not exist yet.

**Step 3: Write minimal implementation**

```python
def build_state_payload(providers):
    return {
        "version": 1,
        "updatedAt": "1970-01-01T00:00:00Z",
        "providers": providers,
    }
```

Add a small executable wrapper that prints the shared backend state as JSON.

**Step 4: Run test to verify it passes**

Run: `pytest tests/core/test_cli_state_output.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add core/ai_usage_monitor/cli.py bin/ai-usage-monitor-state tests/core/test_cli_state_output.py
git commit -m "feat: add shared state cli"
```

### Task 5: Move KDE to the shared backend state

**Files:**
- Modify: `com.aiusagemonitor/contents/ui/main.qml`
- Modify: `com.aiusagemonitor/contents/ui/CompactRepresentation.qml`
- Modify: `com.aiusagemonitor/contents/ui/FullRepresentation.qml`
- Modify: `com.aiusagemonitor/contents/config/main.xml`
- Modify: `com.aiusagemonitor/contents/ui/configGeneral.qml`

**Step 1: Write the failing test**

Create a manual verification checklist file:

```markdown
# KDE verification

- Plasmoid loads provider state from shared backend wrapper
- Visible tools settings persist
- Existing Claude/Codex/Gemini cards still render
```

**Step 2: Run verification to confirm current gaps**

Run:

```bash
cd com.aiusagemonitor
./install.sh
```

Expected: the current implementation still uses duplicated provider logic and visible tool settings do not persist because schema entries are missing.

**Step 3: Write minimal implementation**

- point the KDE wrapper script at the shared backend CLI or shared Python module
- align QML with the normalized state model
- add missing schema entries for visible tool settings

**Step 4: Run verification to confirm behavior**

Run:

```bash
cd com.aiusagemonitor
./install.sh
```

Expected: KDE uses shared backend state, and popup visibility settings persist after reopening settings.

**Step 5: Commit**

```bash
git add com.aiusagemonitor/contents/ui/main.qml com.aiusagemonitor/contents/ui/CompactRepresentation.qml com.aiusagemonitor/contents/ui/FullRepresentation.qml com.aiusagemonitor/contents/config/main.xml com.aiusagemonitor/contents/ui/configGeneral.qml
git commit -m "feat: move kde frontend to shared backend state"
```

### Task 6: Move GNOME to the shared backend state

**Files:**
- Modify: `gnome-extension/aiusagemonitor@aimonitor/extension.js`
- Modify: `gnome-extension/aiusagemonitor@aimonitor/prefs.js`
- Modify: `gnome-extension/aiusagemonitor@aimonitor/schemas/org.gnome.shell.extensions.aiusagemonitor.gschema.xml`

**Step 1: Write the failing test**

Create a manual verification checklist file:

```markdown
# GNOME verification

- Extension reads normalized state from shared backend
- Parse or subprocess failures show a visible error state
- Provider settings still update the popup content
```

**Step 2: Run verification to confirm the current gap**

Run:

```bash
cd gnome-extension/aiusagemonitor@aimonitor
./install.sh
```

Expected: the extension still owns subprocess parsing directly and does not surface parse failures to the UI.

**Step 3: Write minimal implementation**

- change the extension to consume the shared backend payload
- add an explicit error state for subprocess or JSON parse failures
- keep provider toggles working against the new payload

**Step 4: Run verification to confirm behavior**

Run:

```bash
cd gnome-extension/aiusagemonitor@aimonitor
./install.sh
```

Expected: the extension renders shared backend state and exposes fetch/parsing failures clearly.

**Step 5: Commit**

```bash
git add gnome-extension/aiusagemonitor@aimonitor/extension.js gnome-extension/aiusagemonitor@aimonitor/prefs.js gnome-extension/aiusagemonitor@aimonitor/schemas/org.gnome.shell.extensions.aiusagemonitor.gschema.xml
git commit -m "feat: move gnome frontend to shared backend state"
```

### Task 7: Add CodexBar-style overview and provider switching

**Files:**
- Modify: `com.aiusagemonitor/contents/ui/CompactRepresentation.qml`
- Modify: `com.aiusagemonitor/contents/ui/FullRepresentation.qml`
- Modify: `gnome-extension/aiusagemonitor@aimonitor/extension.js`
- Modify: `gnome-extension/aiusagemonitor@aimonitor/prefs.js`
- Modify: `core/ai_usage_monitor/models.py`
- Modify: `core/ai_usage_monitor/config.py`

**Step 1: Write the failing test**

```python
from ai_usage_monitor.config import normalize_overview_provider_ids


def test_overview_provider_ids_are_limited_to_three_entries():
    ids = normalize_overview_provider_ids(["codex", "claude", "gemini", "openrouter"])
    assert ids == ["codex", "claude", "gemini"]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/core/test_overview_config.py -v`
Expected: FAIL because overview config normalization does not exist yet.

**Step 3: Write minimal implementation**

- add overview provider selection to shared config
- add provider switcher and overview rendering to KDE and GNOME
- ensure overview is hidden when no providers are selected

**Step 4: Run tests and manual verification**

Run:

```bash
pytest tests/core/test_overview_config.py -v
```

Expected: PASS

Then verify manually in KDE and GNOME that overview mode renders up to three providers.

**Step 5: Commit**

```bash
git add com.aiusagemonitor/contents/ui/CompactRepresentation.qml com.aiusagemonitor/contents/ui/FullRepresentation.qml gnome-extension/aiusagemonitor@aimonitor/extension.js gnome-extension/aiusagemonitor@aimonitor/prefs.js core/ai_usage_monitor/models.py core/ai_usage_monitor/config.py tests/core/test_overview_config.py
git commit -m "feat: add provider overview and switching"
```

### Task 8: Add the first Linux-friendly CodexBar providers

**Files:**
- Create: `core/ai_usage_monitor/providers/openrouter.py`
- Create: `core/ai_usage_monitor/providers/kiro.py`
- Create: `core/ai_usage_monitor/providers/copilot.py`
- Create: `core/ai_usage_monitor/providers/vertexai.py`
- Modify: `core/ai_usage_monitor/providers/registry.py`
- Test: `tests/core/providers/test_openrouter_provider.py`
- Test: `tests/core/providers/test_kiro_provider.py`
- Test: `tests/core/providers/test_copilot_provider.py`
- Test: `tests/core/providers/test_vertexai_provider.py`

**Step 1: Write the failing tests**

```python
from ai_usage_monitor.providers.openrouter import normalize_openrouter_credits


def test_openrouter_credit_usage_maps_to_primary_metric():
    state = normalize_openrouter_credits(total=10.0, used=4.5)
    assert state.primary_metric.label == "Credits"
    assert state.primary_metric.used_pct == 45
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/core/providers -v`
Expected: FAIL because the new provider modules do not exist yet.

**Step 3: Write minimal implementation**

- implement Linux-friendly providers first
- register them in the shared provider registry
- map their usage into the normalized metric model

**Step 4: Run tests to verify they pass**

Run: `pytest tests/core/providers -v`
Expected: PASS

**Step 5: Commit**

```bash
git add core/ai_usage_monitor/providers/openrouter.py core/ai_usage_monitor/providers/kiro.py core/ai_usage_monitor/providers/copilot.py core/ai_usage_monitor/providers/vertexai.py core/ai_usage_monitor/providers/registry.py tests/core/providers
git commit -m "feat: add first linux-friendly codexbar providers"
```

### Task 9: Add developer-facing docs and verification flow

**Files:**
- Modify: `README.md`
- Create: `docs/plans/verification-codexbar-linux-port.md`

**Step 1: Write the failing test**

Create a verification checklist that fails until all items can be checked manually:

```markdown
- shared backend state output works
- KDE renders shared backend state
- GNOME renders shared backend state
- overview mode works
- new providers can be enabled in config
```

**Step 2: Run verification to confirm gaps**

Run manual checks and note which items still fail.

**Step 3: Write minimal implementation**

- document the new backend layout
- document config path and format
- document how to debug provider output from the CLI

**Step 4: Run verification to confirm docs match reality**

Run:

```bash
python3 -m ai_usage_monitor.cli
```

Expected: JSON state output that matches the README examples and verification checklist.

**Step 5: Commit**

```bash
git add README.md docs/plans/verification-codexbar-linux-port.md
git commit -m "docs: document codexbar linux port architecture"
```
