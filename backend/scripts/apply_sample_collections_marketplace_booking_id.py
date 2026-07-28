#!/usr/bin/env python3
"""Apply sample_collections.marketplace_booking_id migration inside Flask app context.

Production-safe runner for:
  backend/migrations/020_sample_collections_marketplace_booking_id.sql

Usage (Render Shell / local with production DATABASE_URL):

  cd /opt/render/project/src/backend   # or repo backend/
  python scripts/apply_sample_collections_marketplace_booking_id.py

  # dry-run verify only:
  python scripts/apply_sample_collections_marketplace_booking_id.py --verify-only

Exits 0 on success, 1 on failure. Does not rewrite existing row data.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATION_NAME = "020_sample_collections_marketplace_booking_id.sql"
MIGRATION_PATH = ROOT / "migrations" / MIGRATION_NAME
REQUIRED_COLUMN = "marketplace_booking_id"
TABLE = "sample_collections"


def _split_sql(sql: str) -> list[str]:
    """Split SQL into executable statements, preserving DO $$ ... $$ blocks."""
    statements: list[str] = []
    buf: list[str] = []
    in_do = False
    for raw in sql.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        upper = stripped.upper()
        if not in_do and upper.startswith("DO $$"):
            in_do = True
            buf = [line]
            if "$$;" in stripped or stripped.endswith("$$ ;"):
                in_do = False
                statements.append("\n".join(buf).strip())
                buf = []
            continue
        if in_do:
            buf.append(line)
            if stripped.endswith("$$;") or stripped == "$$;":
                in_do = False
                statements.append("\n".join(buf).strip())
                buf = []
            continue
        buf.append(line)
        if stripped.endswith(";"):
            statements.append("\n".join(buf).strip().rstrip(";").strip())
            buf = []
    if buf:
        statements.append("\n".join(buf).strip().rstrip(";").strip())
    return [s for s in statements if s]


def verify_column(db) -> dict:
    """Query information_schema.columns for marketplace_booking_id."""
    rows = db.session.execute(
        db.text(
            """
            SELECT
              column_name,
              data_type,
              character_maximum_length,
              is_nullable,
              column_default
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = :table
              AND column_name = :column
            """
        ),
        {"table": TABLE, "column": REQUIRED_COLUMN},
    ).mappings().all()

    fk_rows = db.session.execute(
        db.text(
            """
            SELECT
              tc.constraint_name,
              kcu.column_name,
              ccu.table_name AS foreign_table_name,
              ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
             AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
             AND ccu.table_schema = tc.table_schema
            WHERE tc.table_schema = 'public'
              AND tc.table_name = :table
              AND tc.constraint_type = 'FOREIGN KEY'
              AND kcu.column_name = :column
            """
        ),
        {"table": TABLE, "column": REQUIRED_COLUMN},
    ).mappings().all()

    index_rows = db.session.execute(
        db.text(
            """
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'public'
              AND tablename = :table
              AND indexname = 'ix_sample_collections_marketplace_booking_id'
            """
        ),
        {"table": TABLE},
    ).mappings().all()

    column = dict(rows[0]) if rows else None
    ok = (
        column is not None
        and column.get("data_type") in {"character varying", "varchar"}
        and (
            column.get("character_maximum_length") is None
            or int(column.get("character_maximum_length") or 0) == 36
        )
        and str(column.get("is_nullable", "")).upper() == "YES"
    )
    return {
        "ok": ok,
        "table": TABLE,
        "column": REQUIRED_COLUMN,
        "column_info": column,
        "foreign_keys": [dict(r) for r in fk_rows],
        "indexes": [dict(r) for r in index_rows],
        "verification_sql": (
            "SELECT column_name, data_type, character_maximum_length, is_nullable "
            f"FROM information_schema.columns WHERE table_schema='public' "
            f"AND table_name='{TABLE}' AND column_name='{REQUIRED_COLUMN}';"
        ),
    }


def apply_migration(db) -> list[str]:
    if not MIGRATION_PATH.exists():
        raise FileNotFoundError(f"Migration not found: {MIGRATION_PATH}")
    sql = MIGRATION_PATH.read_text(encoding="utf-8")
    applied: list[str] = []
    for stmt in _split_sql(sql):
        db.session.execute(db.text(stmt))
        applied.append(stmt[:120].replace("\n", " ") + ("…" if len(stmt) > 120 else ""))
    db.session.commit()
    return applied


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only run information_schema verification (no DDL).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON result.",
    )
    args = parser.parse_args()

    sys.path.insert(0, str(ROOT))
    os.environ.setdefault("FLASK_ENV", os.environ.get("APP_ENV", "production"))

    from app import create_app
    from app.extensions.db import db

    app = create_app()
    result: dict = {
        "migration": MIGRATION_NAME,
        "migration_path": str(MIGRATION_PATH),
        "verify_only": bool(args.verify_only),
    }

    with app.app_context():
        dialect = db.engine.dialect.name
        result["dialect"] = dialect
        if dialect != "postgresql":
            result["ok"] = False
            result["error"] = (
                f"Refusing to run against dialect={dialect!r}; "
                "this runner is for PostgreSQL production only."
            )
            print(json.dumps(result, indent=2) if args.json else result["error"])
            return 1

        if not args.verify_only:
            try:
                applied = apply_migration(db)
                result["applied_statements"] = applied
            except Exception as exc:
                db.session.rollback()
                result["ok"] = False
                result["error"] = str(exc)
                print(json.dumps(result, indent=2) if args.json else f"APPLY FAILED: {exc}")
                return 1

        verification = verify_column(db)
        result["verification"] = verification
        result["ok"] = bool(verification.get("ok"))

        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            status = "PASS" if result["ok"] else "FAIL"
            print(f"[{status}] {MIGRATION_NAME}")
            print(f"  dialect: {dialect}")
            if not args.verify_only:
                print(f"  applied: {len(result.get('applied_statements') or [])} statement(s)")
            info = verification.get("column_info")
            if info:
                print(
                    "  column: "
                    f"{info.get('column_name')} "
                    f"{info.get('data_type')}({info.get('character_maximum_length')}) "
                    f"nullable={info.get('is_nullable')}"
                )
            else:
                print(f"  column: {REQUIRED_COLUMN} MISSING")
            fks = verification.get("foreign_keys") or []
            print(f"  foreign_keys: {len(fks)}")
            for fk in fks:
                print(
                    f"    - {fk.get('constraint_name')}: "
                    f"{fk.get('column_name')} → "
                    f"{fk.get('foreign_table_name')}.{fk.get('foreign_column_name')}"
                )
            idxs = verification.get("indexes") or []
            print(f"  indexes: {[i.get('indexname') for i in idxs]}")
            print(f"  verify_sql: {verification.get('verification_sql')}")

        return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
