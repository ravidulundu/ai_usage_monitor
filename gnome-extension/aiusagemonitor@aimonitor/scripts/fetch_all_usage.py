#!/usr/bin/env python3
"""GNOME wrapper for the shared AI Usage Monitor backend."""

from __future__ import annotations

import sys
from pathlib import Path


def extend_sys_path() -> None:
    script_path = Path(__file__).resolve()
    repo_root = script_path.parents[3]
    shared_root = Path.home() / ".local" / "share" / "ai-usage-monitor"

    # Keep declared priority order: repo -> shared.
    for candidate in reversed((repo_root, shared_root)):
        if (candidate / "core" / "ai_usage_monitor").exists():
            candidate_str = str(candidate)
            if candidate_str not in sys.path:
                sys.path.insert(0, candidate_str)


def main() -> int:
    extend_sys_path()
    from core.ai_usage_monitor.cli import main as cli_main

    argv = sys.argv[1:] if len(sys.argv) > 1 else ["state"]
    return cli_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
