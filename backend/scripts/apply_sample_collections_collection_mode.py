"""Apply sample_collections.collection_mode migration (idempotent)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

MIGRATION = ROOT / "migrations" / "021_sample_collections_collection_mode.sql"


def apply(db) -> dict:
    from sqlalchemy import text

    sql = MIGRATION.read_text(encoding="utf-8")
    # Split on statements carefully — migration uses plain SQL
    for statement in sql.split(";"):
        stmt = statement.strip()
        if not stmt or stmt.startswith("--"):
            # drop comment-only blocks
            lines = [
                line
                for line in stmt.splitlines()
                if line.strip() and not line.strip().startswith("--")
            ]
            stmt = "\n".join(lines).strip()
        if not stmt:
            continue
        db.session.execute(text(stmt))
    db.session.commit()

    from app.infrastructure.schema_introspection import get_table_columns

    columns = get_table_columns("sample_collections")
    ambiguous = db.session.execute(
        text(
            "SELECT COUNT(*) FROM sample_collections "
            "WHERE collection_mode IS NULL OR collection_mode = ''"
        )
    ).scalar()
    by_mode = db.session.execute(
        text(
            "SELECT COALESCE(collection_mode, 'NULL'), COUNT(*) "
            "FROM sample_collections GROUP BY 1 ORDER BY 1"
        )
    ).fetchall()
    return {
        "ok": "collection_mode" in columns,
        "columns_include_collection_mode": "collection_mode" in columns,
        "ambiguous_rows": int(ambiguous or 0),
        "by_mode": {str(row[0]): int(row[1]) for row in by_mode},
        "migration": str(MIGRATION),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    from app import create_app
    from app.extensions.db import db

    app = create_app()
    with app.app_context():
        result = apply(db)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(result)
    raise SystemExit(0 if result.get("ok") else 1)


if __name__ == "__main__":
    main()
