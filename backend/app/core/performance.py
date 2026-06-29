import time

from sqlalchemy import event

from app.core.performance_metrics import performance_metrics
from app.extensions.db import db


def init_performance(app):
    from app.core.background_tasks import background_tasks
    from app.core.db_pool import review_pool_config

    performance_metrics.set_slow_query_threshold_ms(
        app.config.get("SLOW_QUERY_THRESHOLD_MS", 100)
    )

    app.extensions["dxcon_performance"] = {
        "pool_review": review_pool_config(app),
        "background_tasks": background_tasks,
        "listeners_registered": False,
    }

    def register_engine_listeners(engine):
        if app.extensions["dxcon_performance"]["listeners_registered"]:
            return

        @event.listens_for(engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            conn.info.setdefault("query_start_time", []).append(time.perf_counter())

        @event.listens_for(engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            started_stack = conn.info.setdefault("query_start_time", [])
            if not started_stack:
                return

            started = started_stack.pop()
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            performance_metrics.record_query(duration_ms, label="sql")

        app.extensions["dxcon_performance"]["listeners_registered"] = True

    @app.before_request
    def ensure_performance_listeners():
        if app.extensions["dxcon_performance"]["listeners_registered"]:
            return None

        register_engine_listeners(db.engine)
        return None
