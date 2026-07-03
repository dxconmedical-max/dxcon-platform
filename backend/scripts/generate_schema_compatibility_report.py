#!/usr/bin/env python3
"""Compare seed SQLAlchemy models against the live database schema."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

REPORT_PATH = ROOT / "generated_release" / "SCHEMA_COMPATIBILITY_REPORT.json"

from app import create_app
from app.infrastructure.schema_introspection import build_schema_compatibility_report


def main() -> int:
    if not os.getenv("DATABASE_URL"):
        print("FAIL: DATABASE_URL is required", file=sys.stderr)
        return 1

    app = create_app()
    with app.app_context():
        report = build_schema_compatibility_report()

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    print("\n=== SCHEMA COMPATIBILITY REPORT ===\n")
    print(f"Report: {REPORT_PATH}")
    print(f"Compatible: {report['summary']['compatible_models']}/{report['summary']['seed_models_checked']}")
    print(f"Models changed for production schema: {report['summary']['models_changed_for_production_schema']}\n")
    for item in report["changed_models"]:
        print(f"  - {item['model']}: {item['change']} {item['from']} -> {item['to']}")
    incompatible = [item for item in report["models"] if not item.get("compatible", False)]
    if incompatible:
        print("\nIncompatible models:")
        for item in incompatible:
            print(f"  - {item.get('model')}: pk={item.get('primary_key_match')} fk={item.get('foreign_key_issues')}")
        print("\nNote: legacy local databases may still expose patients.id while models target production patient_code PK.")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
