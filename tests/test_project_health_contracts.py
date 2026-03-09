from __future__ import annotations

from pathlib import Path

from tools.project_health_contracts import (
    FILE_LINE_BUDGETS,
    FILE_SIZE_BASELINE_REDUCTION_PLAN,
    FILE_SIZE_WARNING_BASELINES,
    FILE_SIZE_WARNING_THRESHOLDS,
    FORBIDDEN_MYPY_PATTERNS,
    GJS_LINT_TARGETS,
    GNOME_EXTENSION_JS_EXCLUDE,
    JS_SYNTAX_TARGETS,
    LIFECYCLE_CONTRACT_RULES,
    MAX_ALLOWED_FILE_BASELINE_LOCKS,
    MAX_ALLOWED_FUNCTION_BASELINE_LOCKS,
    PYTHON_COMPLEXITY_TARGET_FILES,
    PYTHON_FUNCTION_COMPLEXITY_BASELINES,
    PYTHON_FUNCTION_COMPLEXITY_WARN,
    RENDERER_FILES,
    RENDERER_FORBIDDEN_TOKENS,
    SETTINGS_PRESENTATION_CANONICAL_FIELDS,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def _assert_lifecycle_contract(group: str) -> None:
    group_rules = LIFECYCLE_CONTRACT_RULES[group]
    assert group_rules, f"Lifecycle contract group is empty: {group}"

    for rel_path, rule in group_rules.items():
        text = _read(rel_path)
        for token in rule.get("required_tokens", []):
            assert token in text, (
                f"{group} lifecycle missing token in {rel_path}: {token}"
            )
        for token in rule.get("forbidden_tokens", []):
            assert token not in text, (
                f"{group} lifecycle has forbidden token in {rel_path}: {token}"
            )


def test_gnome_lifecycle_contract_tokens_exist():
    _assert_lifecycle_contract("gnome")


def test_kde_lifecycle_contract_tokens_exist():
    _assert_lifecycle_contract("kde")


def test_lifecycle_warn_tokens_are_declared_per_file():
    for group, group_rules in LIFECYCLE_CONTRACT_RULES.items():
        for rel_path, rule in group_rules.items():
            assert "warn_tokens" in rule, (
                f"{group} lifecycle rule missing warn_tokens: {rel_path}"
            )
            assert isinstance(rule["warn_tokens"], list)


def test_kde_full_representation_force_switching_is_wired():
    text = _read("com.aiusagemonitor/contents/ui/FullRepresentation.qml")
    assert "forceSwitchingState: fullRoot.selectedIdentityMismatch" in text


def test_renderer_purity_forbidden_core_tokens_absent():
    for rel_path in RENDERER_FILES:
        text = _read(rel_path)
        for token in RENDERER_FORBIDDEN_TOKENS:
            assert token not in text, (
                f"{rel_path} contains forbidden core token: {token}"
            )


def test_file_line_budgets():
    for rel_path, budget in FILE_LINE_BUDGETS.items():
        line_count = len(_read(rel_path).splitlines())
        assert line_count <= budget, (
            f"{rel_path} exceeded line budget {budget}: {line_count}"
        )


def test_size_warning_thresholds_are_sane_and_files_exist():
    for rel_path, spec in FILE_SIZE_WARNING_THRESHOLDS.items():
        path = REPO_ROOT / rel_path
        assert path.exists(), f"Missing tracked file for warning policy: {rel_path}"
        warn_lines = int(spec["warn_lines"])
        alarm_lines = int(spec["alarm_lines"])
        assert warn_lines > 0
        assert alarm_lines > warn_lines


def test_size_warning_baselines_are_valid():
    for rel_path, baseline in FILE_SIZE_WARNING_BASELINES.items():
        path = REPO_ROOT / rel_path
        assert path.exists(), f"Missing baseline file: {rel_path}"
        assert int(baseline) > 0
        assert rel_path in FILE_SIZE_WARNING_THRESHOLDS
        assert rel_path in FILE_SIZE_BASELINE_REDUCTION_PLAN


def test_size_baseline_reduction_plan_is_sane():
    for rel_path, plan in FILE_SIZE_BASELINE_REDUCTION_PLAN.items():
        assert rel_path in FILE_SIZE_WARNING_THRESHOLDS
        assert (REPO_ROOT / rel_path).exists(), (
            f"Missing reduction plan target file: {rel_path}"
        )
        target_lines = int(plan["target_lines"])
        temporary_baseline = int(plan["temporary_baseline"])
        next_baseline = int(plan["next_baseline"])
        warn_lines = int(FILE_SIZE_WARNING_THRESHOLDS[rel_path]["warn_lines"])
        assert target_lines > 0
        assert target_lines <= warn_lines
        assert temporary_baseline > target_lines
        assert target_lines <= next_baseline <= temporary_baseline


def test_python_function_complexity_warning_thresholds_are_sane():
    warn_lines = int(PYTHON_FUNCTION_COMPLEXITY_WARN["warn_lines"])
    alarm_lines = int(PYTHON_FUNCTION_COMPLEXITY_WARN["alarm_lines"])
    warn_branch_points = int(PYTHON_FUNCTION_COMPLEXITY_WARN["warn_branch_points"])
    alarm_branch_points = int(PYTHON_FUNCTION_COMPLEXITY_WARN["alarm_branch_points"])

    assert warn_lines > 0
    assert alarm_lines > warn_lines
    assert warn_branch_points > 0
    assert alarm_branch_points > warn_branch_points


def test_python_complexity_target_files_exist():
    for rel_path in PYTHON_COMPLEXITY_TARGET_FILES:
        assert (REPO_ROOT / rel_path).exists(), (
            f"Missing complexity target file: {rel_path}"
        )


def test_python_function_complexity_baselines_are_valid():
    for key, values in PYTHON_FUNCTION_COMPLEXITY_BASELINES.items():
        rel_path, func_name = key.split("::", maxsplit=1)
        assert func_name
        assert rel_path in PYTHON_COMPLEXITY_TARGET_FILES
        assert (REPO_ROOT / rel_path).exists(), (
            f"Missing baseline target file: {rel_path}"
        )
        assert int(values["lines"]) > 0
        assert int(values["branch_points"]) >= 0


def test_no_new_baseline_locks_allowed():
    assert MAX_ALLOWED_FILE_BASELINE_LOCKS == 0
    assert MAX_ALLOWED_FUNCTION_BASELINE_LOCKS == 0
    assert len(FILE_SIZE_BASELINE_REDUCTION_PLAN) <= MAX_ALLOWED_FILE_BASELINE_LOCKS
    assert (
        len(PYTHON_FUNCTION_COMPLEXITY_BASELINES) <= MAX_ALLOWED_FUNCTION_BASELINE_LOCKS
    )


def test_mypy_ignore_errors_is_forbidden():
    mypy_text = _read("mypy.ini")
    for pattern in FORBIDDEN_MYPY_PATTERNS:
        assert pattern not in mypy_text


def test_settings_presentation_canonical_fields_are_stable():
    expected = {
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
    }
    assert set(SETTINGS_PRESENTATION_CANONICAL_FIELDS) == expected


def test_gnome_js_lint_targets_cover_all_extension_js_files():
    gnome_dir = REPO_ROOT / "gnome-extension/aiusagemonitor@aimonitor"
    all_js = sorted(
        path.relative_to(REPO_ROOT).as_posix()
        for path in gnome_dir.rglob("*.js")
        if "node_modules" not in path.parts
    )
    excluded = sorted(set(GNOME_EXTENSION_JS_EXCLUDE))
    expected = sorted(path for path in all_js if path not in excluded)

    assert sorted(GJS_LINT_TARGETS) == expected


def test_js_syntax_targets_cover_all_gnome_extension_js_files():
    gnome_dir = REPO_ROOT / "gnome-extension/aiusagemonitor@aimonitor"
    all_js = sorted(
        path.relative_to(REPO_ROOT).as_posix()
        for path in gnome_dir.rglob("*.js")
        if "node_modules" not in path.parts
    )
    excluded = sorted(set(GNOME_EXTENSION_JS_EXCLUDE))
    expected = sorted(path for path in all_js if path not in excluded)

    syntax_gnome_targets = sorted(
        target
        for target in JS_SYNTAX_TARGETS
        if target.startswith("gnome-extension/aiusagemonitor@aimonitor/")
    )
    assert syntax_gnome_targets == expected
