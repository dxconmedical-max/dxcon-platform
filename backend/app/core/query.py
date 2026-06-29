import time
from contextlib import contextmanager

from sqlalchemy.orm import joinedload

from app.core.performance_metrics import performance_metrics


def fetch_by_ids(model, ids, id_field="id"):
    if not ids:
        return []

    column = getattr(model, id_field)
    return model.query.filter(column.in_(list(ids))).all()


def with_joinedload(query, *relationships):
    options = [joinedload(relationship) for relationship in relationships]
    return query.options(*options)


def count_query(query):
    return query.order_by(None).count()


@contextmanager
def timed_query(label="query"):
    started = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        performance_metrics.record_query(duration_ms, label=label)
