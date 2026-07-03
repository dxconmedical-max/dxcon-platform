#!/usr/bin/env python3
"""Verify secret safety, env tracking policy, and source hygiene."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT))

from env_safety_lib import git_tracked, run_env_safety_verification, scan_example_secrets

ALLOWED_ENV_TRACKED = {
    "backend/.env.example",
    "backend/.env.staging.example",
    "backend/.env.production.example",
}

FORBIDDEN_TRACKED_PATTERNS = (
    r"\.pyc$",
    r"__pycache__/",
    r"\.DS_Store$",
    r"__MACOSX/",
    r"\.save$",
    r"^backend/generated_reports/",
    r"^backend/instance/",
    r"^uploads/tmp/",
    r"^backend/\.env$",
)

REQUIRED_SOURCE_FILES = (
    "backend/app/__init__.py",
    "backend/app/models/__init__.py",
)


def git_tracked_paths() -> list[str]:
    proc = subprocess.run(
        ["git", "ls-files"],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
    )
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def check_gitignore_env() -> dict:
    gitignore = REPO / ".gitignore"
    text = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    patterns = [".env", "backend/.env"]
    present = [pattern for pattern in patterns if pattern in text]
    return {
        "ok": ".env" in text,
        "patterns_found": present,
        "path": str(gitignore.relative_to(REPO)),
    }


def check_env_tracking_policy() -> dict:
    tracked_env = [
        path
        for path in git_tracked_paths()
        if path.startswith("backend/") and ".env" in path
    ]
    unexpected = [path for path in tracked_env if path not in ALLOWED_ENV_TRACKED]
    missing = [path for path in ALLOWED_ENV_TRACKED if path not in tracked_env]
    return {
        "ok": not git_tracked("backend/.env") and not unexpected and not missing,
        "backend_env_tracked": git_tracked("backend/.env"),
        "tracked_env_files": tracked_env,
        "unexpected_tracked_env": unexpected,
        "missing_example_env": missing,
        "allowed_tracked_env": sorted(ALLOWED_ENV_TRACKED),
    }


def check_repository_hygiene() -> dict:
    import re

    findings = []
    for path in git_tracked_paths():
        for pattern in FORBIDDEN_TRACKED_PATTERNS:
            if re.search(pattern, path):
                findings.append(path)
                break
    return {"ok": not findings, "forbidden_tracked": findings}


def check_required_sources() -> dict:
    missing = [path for path in REQUIRED_SOURCE_FILES if not (REPO / path).exists()]
    return {
        "ok": not missing,
        "required": list(REQUIRED_SOURCE_FILES),
        "missing": missing,
    }


def run_secret_safety_verification() -> dict:
    env_safety = run_env_safety_verification()
    checks = {
        "required_sources": check_required_sources(),
        "gitignore_env": check_gitignore_env(),
        "env_tracking_policy": check_env_tracking_policy(),
        "repository_hygiene": check_repository_hygiene(),
        "example_secret_scan": env_safety.get("checks", {}).get("example_secret_scan", {"ok": False}),
    }
    passed = sum(1 for item in checks.values() if item.get("ok"))
    return {
        "ok": passed == len(checks) and env_safety.get("ok"),
        "passed": passed,
        "total": len(checks),
        "checks": checks,
        "env_safety": env_safety,
    }


def main() -> int:
    result = run_secret_safety_verification()
    print("\n=== DXCON SECRET SAFETY VERIFY ===\n")
    for name, payload in result.get("checks", {}).items():
        print(f"{'PASS' if payload.get('ok') else 'FAIL'}: {name}")
        if not payload.get("ok"):
            for key, value in payload.items():
                if key != "ok" and value:
                    print(f"  {key}: {value}")
    print(f"\nSUMMARY: {result.get('passed')}/{result.get('total')} checks passed")
    if result.get("ok"):
        print("SECRET SAFETY VERIFY PASSED\n")
        return 0
    print("SECRET SAFETY VERIFY FAILED\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
