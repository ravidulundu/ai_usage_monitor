from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path


def _is_executable_file(path: Path) -> bool:
    try:
        return path.is_file() and os.access(path, os.X_OK)
    except OSError:
        return False


def _candidate_bin_dirs() -> list[Path]:
    home = Path.home()
    candidates = [
        Path("/usr/local/bin"),
        Path("/usr/bin"),
        Path("/bin"),
        Path("/snap/bin"),
        home / ".local" / "bin",
        home / ".bun" / "bin",
        home / ".npm-global" / "bin",
        home / ".local" / "share" / "pnpm",
        home / ".volta" / "bin",
        home / ".yarn" / "bin",
    ]

    pnpm_home = os.environ.get("PNPM_HOME")
    if pnpm_home:
        candidates.append(Path(pnpm_home))

    npm_prefix = os.environ.get("NPM_CONFIG_PREFIX")
    if npm_prefix:
        candidates.append(Path(npm_prefix) / "bin")

    bun_install = os.environ.get("BUN_INSTALL")
    if bun_install:
        candidates.append(Path(bun_install) / "bin")

    volta_home = os.environ.get("VOLTA_HOME")
    if volta_home:
        candidates.append(Path(volta_home) / "bin")

    yarn_global_folder = os.environ.get("YARN_GLOBAL_FOLDER")
    if yarn_global_folder:
        candidates.append(Path(yarn_global_folder))
        candidates.append(Path(yarn_global_folder) / "bin")

    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate)
    return unique


_SAFE_BINARY_PATTERN = re.compile(r"^[A-Za-z0-9._+-]+$")


def _resolve_via_login_shell(binary_name: str) -> str | None:
    if not _SAFE_BINARY_PATTERN.fullmatch(binary_name):
        return None

    shells: list[str] = []
    env_shell = os.environ.get("SHELL")
    if env_shell:
        shells.append(env_shell)
    shells.extend(("/bin/zsh", "/bin/bash", "/bin/sh"))

    seen: set[str] = set()
    for shell in shells:
        if shell in seen:
            continue
        seen.add(shell)
        shell_path = Path(shell)
        if not _is_executable_file(shell_path):
            continue
        try:
            probe = subprocess.run(
                [shell, "-lc", f"command -v -- {binary_name} 2>/dev/null || true"],
                capture_output=True,
                text=True,
                timeout=1.0,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            continue

        resolved = str(probe.stdout or "").strip().splitlines()
        if not resolved:
            continue
        candidate = Path(resolved[0]).expanduser()
        if _is_executable_file(candidate):
            return str(candidate)
    return None


def resolve_cli_binary(binary_name: str, env_var: str | None = None) -> str | None:
    if env_var:
        override = os.environ.get(env_var)
        if override:
            override_path = Path(override).expanduser()
            if _is_executable_file(override_path):
                return str(override_path)

    discovered = shutil.which(binary_name)
    if discovered:
        return discovered

    for directory in _candidate_bin_dirs():
        candidate = directory / binary_name
        if _is_executable_file(candidate):
            return str(candidate)

    shell_resolved = _resolve_via_login_shell(binary_name)
    if shell_resolved:
        return shell_resolved

    return None
