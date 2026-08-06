#!/usr/bin/env python3
"""Verify ORM schema against live PostgreSQL (or against migration SQL offline).

Modes:
  --live     Compare db.Model.metadata to information_schema / pg_indexes / pg_constraint
  --offline  Ensure 021_schema_reconciliation.sql covers every ORM column (default)

Prints PASS/FAIL per model table.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECON = ROOT / "migrations" / "021_schema_reconciliation.sql"


def bootstrap():
    if "DATABASE_URL" not in os.environ:
        tf = tempfile.NamedTemporaryFile(prefix="dxcon_verify_schema_", suffix=".db", delete=False)
        tf.close()
        os.environ["DATABASE_URL"] = f"sqlite:///{tf.name}"
    sys.path.insert(0, str(ROOT))
    from app import create_app
    from app.extensions.db import db

    return create_app(), db


def parse_reconciliation_columns(sql: str) -> dict[str, set[str]]:
    cols: dict[str, set[str]] = {}
    current = None
    header = re.compile(r"^-- ===== ([a-zA-Z0-9_]+) =====")
    add = re.compile(
        r"ALTER TABLE\s+([a-zA-Z0-9_]+)\s+ADD COLUMN IF NOT EXISTS\s+([a-zA-Z0-9_]+)",
        re.I,
    )
    create = re.compile(
        r"CREATE TABLE IF NOT EXISTS\s+([a-zA-Z0-9_]+)\s*\((.*?)\)\s*;",
        re.I | re.S,
    )
    for line in sql.splitlines():
        m = header.match(line.strip())
        if m:
            current = m.group(1)
            cols.setdefault(current, set())
    for m in add.finditer(sql):
        cols.setdefault(m.group(1), set()).add(m.group(2))
    for m in create.finditer(sql):
        table = m.group(1)
        cols.setdefault(table, set())
        for raw in m.group(2).splitlines():
            raw = raw.strip().rstrip(",")
            if not raw or raw.upper().startswith("PRIMARY"):
                continue
            name = raw.split()[0]
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
                cols[table].add(name)
    return cols


def verify_offline(db) -> dict:
    if not RECON.exists():
        return {"ok": False, "error": f"missing {RECON}", "tables": []}
    covered = parse_reconciliation_columns(RECON.read_text(encoding="utf-8"))
    results = []
    fails = 0
    for table_name in sorted(db.Model.metadata.tables.keys()):
        table = db.Model.metadata.tables[table_name]
        have = covered.get(table_name, set())
        missing = [c.name for c in table.columns if c.name not in have]
        if table_name not in covered:
            results.append({"model_table": table_name, "status": "FAIL", "detail": "missing table DDL"})
            fails += 1
        elif missing:
            results.append(
                {
                    "model_table": table_name,
                    "status": "FAIL",
                    "detail": f"missing columns in migration: {', '.join(missing)}",
                }
            )
            fails += 1
        else:
            results.append(
                {
                    "model_table": table_name,
                    "status": "PASS",
                    "detail": f"{len(list(table.columns))} columns covered",
                }
            )
    return {"ok": fails == 0, "fail_count": fails, "pass_count": len(results) - fails, "tables": results}


def verify_live(db) -> dict:
    results = []
    fails = 0
    for table_name in sorted(db.Model.metadata.tables.keys()):
        table = db.Model.metadata.tables[table_name]
        exists = db.session.execute(
            db.text(
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_schema='public' AND table_name=:t"
            ),
            {"t": table_name},
        ).scalar()
        if not exists:
            results.append({"model_table": table_name, "status": "FAIL", "detail": "table absent"})
            fails += 1
            continue
        col_rows = db.session.execute(
            db.text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema='public' AND table_name=:t"
            ),
            {"t": table_name},
        ).fetchall()
        present = {r[0] for r in col_rows}
        missing_cols = [c.name for c in table.columns if c.name not in present]

        idx_rows = db.session.execute(
            db.text(
                "SELECT indexname FROM pg_indexes "
                "WHERE schemaname='public' AND tablename=:t"
            ),
            {"t": table_name},
        ).fetchall()
        indexes = [r[0] for r in idx_rows]

        con_rows = db.session.execute(
            db.text(
                "SELECT con.conname, con.contype FROM pg_constraint con "
                "JOIN pg_class rel ON rel.oid = con.conrelid "
                "JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace "
                "WHERE nsp.nspname='public' AND rel.relname=:t"
            ),
            {"t": table_name},
        ).fetchall()
        constraints = [{"name": r[0], "type": r[1]} for r in con_rows]

        if missing_cols:
            results.append(
                {
                    "model_table": table_name,
                    "status": "FAIL",
                    "detail": f"missing columns: {', '.join(missing_cols)}",
                    "indexes": indexes,
                    "constraints": constraints,
                }
            )
            fails += 1
        else:
            results.append(
                {
                    "model_table": table_name,
                    "status": "PASS",
                    "detail": f"columns={len(present)} indexes={len(indexes)} constraints={len(constraints)}",
                    "indexes": indexes,
                    "constraints": constraints,
                }
            )
    return {"ok": fails == 0, "fail_count": fails, "pass_count": len(results) - fails, "tables": results}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Query live PostgreSQL")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fail-only", action="store_true")
    args = parser.parse_args()

    app, db = bootstrap()
    with app.app_context():
        if args.live:
            if db.engine.dialect.name != "postgresql":
                print("FAIL: --live requires PostgreSQL")
                return 1
            report = verify_live(db)
        else:
            report = verify_offline(db)

    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        status = "PASS" if report.get("ok") else "FAIL"
        print(f"[{status}] schema reconciliation verification")
        print(f"  pass={report.get('pass_count')} fail={report.get('fail_count')}")
        for row in report.get("tables") or []:
            if args.fail_only and row["status"] == "PASS":
                continue
            print(f"  {row['status']}: {row['model_table']} — {row['detail']}")

    out = ROOT / "generated_release" / "SCHEMA_VERIFICATION_REPORT.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "mode": "live" if args.live else "offline",
        **report,
    }
    out.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
