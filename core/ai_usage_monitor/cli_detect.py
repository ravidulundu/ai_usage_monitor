from __future__ import annotations

import os
import shutil
from pathlib import Path


def _is_executable_file(path: Path) -> bool:
    try:
        return path.is_file() and os.access(path, os.X_OK)
    except OSError:
        return False


def _candidate_bin_dirs() -> list[Path]:
    home = Path.home()
    candidates = [
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

    return None
