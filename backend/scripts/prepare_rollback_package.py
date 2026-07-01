#!/usr/bin/env python3
"""Prepare rollback package metadata for production cutover."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.go_live_rc2_lib import build_rollback_package, write_json


def main():
    print("\n=== DXCON ROLLBACK PACKAGE PREP ===\n")
    package = build_rollback_package()
    print(json.dumps(
        {
            "current_git_sha": package["current_git_sha"],
            "previous_release_sha": package["previous_release_sha"],
            "rollback_command_recommendation": package["rollback_command_recommendation"],
        },
        indent=2,
    ))
    print("\nOK: wrote backend/generated_release/ROLLBACK_PACKAGE.json\n")


if __name__ == "__main__":
    main()
