#!/usr/bin/env python3
"""Verify rollback package metadata."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATED_DIR = ROOT / "generated_release"
sys.path.insert(0, str(ROOT))

from scripts.go_live_rc2_lib import build_rollback_checklist, git_sha


def main():
    print("\n=== DXCON ROLLBACK PACKAGE VERIFY ===\n")
    errors = 0
    package_path = GENERATED_DIR / "ROLLBACK_PACKAGE.json"
    if not package_path.exists():
        print("FAIL: ROLLBACK_PACKAGE.json missing")
        sys.exit(1)

    package = json.loads(package_path.read_text(encoding="utf-8"))
    required = (
        "current_git_sha",
        "previous_release_sha",
        "rollback_command_recommendation",
        "database_migration_warning",
        "artifact_checklist",
    )
    for key in required:
        if package.get(key):
            print("OK:", key)
        else:
            print("FAIL:", key)
            errors += 1

    checklist = build_rollback_checklist()
    if package.get("current_git_sha") == git_sha():
        print("OK: current git SHA matches")
    else:
        print("WARN: git SHA drift", package.get("current_git_sha"), git_sha())

    if checklist.get("previous_release_sha"):
        print("OK: previous release SHA placeholder")
    else:
        errors += 1

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
