#!/usr/bin/env python3

from __future__ import annotations

import argparse
import ast
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from project_health_contracts import (
    CORE_FORBIDDEN_TOKENS,
    FILE_LINE_BUDGETS,
    FILE_SIZE_BASELINE_REDUCTION_PLAN,
    FILE_SIZE_WARNING_BASELINES,
    FILE_SIZE_WARNING_THRESHOLDS,
    FORBIDDEN_MYPY_PATTERNS,
    GJS_LINT_TARGETS,
    JS_SYNTAX_TARGETS,
    LIFECYCLE_CONTRACT_RULES,
    MAX_ALLOWED_FILE_BASELINE_LOCKS,
    MAX_ALLOWED_FUNCTION_BASELINE_LOCKS,
    PYTHON_COMPLEXITY_TARGET_FILES,
    PYTHON_FUNCTION_COMPLEXITY_BASELINES,
    PYTHON_FUNCTION_COMPLEXITY_WARN,
    PYTHON_FUNCTION_LINE_BUDGETS,
    RENDERER_FILES,
    RENDERER_FORBIDDEN_TOKENS,
    SHELL_TARGETS,
    TYPE_SIGNATURE_TARGETS,
)


ROOT = Path(__file__).resolve().parents[1]

PYTHON_COMPILE_TARGETS = [
    "core",
    "tests",
    "com.aiusagemonitor/contents/scripts",
    "gnome-extension/aiusagemonitor@aimonitor/scripts",
]
PYTHON_ENTRYPOINTS = [
    "bin/ai-usage-monitor-state",
]
PYTHON_LINT_TARGETS = PYTHON_COMPILE_TARGETS + PYTHON_ENTRYPOINTS


