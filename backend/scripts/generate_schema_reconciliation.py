#!/usr/bin/env python3
"""Generate 021_schema_reconciliation.sql from live SQLAlchemy metadata.

Audits every mapped table/column against backend/migrations/*.sql, writes:
  - backend/migrations/021_schema_reconciliation.sql
  - backend/generated_release/SCHEMA_DRIFT_REPORT.json

Rules encoded in the migration:
  - PostgreSQL only
  - CREATE TABLE IF NOT EXISTS (PK skeleton)
  - ADD COLUMN IF NOT EXISTS (all mapped columns)
  - CREATE INDEX IF NOT EXISTS (column indexes + unique indexes)
  - ADD CONSTRAINT only inside existence-checked DO blocks
  - never DROP / ALTER TYPE / DELETE
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "migrations"
OUT_SQL = MIGRATIONS / "021_schema_reconciliation.sql"
OUT_REPORT = ROOT / "generated_release" / "SCHEMA_DRIFT_REPORT.json"


def _bootstrap_app():
    if "DATABASE_URL" not in os.environ:
        tf = tempfile.NamedTemporaryFile(prefix="dxcon_schema_gen_", suffix=".db", delete=False)
        tf.close()
        os.environ["DATABASE_URL"] = f"sqlite:///{tf.name}"
    sys.path.insert(0, str(ROOT))
    from app import create_app
    from app.extensions.db import db

    app = create_app()
    return app, db


def _pg_type(column) -> str:
    from sqlalchemy.dialects import postgresql

    try:
        compiled = column.type.compile(dialect=postgresql.dialect())
        return str(compiled)
    except Exception:
        # Fallback for uncommon types
        name = type(column.type).__name__.upper()
        length = getattr(column.type, "length", None)
        if name in {"VARCHAR", "STRING"} and length:
            return f"VARCHAR({length})"
        if name in {"VARCHAR", "STRING"}:
            return "VARCHAR"
        if name in {"TEXT"}:
            return "TEXT"
        if name in {"BOOLEAN", "BOOL"}:
            return "BOOLEAN"
        if name in {"INTEGER", "INT"}:
            return "INTEGER"
        if name in {"BIGINT"}:
            return "BIGINT"
        if name in {"FLOAT", "REAL", "DOUBLE"}:
            return "DOUBLE PRECISION"
        if name in {"NUMERIC", "DECIMAL"}:
            precision = getattr(column.type, "precision", None)
            scale = getattr(column.type, "scale", None)
            if precision is not None and scale is not None:
                return f"NUMERIC({precision},{scale})"
            if precision is not None:
                return f"NUMERIC({precision})"
            return "NUMERIC"
        if name in {"DATETIME", "TIMESTAMP", "DATE"}:
            return "TIMESTAMP" if name != "DATE" else "DATE"
        if name in {"JSON", "JSONB"}:
            return "JSONB"
        if name in {"UUID"}:
            return "UUID"
        return "TEXT"


def _default_sql(column) -> str:
    if column.default is None and column.server_default is None:
        return ""
    # Prefer server_default when present
    if column.server_default is not None:
        try:
            text = str(column.server_default.arg)
            if text.upper() in {"TRUE", "FALSE"}:
                return f" DEFAULT {text.upper()}"
            if text.isdigit() or (text.startswith("-") and text[1:].isdigit()):
                return f" DEFAULT {text}"
            return f" DEFAULT {text}"
        except Exception:
            pass
    # Python-side defaults: only emit for simple scalars / bools
    default = column.default
    if default is not None and getattr(default, "is_scalar", False):
        arg = default.arg
        if isinstance(arg, bool):
            return f" DEFAULT {'TRUE' if arg else 'FALSE'}"
        if isinstance(arg, (int, float)):
            return f" DEFAULT {arg}"
        if isinstance(arg, str) and len(arg) < 64:
            escaped = arg.replace("'", "''")
            return f" DEFAULT '{escaped}'"
    # Common Flask-SQLAlchemy bool defaults via callable-less Column(default=False)
    if default is not None and not getattr(default, "is_callable", False):
        arg = getattr(default, "arg", None)
        if isinstance(arg, bool):
            return f" DEFAULT {'TRUE' if arg else 'FALSE'}"
    return ""


def _scan_migrations() -> dict:
    """Parse existing migrations for CREATE TABLE / ADD COLUMN / INDEX / CONSTRAINT mentions."""
    tables: set[str] = set()
    columns: dict[str, set[str]] = defaultdict(set)
    indexes: set[str] = set()
    constraints: set[str] = set()

    create_re = re.compile(
        r"CREATE TABLE IF NOT EXISTS\s+([a-zA-Z0-9_]+)\s*\((.*?)\)\s*;",
        re.I | re.S,
    )
    add_re = re.compile(
        r"ALTER TABLE\s+([a-zA-Z0-9_]+)\s+ADD COLUMN IF NOT EXISTS\s+([a-zA-Z0-9_]+)",
        re.I,
    )
    index_re = re.compile(
        r"CREATE (?:UNIQUE )?INDEX IF NOT EXISTS\s+([a-zA-Z0-9_]+)",
        re.I,
    )
    constraint_re = re.compile(
        r"ADD CONSTRAINT\s+([a-zA-Z0-9_]+)",
        re.I,
    )

    for path in sorted(MIGRATIONS.glob("*.sql")):
        if path.name.startswith("021_schema_reconciliation"):
            continue
        text = path.read_text(encoding="utf-8")
        for m in create_re.finditer(text):
            table = m.group(1)
            tables.add(table)
            body = m.group(2)
            for line in body.splitlines():
                line = line.strip().rstrip(",")
                if not line:
                    continue
                upper = line.upper()
                if upper.startswith("PRIMARY") or upper.startswith("CONSTRAINT") or upper.startswith("UNIQUE") or upper.startswith("FOREIGN"):
                    continue
                name = line.split()[0]
                if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
                    columns[table].add(name)
        for m in add_re.finditer(text):
            tables.add(m.group(1))
            columns[m.group(1)].add(m.group(2))
        for m in index_re.finditer(text):
            indexes.add(m.group(1))
        for m in constraint_re.finditer(text):
            constraints.add(m.group(1))

    return {
        "tables": tables,
        "columns": {k: sorted(v) for k, v in columns.items()},
        "indexes": sorted(indexes),
        "constraints": sorted(constraints),
    }


def _patient_fk_quirk_targets() -> set[str]:
    """FKs targeting patients.id are unsafe on production (patient_code PK)."""
    return {"patients.id"}


def generate() -> dict:
    app, db = _bootstrap_app()
    from sqlalchemy import UniqueConstraint
    from sqlalchemy.schema import ForeignKeyConstraint

    with app.app_context():
        # Ensure HomeSampling and other optional packages are loaded when possible
        try:
            import app.models.home_sampling  # noqa: F401
        except Exception:
            pass
        try:
            import app.patient_marketplace.models  # noqa: F401
        except Exception:
            pass
        try:
            import app.mobile_mvp.models  # noqa: F401
        except Exception:
            pass
        try:
            import app.integration.models  # noqa: F401
        except Exception:
            pass

        metadata = db.Model.metadata
        mig = _scan_migrations()

        missing_tables: list[str] = []
        missing_columns: dict[str, list[str]] = {}
        missing_indexes: list[dict] = []
        missing_uniques: list[dict] = []
        missing_fks: list[dict] = []

        sql_lines: list[str] = []
        sql_lines.append("-- DxCon full schema reconciliation — additive, idempotent.")
        sql_lines.append("-- Generated from SQLAlchemy metadata. PostgreSQL only.")
        sql_lines.append("--")
        sql_lines.append("-- Rules:")
        sql_lines.append("--   * CREATE TABLE IF NOT EXISTS (PK skeleton)")
        sql_lines.append("--   * ADD COLUMN IF NOT EXISTS")
        sql_lines.append("--   * CREATE INDEX IF NOT EXISTS")
        sql_lines.append("--   * ADD CONSTRAINT only when missing (DO blocks)")
        sql_lines.append("--   * never DROP / ALTER TYPE / DELETE")
        sql_lines.append("--")
        sql_lines.append(f"-- Generated at: {datetime.now(timezone.utc).isoformat()}")
        sql_lines.append(f"-- ORM tables: {len(metadata.tables)}")
        sql_lines.append("")

        for table_name in sorted(metadata.tables.keys()):
            table = metadata.tables[table_name]
            orm_cols = {c.name for c in table.columns}
            mig_cols = set(mig["columns"].get(table_name, []))
            if table_name not in mig["tables"]:
                missing_tables.append(table_name)
            col_miss = sorted(orm_cols - mig_cols)
            if col_miss:
                missing_columns[table_name] = col_miss

            sql_lines.append(f"-- ===== {table_name} =====")
            pk_cols = [c for c in table.columns if c.primary_key]
            if not pk_cols:
                # No PK — create empty table with first column as soft key
                first = list(table.columns)[0]
                sql_lines.append(
                    f"CREATE TABLE IF NOT EXISTS {table_name} ("
                    f"{first.name} {_pg_type(first)}"
                    f");"
                )
            else:
                pk_defs = []
                for c in pk_cols:
                    null_sql = " NOT NULL" if not c.nullable or c.primary_key else ""
                    pk_defs.append(f"    {c.name} {_pg_type(c)}{null_sql}")
                pk_names = ", ".join(c.name for c in pk_cols)
                sql_lines.append(f"CREATE TABLE IF NOT EXISTS {table_name} (")
                sql_lines.append(",\n".join(pk_defs) + ",")
                sql_lines.append(f"    PRIMARY KEY ({pk_names})")
                sql_lines.append(");")
            sql_lines.append("")

            for column in table.columns:
                # Always ADD IF NOT EXISTS so existing incomplete tables catch up
                typ = _pg_type(column)
                default = _default_sql(column)
                sql_lines.append(
                    f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS "
                    f"{column.name} {typ}{default};"
                )
            sql_lines.append("")

            # Column-level indexes
            for column in table.columns:
                if column.index or column.unique:
                    idx_name = f"ix_{table_name}_{column.name}"[:63]
                    unique = "UNIQUE " if column.unique and not column.primary_key else ""
                    if idx_name not in mig["indexes"] and not column.primary_key:
                        missing_indexes.append(
                            {"table": table_name, "index": idx_name, "columns": [column.name]}
                        )
                    if not column.primary_key:
                        sql_lines.append(
                            f"CREATE {unique}INDEX IF NOT EXISTS {idx_name} "
                            f"ON {table_name} ({column.name});"
                        )
            sql_lines.append("")

            # UniqueConstraint from table args
            for const in table.constraints:
                if isinstance(const, UniqueConstraint):
                    cols = [c.name for c in const.columns]
                    name = const.name or f"uq_{table_name}_{'_'.join(cols)}"
                    name = name[:63]
                    if name not in mig["constraints"]:
                        missing_uniques.append(
                            {"table": table_name, "constraint": name, "columns": cols}
                        )
                    col_list = ", ".join(cols)
                    sql_lines.append(
                        "DO $$\n"
                        "BEGIN\n"
                        "  IF NOT EXISTS (\n"
                        "    SELECT 1 FROM pg_constraint\n"
                        "    WHERE conname = '" + name + "'\n"
                        "  ) THEN\n"
                        f"    ALTER TABLE {table_name}\n"
                        f"      ADD CONSTRAINT {name} UNIQUE ({col_list});\n"
                        "  END IF;\n"
                        "END $$;"
                    )
            sql_lines.append("")

            # Foreign keys (skip known patients.id production quirk)
            quirk = _patient_fk_quirk_targets()
            for fk in table.foreign_key_constraints:
                assert isinstance(fk, ForeignKeyConstraint)
                cols = [c.name for c in fk.columns]
                remote = []
                skip = False
                for element in fk.elements:
                    target = f"{element.column.table.name}.{element.column.name}"
                    remote.append(target)
                    if target in quirk:
                        skip = True
                if skip:
                    sql_lines.append(
                        f"-- skip FK on {table_name}({', '.join(cols)}) → "
                        f"{', '.join(remote)} (patients PK quirk)"
                    )
                    continue
                name = fk.name or f"fk_{table_name}_{'_'.join(cols)}"
                name = name[:63]
                if name not in mig["constraints"]:
                    missing_fks.append(
                        {
                            "table": table_name,
                            "constraint": name,
                            "columns": cols,
                            "ref": remote,
                        }
                    )
                local = ", ".join(cols)
                # REFERENCES table(col[,col])
                ref_table = fk.elements[0].column.table.name
                ref_cols = ", ".join(el.column.name for el in fk.elements)
                sql_lines.append(
                    "DO $$\n"
                    "BEGIN\n"
                    f"  IF to_regclass('public.{ref_table}') IS NULL THEN\n"
                    f"    RAISE NOTICE '{ref_table} missing — skip FK {name}';\n"
                    "    RETURN;\n"
                    "  END IF;\n"
                    "  IF EXISTS (\n"
                    "    SELECT 1 FROM pg_constraint WHERE conname = '" + name + "'\n"
                    "  ) THEN\n"
                    "    RETURN;\n"
                    "  END IF;\n"
                    f"  ALTER TABLE {table_name}\n"
                    f"    ADD CONSTRAINT {name}\n"
                    f"    FOREIGN KEY ({local}) REFERENCES {ref_table} ({ref_cols});\n"
                    "EXCEPTION WHEN others THEN\n"
                    f"  RAISE NOTICE 'skip FK {name}: %', SQLERRM;\n"
                    "END $$;"
                )
            sql_lines.append("")

        OUT_SQL.write_text("\n".join(sql_lines) + "\n", encoding="utf-8")

        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "orm_table_count": len(metadata.tables),
            "migration_table_count_before": len(mig["tables"]),
            "missing_tables_count": len(missing_tables),
            "missing_tables": missing_tables,
            "missing_columns_count": sum(len(v) for v in missing_columns.values()),
            "missing_columns": missing_columns,
            "missing_indexes_count": len(missing_indexes),
            "missing_indexes": missing_indexes[:500],
            "missing_unique_constraints_count": len(missing_uniques),
            "missing_unique_constraints": missing_uniques,
            "missing_foreign_keys_count": len(missing_fks),
            "missing_foreign_keys": missing_fks[:500],
            "sample_collections": {
                "orm_columns": sorted(
                    c.name for c in metadata.tables["sample_collections"].columns
                )
                if "sample_collections" in metadata.tables
                else [],
                "migration_columns_before": mig["columns"].get("sample_collections", []),
                "missing_before": missing_columns.get("sample_collections", []),
            },
            "output_migration": str(OUT_SQL.relative_to(ROOT.parent))
            if OUT_SQL.exists()
            else str(OUT_SQL),
        }
        OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
        OUT_REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report


def main() -> int:
    report = generate()
    print(
        json.dumps(
            {
                "ok": True,
                "orm_tables": report["orm_table_count"],
                "missing_tables": report["missing_tables_count"],
                "missing_columns": report["missing_columns_count"],
                "missing_indexes": report["missing_indexes_count"],
                "missing_uniques": report["missing_unique_constraints_count"],
                "missing_fks": report["missing_foreign_keys_count"],
                "migration": str(OUT_SQL),
                "report": str(OUT_REPORT),
                "sample_collections_missing_before": report["sample_collections"][
                    "missing_before"
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
