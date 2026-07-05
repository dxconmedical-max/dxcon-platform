#!/usr/bin/env python3
"""Verify MDM platform — imports, dashboard, reports."""

from __future__ import annotations

import csv
import io
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

GENERATED = ROOT / "generated_release"
ENV_FILE = ROOT / ".env"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_database_url() -> str:
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("DATABASE_URL=") and not line.startswith("#"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("DATABASE_URL", "sqlite:///:memory:")


def apply_mdm_migration(db) -> None:
    migration = ROOT / "migrations" / "003_mdm_foundation.sql"
    if not migration.exists():
        return
    lines = [ln for ln in migration.read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.strip().startswith("--")]
    for stmt in " ".join(lines).split(";"):
        stmt = stmt.strip()
        if stmt:
            db.session.execute(db.text(stmt))
    db.session.commit()


def csv_bytes(entity_type: str, code: str) -> bytes:
    from app.mdm.registry import sample_row, template_columns

    cols = template_columns(entity_type)
    sample = sample_row(entity_type)
    sample["code"] = code
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
    writer.writeheader()
    writer.writerow({c: sample.get(c, "") for c in cols})
    return buf.getvalue().encode("utf-8")


def main() -> int:
    database_url = load_database_url()
    os.environ["DATABASE_URL"] = database_url
    is_pg = database_url.startswith("postgresql") or database_url.startswith("postgres")

    from app import create_app
    from app.extensions.db import db
    from app.mdm.import_engine import approve_batch, commit_batch, import_from_bytes, rollback_batch
    from app.mdm.registry import ENTITY_TYPES
    from app.mdm.service import dashboard_stats, master_data_report
    from app.models.mdm import MdmMasterRecord

    start = time.time()
    checks: dict = {}
    app = create_app()

    with app.app_context():
        if is_pg:
            apply_mdm_migration(db)
        else:
            db.create_all()

        # Import each entity type
        import_results = []
        run_tag = uuid.uuid4().hex[:6].upper()
        for entity_type in ENTITY_TYPES:
            tag = entity_type.replace("_", "-").upper()[:8]
            code = f"MDM-{tag}-{run_tag}"
            content = csv_bytes(entity_type, code)
            batch = import_from_bytes(
                entity_type,
                content,
                file_name=f"{entity_type}.csv",
                actor="verify-mdm@dxcon.test",
                auto_approve=True,
                auto_commit=True,
            )
            db.session.commit()
            import_results.append({
                "entity_type": entity_type,
                "batch_code": batch.batch_code,
                "status": batch.status,
                "committed_rows": batch.committed_rows,
                "ok": batch.committed_rows >= 1,
            })

        checks["imports_all_entities"] = {
            "ok": all(r["ok"] for r in import_results),
            "passed": sum(1 for r in import_results if r["ok"]),
            "total": len(import_results),
        }

        # Duplicate detection
        dup_content = csv_bytes("test_catalog", f"MDM-DUP-{run_tag}")
        import_from_bytes(
            "test_catalog",
            dup_content,
            file_name="dup.csv",
            actor="verify@dxcon.test",
            auto_approve=True,
            auto_commit=True,
        )
        db.session.commit()
        dup_batch2 = import_from_bytes("test_catalog", dup_content, file_name="dup2.csv", actor="verify@dxcon.test")
        db.session.commit()
        checks["duplicate_detection"] = {
            "ok": dup_batch2.duplicate_rows >= 1,
            "duplicate_rows": dup_batch2.duplicate_rows,
            "valid_rows": dup_batch2.valid_rows,
        }

        # Approve / commit / rollback cycle on sample_type
        rb_content = csv_bytes("sample_type", f"RB-SAMPLE-{run_tag}")
        rb_batch = import_from_bytes("sample_type", rb_content, file_name="rb.csv", actor="verify@dxcon.test")
        approve_batch(rb_batch.id, actor="verify@dxcon.test")
        commit_batch(rb_batch.id, actor="verify@dxcon.test")
        db.session.commit()
        rollback_batch(rb_batch.id, actor="verify@dxcon.test")
        db.session.commit()
        rb_record = MdmMasterRecord.query.filter_by(entity_type="sample_type", code=f"RB-SAMPLE-{run_tag}").first()
        checks["rollback"] = {
            "ok": rb_record is not None and rb_record.status == "inactive",
            "status": rb_record.status if rb_record else None,
        }

        dashboard = dashboard_stats()
        master_report = master_data_report()
        checks["dashboard"] = {
            "ok": dashboard["totals"]["records"] >= len(ENTITY_TYPES),
            "records": dashboard["totals"]["records"],
            "populated": dashboard["totals"]["populated_entity_types"],
        }
        checks["no_duplicates"] = {
            "ok": len(dashboard["duplicate_records"]) == 0,
            "duplicates": dashboard["duplicate_records"],
        }

        elapsed = round(time.time() - start, 2)
        passed = sum(1 for c in checks.values() if c.get("ok"))

        import_report = {
            "report": "MASTER_DATA_IMPORT_REPORT",
            "generated_at": utc_now(),
            "database": "postgresql" if is_pg else "sqlite",
            "elapsed_seconds": elapsed,
            "entity_imports": import_results,
            "checks": checks,
            "summary": {"passed": passed, "total": len(checks), "ok": passed == len(checks)},
        }
        dashboard_report = {
            "report": "MASTER_DATA_DASHBOARD",
            "generated_at": utc_now(),
            **dashboard,
        }
        master_data_report_file = {
            "report": "MASTER_DATA_REPORT",
            "generated_at": utc_now(),
            **master_report,
        }

        GENERATED.mkdir(parents=True, exist_ok=True)
        (GENERATED / "MASTER_DATA_IMPORT_REPORT.json").write_text(json.dumps(import_report, indent=2, default=str), encoding="utf-8")
        (GENERATED / "MASTER_DATA_DASHBOARD.json").write_text(json.dumps(dashboard_report, indent=2, default=str), encoding="utf-8")
        (GENERATED / "MASTER_DATA_REPORT.json").write_text(json.dumps(master_data_report_file, indent=2, default=str), encoding="utf-8")

        print("\n=== MDM VERIFY ===\n")
        for name, item in checks.items():
            print(f"{'PASS' if item.get('ok') else 'FAIL'}: {name}")
        print(f"\nImports: {checks['imports_all_entities']['passed']}/{checks['imports_all_entities']['total']}")
        print(f"Summary: {passed}/{len(checks)} in {elapsed}s\n")
        return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