@dataclass
class CheckResult:
    name: str
    status: str
    details: str = ""
    elapsed_ms: float | None = None


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _run(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return proc.returncode, (proc.stdout or "").strip()


def _resolve_tool(binary: str) -> str | None:
    venv = ROOT / ".venv" / "bin" / binary
    if venv.exists():
        return str(venv)
    local = ROOT / "node_modules" / ".bin" / binary
    if local.exists():
        return str(local)
    return shutil.which(binary)


def _resolve_qmllint() -> str | None:
    for binary in ("qmllint", "qmllint6"):
        resolved = shutil.which(binary)
        if resolved:
            return resolved

    qtpaths = shutil.which("qtpaths6")
    if qtpaths:
        rc, out = _run([qtpaths, "--query", "QT_HOST_BINS"])
        if rc == 0:
            host_bins = out.strip()
            if host_bins:
                for binary in ("qmllint", "qmllint6"):
                    candidate = Path(host_bins) / binary
                    if candidate.exists() and candidate.is_file():
                        return str(candidate)

    for candidate in (
        "/usr/lib/qt6/bin/qmllint",
        "/usr/lib/qt6/bin/qmllint6",
        "/usr/lib/qt/bin/qmllint",
        "/usr/lib/qt/bin/qmllint6",
    ):
        path = Path(candidate)
        if path.exists() and path.is_file():
            return str(path)
    return None


def _python_executable() -> str:
    return _resolve_tool("python3") or _resolve_tool("python") or sys.executable


def _ok(name: str, details: str = "") -> CheckResult:
    return CheckResult(name=name, status="PASS", details=details)


def _warn(name: str, details: str) -> CheckResult:
    return CheckResult(name=name, status="WARN", details=details)


def _fail(name: str, details: str) -> CheckResult:
    return CheckResult(name=name, status="FAIL", details=details)


def check_python_syntax() -> CheckResult:
    python = _python_executable()
    compile_cmd = [python, "-m", "compileall", "-q"] + PYTHON_COMPILE_TARGETS
    rc, out = _run(compile_cmd)
    if rc != 0:
        return _fail("python-syntax", out or "compileall failed")

    py_compile_cmd = [python, "-m", "py_compile"] + PYTHON_ENTRYPOINTS
    rc, out = _run(py_compile_cmd)
    if rc != 0:
        return _fail("python-entrypoints", out or "py_compile failed")
    return _ok("python-syntax")


def check_js_syntax() -> CheckResult:
    node = shutil.which("node")
    if not node:
        return _fail("js-syntax", "node is not installed")

    for rel_path in JS_SYNTAX_TARGETS:
        rc, out = _check_node_syntax(node, rel_path)
        if rc != 0:
            return _fail("js-syntax", f"{rel_path}\n{out}".strip())
    return _ok("js-syntax")


def _check_node_syntax(node: str, rel_path: str) -> tuple[int, str]:
    path = ROOT / rel_path
    text = path.read_text(encoding="utf-8")
    if ".pragma" not in text:
        return _run([node, "--check", rel_path])

    sanitized_lines = [
        line for line in text.splitlines() if not line.lstrip().startswith(".pragma ")
    ]
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".js", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write("\n".join(sanitized_lines))
        tmp.flush()
        tmp_path = Path(tmp.name)
    try:
        return _run([node, "--check", str(tmp_path)])
    finally:
        tmp_path.unlink(missing_ok=True)


def check_qml_syntax(require_tool: bool) -> CheckResult:
    runner = ROOT / "tools" / "run_qmllint.sh"
    if not runner.exists():
        return _fail("qml-syntax", "tools/run_qmllint.sh is missing")

    qmllint = _resolve_qmllint()
    if not qmllint and not require_tool:
        return _warn("qml-syntax", "qmllint not installed, skipping")
    if not qmllint:
        return _fail("qml-syntax", "qmllint is required but not installed")

    rc, out = _run([str(runner)])
    if rc != 0:
        return _fail("qml-syntax", out or "qmllint failed")
    return _ok("qml-syntax")


def check_shell_scripts(require_tool: bool) -> CheckResult:
    shellcheck = shutil.which("shellcheck")
    if not shellcheck:
        if require_tool:
            return _fail("shellcheck", "shellcheck is required but not installed")
        return _warn("shellcheck", "shellcheck not installed, skipping")

    rc, out = _run([shellcheck] + SHELL_TARGETS)
    if rc != 0:
        return _fail("shellcheck", out or "shellcheck failed")
    return _ok("shellcheck")


def check_ruff_lint(require_tool: bool) -> CheckResult:
    ruff = _resolve_tool("ruff")
    if not ruff:
        if require_tool:
            return _fail("ruff-lint", "ruff is required but not installed")
        return _warn("ruff-lint", "ruff not installed, skipping")

    cmd = [ruff, "check", "--select", "F,E9"] + PYTHON_LINT_TARGETS
    rc, out = _run(cmd)
    if rc != 0:
        return _fail("ruff-lint", out or "ruff lint failed")
    return _ok("ruff-lint", "rules: F,E9")


def check_ruff_format(require_tool: bool, enforce: bool) -> CheckResult:
    ruff = _resolve_tool("ruff")
    if not ruff:
        if require_tool:
            return _fail("ruff-format", "ruff is required but not installed")
        return _warn("ruff-format", "ruff not installed, skipping")

    cmd = [ruff, "format", "--check"] + PYTHON_LINT_TARGETS
    rc, out = _run(cmd)
    if rc == 0:
        return _ok("ruff-format")
    if enforce:
        return _fail("ruff-format", out or "ruff format check failed")
    return _warn("ruff-format", out or "format drift detected")


def check_gjs_lint(require_tool: bool) -> CheckResult:
    eslint = _resolve_tool("eslint")
    if not eslint:
        if require_tool:
            return _fail("gjs-lint", "eslint is required but not installed (`npm ci`)")
        return _warn("gjs-lint", "eslint not installed, skipping")

    cmd = [eslint, "--max-warnings=0"] + GJS_LINT_TARGETS
    rc, out = _run(cmd)
    if rc != 0:
        return _fail("gjs-lint", out or "eslint failed")
    return _ok("gjs-lint", f"checked {len(GJS_LINT_TARGETS)} files")


def check_mypy(require_tool: bool) -> CheckResult:
    python = _python_executable()
    mypy = _resolve_tool("mypy")
    if not mypy and require_tool:
        return _fail("mypy", "mypy is required but not installed")
    if not mypy:
        return _warn("mypy", "mypy not installed, skipping")

    cmd = [python, "-m", "mypy", "--config-file", "mypy.ini"]
    rc, out = _run(cmd)
    if rc != 0:
        return _fail("mypy", out or "mypy failed")
    return _ok("mypy")


def check_renderer_purity() -> CheckResult:
    violations: list[str] = []

    for rel_path in RENDERER_FILES:
        text = (ROOT / rel_path).read_text(encoding="utf-8")
        for token in RENDERER_FORBIDDEN_TOKENS:
            if token in text:
                violations.append(f"{rel_path}: forbidden token `{token}`")

    for py_file in sorted((ROOT / "core/ai_usage_monitor").rglob("*.py")):
        text = py_file.read_text(encoding="utf-8")
        for token in CORE_FORBIDDEN_TOKENS:
            if token in text:
                violations.append(f"{_rel(py_file)}: forbidden token `{token}`")

    if violations:
        return _fail("renderer-purity", "\n".join(violations))
    return _ok("renderer-purity")


def check_debt_guardrails() -> CheckResult:
    violations: list[str] = []

    file_baseline_count = len(FILE_SIZE_BASELINE_REDUCTION_PLAN)
    if file_baseline_count > MAX_ALLOWED_FILE_BASELINE_LOCKS:
        violations.append(
            "file baseline locks exceeded policy: "
            f"{file_baseline_count} > {MAX_ALLOWED_FILE_BASELINE_LOCKS}"
        )

    function_baseline_count = len(PYTHON_FUNCTION_COMPLEXITY_BASELINES)
    if function_baseline_count > MAX_ALLOWED_FUNCTION_BASELINE_LOCKS:
        violations.append(
            "function baseline locks exceeded policy: "
            f"{function_baseline_count} > {MAX_ALLOWED_FUNCTION_BASELINE_LOCKS}"
        )

    mypy_path = ROOT / "mypy.ini"
    if mypy_path.exists():
        for lineno, line in enumerate(
            mypy_path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            normalized = line.strip()
            for pattern in FORBIDDEN_MYPY_PATTERNS:
                if normalized == pattern:
                    violations.append(
                        f"mypy.ini:{lineno} forbidden typing debt override `{pattern}`"
                    )

    if violations:
        return _fail("debt-guardrails", "\n".join(violations))
    return _ok("debt-guardrails")


def check_file_budgets() -> CheckResult:
    violations: list[str] = []
    for rel_path, max_lines in FILE_LINE_BUDGETS.items():
        path = ROOT / rel_path
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        if line_count > max_lines:
            violations.append(f"{rel_path}: {line_count} lines (budget {max_lines})")
    if violations:
        return _fail("file-budgets", "\n".join(violations))
    return _ok("file-budgets")


def check_function_budgets() -> CheckResult:
    violations: list[str] = []
    for rel_path, max_lines in PYTHON_FUNCTION_LINE_BUDGETS.items():
        path = ROOT / rel_path
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel_path)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not hasattr(node, "end_lineno") or node.end_lineno is None:
                continue
            line_count = int(node.end_lineno - node.lineno + 1)
            if line_count > max_lines:
                violations.append(
                    f"{rel_path}:{node.lineno} {node.name}() -> {line_count} lines (budget {max_lines})"
                )
    if violations:
        return _fail("function-budgets", "\n".join(violations))
    return _ok("function-budgets")


def _ast_branch_points(node: ast.AST) -> int:
    branch_nodes = (
        ast.If,
        ast.For,
        ast.AsyncFor,
        ast.While,
        ast.Try,
        ast.BoolOp,
        ast.IfExp,
        ast.Match,
    )
    count = 0
    for child in ast.walk(node):
        if isinstance(child, branch_nodes):
            count += 1
    return count


def check_size_complexity_warnings() -> CheckResult:
    file_legacy_locked: list[str] = []
    file_tighten_due: list[str] = []
    file_growth: list[str] = []
    file_fresh: list[str] = []
    function_legacy_locked: list[str] = []
    function_tighten_due: list[str] = []
    function_growth: list[str] = []
    function_fresh: list[str] = []
    healthy_file_count = 0
    checked_file_count = 0
    stale_function_baselines: list[str] = []

    for rel_path, spec in FILE_SIZE_WARNING_THRESHOLDS.items():
        path = ROOT / rel_path
        if not path.exists():
            file_fresh.append(f"WARN  missing tracked file: {rel_path}")
            continue
        checked_file_count += 1
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        warn_lines = int(spec["warn_lines"])
        alarm_lines = int(spec["alarm_lines"])
        category = str(spec.get("category", "file"))
        baseline = FILE_SIZE_WARNING_BASELINES.get(rel_path)
        reduction = FILE_SIZE_BASELINE_REDUCTION_PLAN.get(rel_path, {})
        target_lines = reduction.get("target_lines")
        next_baseline = reduction.get("next_baseline")
        reduction_plan = reduction.get("reduction_plan")
        baseline_value = int(baseline) if baseline is not None else None
        next_baseline_value = int(next_baseline) if next_baseline is not None else None

        if line_count < warn_lines:
            healthy_file_count += 1
            continue

        severity = "ALARM" if line_count >= alarm_lines else "WARN "
        plan_suffix = ""
        if target_lines is not None:
            plan_suffix = f", target {target_lines}"
        if next_baseline is not None:
            plan_suffix += f", next-baseline {next_baseline}"
        gap_suffix = (
            f", debt-gap +{line_count - int(target_lines)}"
            if target_lines is not None and line_count > int(target_lines)
            else ""
        )
        reduction_suffix = (
            f", plan {reduction_plan}" if isinstance(reduction_plan, str) else ""
        )

        if baseline_value is not None and line_count <= baseline_value:
            if next_baseline_value is not None and line_count >= next_baseline_value:
                file_tighten_due.append(
                    f"{severity} BASELINE_TIGHTEN_DUE {rel_path}: {line_count} lines "
                    f"(warn {warn_lines}, alarm {alarm_lines}, baseline {baseline_value}{plan_suffix}{gap_suffix}{reduction_suffix})"
                )
                continue
            file_legacy_locked.append(
                f"{severity} LEGACY_DEBT_LOCKED {rel_path}: {line_count} lines "
                f"(warn {warn_lines}, alarm {alarm_lines}, baseline {baseline_value}{plan_suffix}{gap_suffix})"
            )
            continue
        if baseline_value is not None and line_count > baseline_value:
            file_growth.append(
                f"{severity} BASELINE_BREACH {rel_path}: {line_count} lines > baseline {baseline_value} "
                f"({category}{plan_suffix})"
            )
            continue
        file_fresh.append(
            f"{severity} NEW_DEBT {rel_path}: {line_count} lines >= {warn_lines} ({category}{plan_suffix})"
        )

    warn_lines = int(PYTHON_FUNCTION_COMPLEXITY_WARN["warn_lines"])
    alarm_lines = int(PYTHON_FUNCTION_COMPLEXITY_WARN["alarm_lines"])
    warn_branches = int(PYTHON_FUNCTION_COMPLEXITY_WARN["warn_branch_points"])
    alarm_branches = int(PYTHON_FUNCTION_COMPLEXITY_WARN["alarm_branch_points"])
    seen_baseline_keys: set[str] = set()

    for rel_path in PYTHON_COMPLEXITY_TARGET_FILES:
        py_file = ROOT / rel_path
        if not py_file.exists():
            function_fresh.append(f"WARN  missing complexity target file: {rel_path}")
            continue
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=rel_path)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not hasattr(node, "end_lineno") or node.end_lineno is None:
                continue
            line_count = int(node.end_lineno - node.lineno + 1)
            branch_points = _ast_branch_points(node)
            baseline_key = f"{rel_path}::{node.name}"
            baseline = PYTHON_FUNCTION_COMPLEXITY_BASELINES.get(baseline_key)
            if baseline is not None:
                seen_baseline_keys.add(baseline_key)

            exceeds_warn = line_count >= warn_lines or branch_points >= warn_branches
            exceeds_alarm = line_count >= alarm_lines or branch_points >= alarm_branches
            if not exceeds_warn:
                continue

            if baseline is not None:
                baseline_lines = int(baseline["lines"])
                baseline_branches = int(baseline["branch_points"])
                severity = "ALARM" if exceeds_alarm else "WARN "
                if line_count <= baseline_lines and branch_points <= baseline_branches:
                    if (
                        line_count == baseline_lines
                        or branch_points == baseline_branches
                    ):
                        function_tighten_due.append(
                            f"{severity} BASELINE_TIGHTEN_DUE {rel_path}:{node.lineno} {node.name}() "
                            f"lines={line_count} branches={branch_points} "
                            f"(baseline lines={baseline_lines} branches={baseline_branches})"
                        )
                        continue
                    function_legacy_locked.append(
                        f"{severity} LEGACY_DEBT_LOCKED {rel_path}:{node.lineno} {node.name}() "
                        f"lines={line_count} branches={branch_points} "
                        f"(baseline lines={baseline_lines} branches={baseline_branches})"
                    )
                    continue
                function_growth.append(
                    f"{severity} BASELINE_BREACH {rel_path}:{node.lineno} {node.name}() "
                    f"lines={line_count} branches={branch_points} "
                    f"(baseline lines={baseline_lines} branches={baseline_branches})"
                )
                continue

            severity = "ALARM" if exceeds_alarm else "WARN "
            function_fresh.append(
                f"{severity} NEW_DEBT {rel_path}:{node.lineno} {node.name}() "
                f"lines={line_count} branches={branch_points}"
            )

    stale_keys = sorted(set(PYTHON_FUNCTION_COMPLEXITY_BASELINES) - seen_baseline_keys)
    for stale_key in stale_keys:
        stale_function_baselines.append(
            f"WARN  STALE_BASELINE {stale_key}: function no longer found"
        )

    details: list[str] = []
    total_debt = (
        len(file_legacy_locked)
        + len(file_tighten_due)
        + len(file_growth)
        + len(file_fresh)
        + len(function_legacy_locked)
        + len(function_tighten_due)
        + len(function_growth)
        + len(function_fresh)
    )
    if total_debt == 0 and not stale_function_baselines:
        return _ok("size-complexity-warnings")

    details.append(
        "DEBT_SUMMARY "
        f"files_checked={checked_file_count} healthy_files={healthy_file_count} "
        f"legacy_locked={len(file_legacy_locked) + len(function_legacy_locked)} "
        f"tighten_due={len(file_tighten_due) + len(function_tighten_due)} "
        f"baseline_breach={len(file_growth) + len(function_growth)} "
        f"new_debt={len(file_fresh) + len(function_fresh)} "
        f"stale_baselines={len(stale_function_baselines)}"
    )
    details.append(
        "NOTE legacy debt is reported as WARN; 0 warnings is the only 0-debt signal."
    )

    if file_legacy_locked:
        details.append("[FILES LEGACY_DEBT_LOCKED]")
        details.extend(file_legacy_locked)
    if file_tighten_due:
        details.append("[FILES BASELINE_TIGHTEN_DUE]")
        details.extend(file_tighten_due)
    if file_growth:
        details.append("[FILES BASELINE_BREACH]")
        details.extend(file_growth)
    if file_fresh:
        details.append("[FILES NEW_DEBT]")
        details.extend(file_fresh)

    if function_legacy_locked:
        details.append("[FUNCTIONS LEGACY_DEBT_LOCKED]")
        details.extend(function_legacy_locked)
    if function_tighten_due:
        details.append("[FUNCTIONS BASELINE_TIGHTEN_DUE]")
        details.extend(function_tighten_due)
    if function_growth:
        details.append("[FUNCTIONS BASELINE_BREACH]")
        details.extend(function_growth)
    if function_fresh:
        details.append("[FUNCTIONS NEW_DEBT]")
        details.extend(function_fresh)
    if stale_function_baselines:
        details.append("[FUNCTIONS STALE_BASELINES]")
        details.extend(stale_function_baselines)

    if total_debt > 0 or stale_function_baselines:
        return _warn("size-complexity-warnings", "\n".join(details))
    return _ok("size-complexity-warnings")


