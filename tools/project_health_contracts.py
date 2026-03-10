from __future__ import annotations

from pathlib import Path

# Conscious exclusion list for GNOME extension JS lint/syntax coverage.
# Keep this empty unless a file is generated/vendor and intentionally excluded.
GNOME_EXTENSION_JS_EXCLUDE: list[str] = []

_REPO_ROOT = Path(__file__).resolve().parents[1]
_GNOME_EXTENSION_ROOT = _REPO_ROOT / "gnome-extension" / "aiusagemonitor@aimonitor"


def _discover_gnome_extension_js_targets() -> list[str]:
    excluded = set(GNOME_EXTENSION_JS_EXCLUDE)
    targets: list[str] = []
    for path in sorted(_GNOME_EXTENSION_ROOT.rglob("*.js")):
        if not path.is_file():
            continue
        if "node_modules" in path.parts:
            continue
        rel_path = path.relative_to(_REPO_ROOT).as_posix()
        if rel_path in excluded:
            continue
        targets.append(rel_path)
    return targets


GNOME_EXTENSION_JS_TARGETS = _discover_gnome_extension_js_targets()

JS_SYNTAX_TARGETS = [
    *GNOME_EXTENSION_JS_TARGETS,
    "com.aiusagemonitor/contents/ui/ConfigPresentation.js",
    "com.aiusagemonitor/contents/ui/ConfigBackend.js",
    "com.aiusagemonitor/contents/ui/PopupVmSelection.js",
]

GJS_LINT_TARGETS = [*GNOME_EXTENSION_JS_TARGETS]

SHELL_TARGETS = [
    "com.aiusagemonitor/install.sh",
    "com.aiusagemonitor/upgrade.sh",
    "gnome-extension/aiusagemonitor@aimonitor/install.sh",
]

RENDERER_FILES = [
    "gnome-extension/aiusagemonitor@aimonitor/extension.js",
    "gnome-extension/aiusagemonitor@aimonitor/prefs.js",
    "com.aiusagemonitor/contents/ui/FullRepresentation.qml",
    "com.aiusagemonitor/contents/ui/ProviderDetailSection.qml",
    "com.aiusagemonitor/contents/ui/PopupHeader.qml",
    "com.aiusagemonitor/contents/ui/configGeneral.qml",
]

RENDERER_FORBIDDEN_TOKENS = [
    "ProviderRegistry(",
    "collect_all(",
    "apply_identity_to_provider(",
    "resolve_provider_source_plan(",
    "load_identity_store(",
]

CORE_FORBIDDEN_TOKENS = [
    "resource:///org/gnome/shell",
    "import QtQuick",
    "org.kde.plasma",
]

FILE_LINE_BUDGETS = {
    "gnome-extension/aiusagemonitor@aimonitor/extension.js": 1700,
    "gnome-extension/aiusagemonitor@aimonitor/prefs.js": 900,
    "core/ai_usage_monitor/presentation/popup_vm.py": 1500,
    "com.aiusagemonitor/contents/ui/configGeneral.qml": 1100,
    "com.aiusagemonitor/contents/ui/FullRepresentation.qml": 450,
}

PYTHON_FUNCTION_LINE_BUDGETS = {
    "core/ai_usage_monitor/presentation/popup_vm.py": 120,
    "core/ai_usage_monitor/collector.py": 90,
    "core/ai_usage_monitor/identity.py": 125,
    "core/ai_usage_monitor/source_strategy.py": 90,
}

TYPE_SIGNATURE_TARGETS = {
    "core/ai_usage_monitor/collector.py": [
        "collect_all",
        "collect_legacy_usage",
        "collect_state_payload",
        "collect_popup_vm_payload",
    ],
    "core/ai_usage_monitor/source_strategy.py": [
        "resolve_provider_source_plan",
    ],
    "core/ai_usage_monitor/identity.py": [
        "apply_identity_to_provider",
    ],
    "core/ai_usage_monitor/presentation/popup_vm.py": [
        "build_popup_view_model",
    ],
}

