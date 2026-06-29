import random
import string
from datetime import datetime

from sqlalchemy import or_

from app.core.pagination import paginate_query, pagination_payload
from app.extensions.db import db


def generate_code(prefix, length=6):
    suffix = "".join(random.choices(string.digits, k=length))
    return f"{prefix}-{suffix}"


def apply_search(query, model, q, fields):
    if not q:
        return query
    clauses = []
    for field_name in fields:
        column = getattr(model, field_name, None)
        if column is not None:
            clauses.append(column.ilike(f"%{q}%"))
    if clauses:
        query = query.filter(or_(*clauses))
    return query


def apply_filters(query, model, filters):
    for key, value in filters.items():
        if value is None or value == "":
            continue
        column = getattr(model, key, None)
        if column is not None:
            query = query.filter(column == value)
    return query


def list_resource(model, serializer, search_fields=None, filters=None, page=1, per_page=20):
    query = model.query
    if filters:
        query = apply_filters(query, model, filters)
    if search_fields and filters and filters.get("q"):
        query = apply_search(query, model, filters["q"], search_fields)
    elif search_fields and isinstance(filters, dict):
        q = filters.get("q")
        if q:
            query = apply_search(query, model, q, search_fields)
    query = query.order_by(getattr(model, "created_at", model.id).desc())
    result = paginate_query(query, page=page, per_page=per_page)
    return pagination_payload(result["items"], result["pagination"], serializer=serializer)


def get_or_404(model, resource_id, error_cls):
    item = model.query.get(resource_id)
    if not item:
        raise error_cls(f"{model.__name__} not found", 404)
    return item


def parse_date(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    return datetime.fromisoformat(str(value)).date()


def parse_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00").replace("+00:00", ""))
