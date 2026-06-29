import math


def normalize_page(page, default=1):
    try:
        value = int(page)
    except (TypeError, ValueError):
        value = default
    return max(value, 1)


def normalize_per_page(per_page, default=20, max_per_page=100):
    try:
        value = int(per_page)
    except (TypeError, ValueError):
        value = default
    return min(max(value, 1), max_per_page)


def paginate_query(query, page=1, per_page=20, max_per_page=100):
    page = normalize_page(page)
    per_page = normalize_per_page(per_page, max_per_page=max_per_page)

    total = query.count()
    items = query.limit(per_page).offset((page - 1) * per_page).all()
    pages = math.ceil(total / per_page) if per_page else 0

    return {
        "items": items,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": pages,
            "has_next": page < pages,
            "has_prev": page > 1,
        },
    }


def pagination_payload(items, pagination, serializer=None):
    serialized = [serializer(item) for item in items] if serializer else items
    return {
        "items": serialized,
        "pagination": pagination,
    }
