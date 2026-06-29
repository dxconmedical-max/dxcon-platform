def build_engine_options(database_uri, pool_size=5, max_overflow=10, pool_recycle=280):
    uri = database_uri or ""

    if uri.startswith("sqlite"):
        options = {
            "connect_args": {"check_same_thread": False},
        }
        if ":memory:" not in uri:
            options["pool_pre_ping"] = True
        return options

    return {
        "pool_pre_ping": True,
        "pool_recycle": int(pool_recycle),
        "pool_size": int(pool_size),
        "max_overflow": int(max_overflow),
    }


def pool_status(app):
    from app.extensions.db import db

    uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    engine = db.engine

    status = {
        "driver": "sqlite" if uri.startswith("sqlite") else "postgresql" if uri.startswith("postgres") else "other",
        "pool_pre_ping": app.config.get("SQLALCHEMY_ENGINE_OPTIONS", {}).get("pool_pre_ping", False),
        "pool_size": app.config.get("SQLALCHEMY_ENGINE_OPTIONS", {}).get("pool_size"),
        "max_overflow": app.config.get("SQLALCHEMY_ENGINE_OPTIONS", {}).get("max_overflow"),
        "pool_recycle": app.config.get("SQLALCHEMY_ENGINE_OPTIONS", {}).get("pool_recycle"),
    }

    if engine is not None and hasattr(engine, "pool"):
        pool = engine.pool
        status.update(
            {
                "checked_in": getattr(pool, "checkedin", lambda: None)(),
                "checked_out": getattr(pool, "checkedout", lambda: None)(),
                "overflow": getattr(pool, "overflow", lambda: None)(),
                "size": getattr(pool, "size", lambda: None)(),
            }
        )

    return status


def review_pool_config(app):
    uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    notes = []

    if uri.startswith("postgres") and not app.config.get("SQLALCHEMY_ENGINE_OPTIONS"):
        notes.append("PostgreSQL should configure SQLALCHEMY_ENGINE_OPTIONS")

    options = app.config.get("SQLALCHEMY_ENGINE_OPTIONS", {})
    if uri.startswith("postgres"):
        if not options.get("pool_pre_ping"):
            notes.append("Enable pool_pre_ping for PostgreSQL")
        if not options.get("pool_recycle"):
            notes.append("Set pool_recycle to avoid stale connections")

    return {
        "ok": len(notes) == 0,
        "notes": notes,
        "engine_options": options,
    }
