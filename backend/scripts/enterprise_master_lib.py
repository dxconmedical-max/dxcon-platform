"""Shared helpers for Enterprise Hardening Master Pack (packs 3-10)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
REPORT_DIR = ROOT / "generated_release"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_report(name: str, payload: dict) -> str:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORT_DIR / name
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return str(path)


def scan_python_files(base: Path):
    for path in base.rglob("*.py"):
        if any(part in {"venv", "__pycache__", ".git"} for part in path.parts):
            continue
        yield path


def run_compileall() -> dict:
    proc = subprocess.run(
        [sys.executable, "-m", "compileall", "-q", "app", "scripts", "tests"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    return {"ok": proc.returncode == 0, "exit_code": proc.returncode}


def run_unit_tests() -> dict:
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    total = None
    for line in proc.stdout.splitlines():
        if line.startswith("Ran "):
            try:
                total = int(line.split()[1])
            except (IndexError, ValueError):
                pass
    return {
        "ok": proc.returncode == 0,
        "exit_code": proc.returncode,
        "total": total,
        "tail": proc.stdout.splitlines()[-3:],
    }


def run_release_isolation(release_id: str) -> dict:
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "release_isolation.py"),
            "check",
            "--release",
            release_id,
        ],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "ok": proc.returncode == 0,
        "exit_code": proc.returncode,
        "stdout_tail": proc.stdout.splitlines()[-8:],
    }


def create_test_app():
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    sys.path.insert(0, str(ROOT))
    from app import create_app
    from app.extensions.db import db

    app = create_app()
    app.config["TESTING"] = True
    return app, db


def score_from_checks(checks: dict, weights: dict | None = None) -> int:
    weights = weights or {}
    total_weight = 0
    earned = 0
    for name, payload in checks.items():
        weight = weights.get(name, 1)
        total_weight += weight
        if isinstance(payload, dict) and payload.get("ok"):
            earned += weight
        elif payload is True:
            earned += weight
    if total_weight == 0:
        return 0
    return round(100 * earned / total_weight)


def print_verify_banner(title: str, sections: dict) -> None:
    print(f"\n=== {title} ===\n")
    for section_name, section in sections.items():
        ok = section.get("ok") if isinstance(section, dict) else bool(section)
        print(f"{'PASS' if ok else 'FAIL'}: {section_name}")
        checks = section.get("checks") if isinstance(section, dict) else None
        if isinstance(checks, dict):
            for name, payload in checks.items():
                if isinstance(payload, dict) and "ok" in payload:
                    print(f"  {'PASS' if payload.get('ok') else 'FAIL'}: {name}")
