"""Database introspection helpers.

Public utilities used across modules. Avoid importing private underscore helpers
across packages to keep deployments stable.
"""

from __future__ import annotations


def table_has_column(db, table_name: str, column_name: str) -> bool:
    """Return True if `table_name` has `column_name`.

    - Works for PostgreSQL and SQLite (including sqlite :memory:).
    - Safe to call during startup, health checks, and migrations.
    """
    try:
        bind = db.session.get_bind()
        if bind.dialect.name == "sqlite":
            rows = db.session.execute(db.text(f"PRAGMA table_info({table_name})")).fetchall()
            return any(row[1] == column_name for row in rows)

        found = (
            db.session.execute(
                db.text(
                    "SELECT 1 FROM information_schema.columns "
                    "WHERE table_name = :table AND column_name = :column LIMIT 1"
                ),
                {"table": table_name, "column": column_name},
            ).first()
            is not None
        )
        return bool(found)
    except Exception:
        return False

