#!/usr/bin/env python3
"""Rollback metadata helper (non-destructive)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "deployment" / "reports"


def load_latest_report():
    candidates = sorted(REPORTS.glob("*-deployment-report.json"))
    if not candidates:
        return None
    return json.loads(candidates[-1].read_text(encoding="utf-8"))


def build_rollback_plan():
    report = load_latest_report()
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "strategy": "metadata-only",
        "destructive": False,
        "previous_report": report,
        "steps": [
            "Validate backup artifacts",
            "Run restore dry-run",
            "Deploy previous container image tag",
            "Run post-deployment verification",
        ],
    }


def main():
    plan = build_rollback_plan()
    output = REPORTS / "rollback-plan.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "plan_path": str(output)}, indent=2))


if __name__ == "__main__":
    main()
