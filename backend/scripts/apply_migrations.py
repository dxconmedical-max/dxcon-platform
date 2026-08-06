#!/usr/bin/env python3
"""Apply all numbered backend/migrations/*.sql in order (PostgreSQL production).

Always includes 021_schema_reconciliation.sql when present.

Usage:
  cd backend
  python scripts/apply_migrations.py
  python scripts/apply_migrations.py --verify-only
  python scripts/apply_migrations.py --json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "migrations"
RECONCILIATION = "021_schema_reconciliation.sql"


def list_migration_files() -> list[Path]:
    files = sorted(MIGRATIONS.glob("*.sql"))
    # Ensure reconciliation is applied (already sorted by name among 021_*)
    return files


def split_sql(sql: str) -> list[str]:
    """Split SQL preserving DO $$ ... $$; blocks."""
    statements: list[str] = []
    buf: list[str] = []
    in_do = False
    for raw in sql.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            if in_do:
                buf.append(line)
            continue
        if not in_do and stripped.startswith("--"):
            continue
        upper = stripped.upper()
        if not in_do and upper.startswith("DO $$"):
            in_do = True
            buf = [line]
            if stripped.endswith("$$;") or "$$;" in stripped and stripped.count("$$") >= 2:
                # single-line DO (rare)
                if stripped.endswith("$$;"):
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
        if stripped.startswith("--"):
            continue
        buf.append(line)
        if stripped.endswith(";"):
            statements.append("\n".join(buf).strip().rstrip(";").strip())
            buf = []
    if buf:
        statements.append("\n".join(buf).strip().rstrip(";").strip())
    return [s for s in statements if s and not s.strip().startswith("--")]


def apply_file(db, path: Path) -> int:
    sql = path.read_text(encoding="utf-8")
    count = 0
    for stmt in split_sql(sql):
        db.session.execute(db.text(stmt))
        count += 1
    db.session.commit()
    return count


def verify_reconciliation(db) -> dict:
    """Check every ORM-mapped table/column exists in public schema."""
    from app.extensions.db import db as _db  # noqa: F401

    metadata_tables = list(db.Model.metadata.tables.keys())
    results = []
    fails = 0
    for table_name in sorted(metadata_tables):
        table = db.Model.metadata.tables[table_name]
        exists = db.session.execute(
            db.text(
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_schema='public' AND table_name=:t"
            ),
            {"t": table_name},
        ).scalar()
        if not exists:
            results.append({"table": table_name, "status": "FAIL", "detail": "missing table"})
            fails += 1
            continue
        rows = db.session.execute(
            db.text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema='public' AND table_name=:t"
            ),
            {"t": table_name},
        ).fetchall()
        present = {r[0] for r in rows}
        missing = [c.name for c in table.columns if c.name not in present]
        if missing:
            results.append(
                {
                    "table": table_name,
                    "status": "FAIL",
                    "detail": f"missing columns: {', '.join(missing)}",
                }
            )
            fails += 1
        else:
            results.append({"table": table_name, "status": "PASS", "detail": f"{len(present)} cols"})
    return {
        "ok": fails == 0,
        "fail_count": fails,
        "pass_count": len(results) - fails,
        "tables": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--only",
        action="append",
        default=[],
        help="Apply only named migration files (repeatable).",
    )
    args = parser.parse_args()

    sys.path.insert(0, str(ROOT))
    os.environ.setdefault("FLASK_ENV", os.environ.get("APP_ENV", "production"))

    from app import create_app
    from app.extensions.db import db

    app = create_app()
    result: dict = {"ok": False, "applied": [], "verify_only": bool(args.verify_only)}

    with app.app_context():
        dialect = db.engine.dialect.name
        result["dialect"] = dialect
        if dialect != "postgresql":
            result["error"] = (
                f"Refusing to run against dialect={dialect!r}; PostgreSQL only."
            )
            print(json.dumps(result, indent=2) if args.json else result["error"])
            return 1

        files = list_migration_files()
        if args.only:
            wanted = set(args.only)
            files = [p for p in files if p.name in wanted]
        # Prefer ensuring reconciliation is present
        names = [p.name for p in files]
        if RECONCILIATION not in names and (MIGRATIONS / RECONCILIATION).exists():
            if not args.only:
                files.append(MIGRATIONS / RECONCILIATION)
                files = sorted(set(files), key=lambda p: p.name)

        if not args.verify_only:
            for path in files:
                try:
                    n = apply_file(db, path)
                    result["applied"].append({"file": path.name, "statements": n, "status": "ok"})
                except Exception as exc:
                    db.session.rollback()
                    result["applied"].append(
                        {"file": path.name, "status": "error", "error": str(exc)}
                    )
                    result["error"] = f"{path.name}: {exc}"
                    print(json.dumps(result, indent=2) if args.json else f"FAIL {path.name}: {exc}")
                    return 1

        verification = verify_reconciliation(db)
        result["verification"] = {
            "ok": verification["ok"],
            "pass_count": verification["pass_count"],
            "fail_count": verification["fail_count"],
        }
        result["verification_tables"] = verification["tables"]
        result["ok"] = bool(verification["ok"])
        result["reconciliation_included"] = any(
            a.get("file") == RECONCILIATION for a in result.get("applied", [])
        ) or (args.verify_only and (MIGRATIONS / RECONCILIATION).exists())

        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            status = "PASS" if result["ok"] else "FAIL"
            print(f"[{status}] apply_migrations")
            print(f"  dialect: {dialect}")
            print(f"  applied files: {len(result.get('applied') or [])}")
            for item in result.get("applied") or []:
                print(f"    - {item['file']}: {item.get('statements', item.get('status'))}")
            print(
                f"  model verification: "
                f"{verification['pass_count']} PASS / {verification['fail_count']} FAIL"
            )
            if not verification["ok"]:
                for row in verification["tables"]:
                    if row["status"] == "FAIL":
                        print(f"    FAIL {row['table']}: {row['detail']}")
        return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