def check_typeish_signatures() -> CheckResult:
    violations: list[str] = []
    for rel_path, function_names in TYPE_SIGNATURE_TARGETS.items():
        path = ROOT / rel_path
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel_path)
        functions = {
            node.name: node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        for name in function_names:
            node = functions.get(name)
            if node is None:
                violations.append(f"{rel_path}: missing function `{name}`")
                continue
            if node.returns is None:
                violations.append(
                    f"{rel_path}:{node.lineno} `{name}` missing return annotation"
                )
            args = [
                *node.args.posonlyargs,
                *node.args.args,
                *node.args.kwonlyargs,
            ]
            for arg in args:
                if arg.arg in {"self", "cls"}:
                    continue
                if arg.annotation is None:
                    violations.append(
                        f"{rel_path}:{node.lineno} `{name}` arg `{arg.arg}` missing annotation"
                    )
    if violations:
        return _fail("typeish-signatures", "\n".join(violations))
    return _ok("typeish-signatures")


def check_gnome_lifecycle_contract() -> CheckResult:
    return _check_lifecycle_contract(
        name="gnome-lifecycle-contract",
        rules=LIFECYCLE_CONTRACT_RULES.get("gnome", {}),
    )


def check_kde_lifecycle_contract() -> CheckResult:
    return _check_lifecycle_contract(
        name="kde-lifecycle-contract",
        rules=LIFECYCLE_CONTRACT_RULES.get("kde", {}),
    )


def _check_lifecycle_contract(
    name: str, rules: dict[str, dict[str, list[str]]]
) -> CheckResult:
    missing: list[str] = []
    forbidden: list[str] = []
    warned: list[str] = []
    checked_files = 0
    for rel_path, rule in rules.items():
        path = ROOT / rel_path
        if not path.exists():
            missing.append(f"{rel_path}: file not found")
            continue
        checked_files += 1
        text = path.read_text(encoding="utf-8")
        required_tokens = rule.get("required_tokens", [])
        forbidden_tokens = rule.get("forbidden_tokens", [])
        warn_tokens = rule.get("warn_tokens", [])

        for token in required_tokens:
            if token not in text:
                missing.append(f"{rel_path}: missing token `{token}`")
        for token in forbidden_tokens:
            if token in text:
                forbidden.append(f"{rel_path}: forbidden token `{token}`")
        for token in warn_tokens:
            if token in text:
                warned.append(f"{rel_path}: risky pattern `{token}`")

    if missing or forbidden:
        details = [f"checked_files={checked_files}"]
        if missing:
            details.append("[MISSING_REQUIRED]")
            details.extend(missing)
        if forbidden:
            details.append("[FORBIDDEN_PRESENT]")
            details.extend(forbidden)
        if warned:
            details.append("[RISKY_PATTERNS]")
            details.extend(warned)
        return _fail(name, "\n".join(details))

    if warned:
        details = [f"checked_files={checked_files}", "[RISKY_PATTERNS]"]
        details.extend(warned)
        return _warn(name, "\n".join(details))

    return _ok(name, f"checked_files={checked_files}")


def check_pytest() -> CheckResult:
    rc, out = _run([_python_executable(), "-m", "pytest", "-q"])
    if rc != 0:
        return _fail("pytest", out or "pytest failed")
    return _ok("pytest", out.splitlines()[-1] if out else "")


def build_checks(mode: str) -> list[tuple[str, object]]:
    require_qmllint = mode == "ci"
    require_shellcheck = mode == "ci"
    require_ruff = True
    require_eslint = True
    require_mypy = mode in {"full", "ci"}
    enforce_format = mode == "ci"
    run_pytest_checks = mode in {"full", "ci"}
    run_mypy_check = mode in {"full", "ci"}

    checks: list[tuple[str, object]] = [
        ("python-syntax", check_python_syntax),
        ("js-syntax", check_js_syntax),
        ("qml-syntax", lambda: check_qml_syntax(require_tool=require_qmllint)),
        ("shellcheck", lambda: check_shell_scripts(require_tool=require_shellcheck)),
        ("ruff-lint", lambda: check_ruff_lint(require_tool=require_ruff)),
        (
            "ruff-format",
            lambda: check_ruff_format(
                require_tool=require_ruff, enforce=enforce_format
            ),
        ),
        ("gjs-lint", lambda: check_gjs_lint(require_tool=require_eslint)),
        ("typeish-signatures", check_typeish_signatures),
        ("renderer-purity", check_renderer_purity),
        ("debt-guardrails", check_debt_guardrails),
        ("size-complexity-warnings", check_size_complexity_warnings),
        ("file-budgets", check_file_budgets),
        ("function-budgets", check_function_budgets),
        ("gnome-lifecycle-contract", check_gnome_lifecycle_contract),
        ("kde-lifecycle-contract", check_kde_lifecycle_contract),
    ]
    if run_mypy_check:
        checks.append(("mypy", lambda: check_mypy(require_tool=require_mypy)))
    if run_pytest_checks:
        checks.append(("pytest", check_pytest))
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description="Project health quality gates")
    parser.add_argument(
        "--mode",
        choices=["quick", "full", "ci"],
        default="full",
        help="quick = syntax/lint/boundary checks, full = quick + mypy + pytest, ci = strict tools required",
    )
    parser.add_argument(
        "--fail-on-warn",
        action="store_true",
        help="exit non-zero if any WARN check is reported",
    )
    args = parser.parse_args()

    results: list[CheckResult] = []
    for _name, fn in build_checks(args.mode):
        started = time.perf_counter()
        result = fn()
        result.elapsed_ms = (time.perf_counter() - started) * 1000.0
        results.append(result)
        elapsed = (
            f"{result.elapsed_ms:.1f}ms" if result.elapsed_ms is not None else "n/a"
        )
        print(f"[{result.status}] {result.name} ({elapsed})")
        if result.details:
            print(result.details)

    failed = [result for result in results if result.status == "FAIL"]
    warned = [result for result in results if result.status == "WARN"]
    print(
        f"\nSummary: {len(results) - len(failed)} passed/warned, {len(failed)} failed, {len(warned)} warnings"
    )
    fail_on_warn = args.fail_on_warn or args.mode == "ci"
    if failed:
        return 1
    if fail_on_warn and warned:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