LIFECYCLE_CONTRACT_RULES = {
    "gnome": {
        "gnome-extension/aiusagemonitor@aimonitor/extension.js": {
            "required_tokens": [
                "destroy() {",
                "this._destroyed = true;",
                "this._refreshGeneration += 1;",
                "this._clearIdentityRefreshTimeout();",
                "this._clearRefreshTimeout();",
                "this._activeProcess.force_exit();",
                "this._settings.disconnect(this._settingsChangedId);",
                "this._disconnectSignal(this.menu, this._menuOpenStateChangedId);",
                "this._disconnectSignal(this._panelRing, this._panelRingRepaintId);",
                "this._resetBoxChildren(this._contentBox);",
                "this._resetBoxChildren(this._switcherBox);",
                "this._popupVm = {};",
                "this._popupProviders = [];",
                "this._lastRenderedIdentityByProvider = {};",
            ],
            "forbidden_tokens": [],
            "warn_tokens": [],
        },
        "gnome-extension/aiusagemonitor@aimonitor/indicatorLifecycleMixin.js": {
            "required_tokens": [
                "this._timeoutId = GLib.timeout_add_seconds(",
                "this._identityRefreshTimeoutId = GLib.timeout_add(",
                "this._cancellable.cancel();",
                "this._activeProcess = null;",
                "GLib.source_remove(this._timeoutId);",
                "GLib.source_remove(this._identityRefreshTimeoutId);",
                "_pruneIdentityCaches(providers);",
                "if (this._destroyed || refreshGeneration !== this._refreshGeneration)",
                "this._refresh(false);",
                "this._refresh(true);",
                "argv.push('--force');",
            ],
            "forbidden_tokens": [],
            "warn_tokens": [],
        },
        "gnome-extension/aiusagemonitor@aimonitor/indicatorContentFlowMixin.js": {
            "required_tokens": [
                "if (this._destroyed || !this._contentBox)",
                "if (this._destroyed || !this._switcherBox)",
                "box.destroy_all_children();",
                "this._switcherBox.add_child(this.buildProviderTabsRow());",
                "this.menu.box.queue_relayout();",
            ],
            "forbidden_tokens": [],
            "warn_tokens": [],
        },
    },
    "kde": {
        "com.aiusagemonitor/contents/ui/main.qml": {
            "required_tokens": [
                "P5Support.DataSource {",
                "disconnectSource(sourceName)",
                "Timer {",
                "id: refreshTimer",
                "id: identityRefreshTimer",
                "Component.onDestruction:",
                "refreshTimer.stop()",
                "identityRefreshTimer.stop()",
                "root.disconnectRunnerSources()",
                "onExpandedChanged:",
                "root.refresh(false)",
                "root.refresh(true)",
                'command += " --force"',
            ],
            "forbidden_tokens": [],
            "warn_tokens": [
                "Connections {",
            ],
        },
        "com.aiusagemonitor/contents/ui/configGeneral.qml": {
            "required_tokens": [
                "P5Support.DataSource {",
                "disconnectSource(sourceName)",
                "Component.onDestruction:",
                "Component.onCompleted: loadSharedConfig()",
                "disconnectPendingCommands()",
            ],
            "forbidden_tokens": [],
            "warn_tokens": [
                "Connections {",
            ],
        },
        "com.aiusagemonitor/contents/ui/FullRepresentation.qml": {
            "required_tokens": [
                "Component.onCompleted: syncSelectedProvider()",
                "onTabsModelChanged: syncSelectedProvider()",
                "onPopupDataChanged: syncSelectedProvider()",
            ],
            "forbidden_tokens": [],
            "warn_tokens": [],
        },
    },
}

# Backward-compatible flat list for older tests/checks.
GNOME_LIFECYCLE_REQUIRED_TOKENS = [
    token
    for rule in LIFECYCLE_CONTRACT_RULES["gnome"].values()
    for token in rule.get("required_tokens", [])
]

