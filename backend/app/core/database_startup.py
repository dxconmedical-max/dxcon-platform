import logging
import time

from sqlalchemy import inspect, text

from app.extensions.db import db

logger = logging.getLogger("dxcon.database")


def verify_database_connection(app, retries=None, delay_seconds=None):
    retries = retries if retries is not None else app.config.get("DB_CONNECT_RETRIES", 5)
    delay_seconds = delay_seconds if delay_seconds is not None else app.config.get(
        "DB_CONNECT_RETRY_DELAY_SECONDS", 2
    )

    last_error = None
    for attempt in range(1, int(retries) + 1):
        try:
            db.session.execute(text("SELECT 1"))
            db.session.commit()
            logger.info(
                "database connection verified",
                extra={"attempt": attempt, "retries": retries},
            )
            return True
        except Exception as exc:
            last_error = exc
            db.session.rollback()
            logger.warning(
                "database connection attempt failed",
                extra={"attempt": attempt, "error": str(exc)},
            )
            if attempt < retries:
                time.sleep(float(delay_seconds))

    raise RuntimeError(f"Database connection failed after {retries} attempts: {last_error}")


def verify_migrations(app):
    inspector = inspect(db.engine)
    tables = set(inspector.get_table_names())
    has_alembic = "alembic_version" in tables

    core_tables = {"users", "patients", "orders"}
    missing_core = sorted(core_tables - tables)

    status = {
        "alembic_present": has_alembic,
        "table_count": len(tables),
        "missing_core_tables": missing_core,
        "ready": len(missing_core) == 0,
    }

    if app.config.get("APP_ENV") == "production" and missing_core:
        logger.warning("migration verification found missing core tables", extra=status)

    return status


def startup_database_check(app):
    verify_database_connection(app)
    migration_status = verify_migrations(app)
    return migration_status