# Warning-first size/complexity policy.
# These thresholds emit WARN in health checks (not FAIL) to allow incremental cleanup.
FILE_SIZE_WARNING_THRESHOLDS = {
    # Orchestration files: alarm early when file keeps growing.
    "gnome-extension/aiusagemonitor@aimonitor/extension.js": {
        "warn_lines": 220,
        "alarm_lines": 250,
        "category": "orchestration",
    },
    "gnome-extension/aiusagemonitor@aimonitor/prefs.js": {
        "warn_lines": 220,
        "alarm_lines": 250,
        "category": "orchestration",
    },
    "core/ai_usage_monitor/presentation/popup_vm.py": {
        "warn_lines": 220,
        "alarm_lines": 250,
        "category": "orchestration",
    },
    "core/ai_usage_monitor/identity.py": {
        "warn_lines": 220,
        "alarm_lines": 250,
        "category": "orchestration",
    },
    "core/ai_usage_monitor/collector.py": {
        "warn_lines": 220,
        "alarm_lines": 250,
        "category": "orchestration",
    },
    # UI components: keep medium-sized and composable.
    "com.aiusagemonitor/contents/ui/FullRepresentation.qml": {
        "warn_lines": 150,
        "alarm_lines": 200,
        "category": "ui-component",
    },
    "com.aiusagemonitor/contents/ui/CompactRepresentation.qml": {
        "warn_lines": 150,
        "alarm_lines": 200,
        "category": "ui-component",
    },
    "com.aiusagemonitor/contents/ui/ProviderDetailSection.qml": {
        "warn_lines": 150,
        "alarm_lines": 200,
        "category": "ui-component",
    },
    "com.aiusagemonitor/contents/ui/PopupHeader.qml": {
        "warn_lines": 150,
        "alarm_lines": 200,
        "category": "ui-component",
    },
    "com.aiusagemonitor/contents/ui/configGeneral.qml": {
        "warn_lines": 170,
        "alarm_lines": 220,
        "category": "ui-config",
    },
}

# Baseline lock policy: debt has been reduced to zero, new baseline locks are disallowed.
FILE_SIZE_BASELINE_REDUCTION_PLAN: dict[str, dict[str, int | str]] = {}

# Legacy debt baselines are temporary tolerance ceilings.
# Values come from FILE_SIZE_BASELINE_REDUCTION_PLAN and are still reported as debt.
FILE_SIZE_WARNING_BASELINES = {
    key: int(value["temporary_baseline"])
    for key, value in FILE_SIZE_BASELINE_REDUCTION_PLAN.items()
}

PYTHON_FUNCTION_COMPLEXITY_WARN = {
    "warn_lines": 90,
    "alarm_lines": 120,
    "warn_branch_points": 16,
    "alarm_branch_points": 24,
}

PYTHON_COMPLEXITY_TARGET_FILES = [
    "core/ai_usage_monitor/presentation/popup_vm.py",
    "core/ai_usage_monitor/identity.py",
    "core/ai_usage_monitor/collector.py",
    "core/ai_usage_monitor/config.py",
    "core/ai_usage_monitor/sources/model.py",
    "core/ai_usage_monitor/sources/strategy.py",
    "core/ai_usage_monitor/providers/gemini.py",
    "core/ai_usage_monitor/providers/kilo.py",
    "core/ai_usage_monitor/providers/minimax.py",
    "core/ai_usage_monitor/providers/opencode.py",
]

# Legacy function complexity baselines are intentionally empty.
PYTHON_FUNCTION_COMPLEXITY_BASELINES: dict[str, dict[str, int]] = {}

MAX_ALLOWED_FILE_BASELINE_LOCKS = 0
MAX_ALLOWED_FUNCTION_BASELINE_LOCKS = 0

FORBIDDEN_MYPY_PATTERNS = (
    "ignore_errors = True",
    "ignore_errors=True",
)

SETTINGS_PRESENTATION_CANONICAL_FIELDS = (
    "sourceModeLabel",
    "activeSourceLabel",
    "preferredSourceLabel",
    "sourceStatusLabel",
    "fallbackLabel",
    "availabilityLabel",
    "statusTags",
    "sourceReasonLabel",
    "strategyLabel",
    "capabilitiesLabel",
    "subtitle",
)
