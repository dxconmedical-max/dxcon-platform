from app.core.errors import ApiError
from app.core.pagination import normalize_page, normalize_per_page


ALLOWED_SORT_DIRECTIONS = {"asc", "desc"}


def parse_pagination_args(args, default_page=1, default_per_page=20, max_per_page=100):
    return (
        normalize_page(args.get("page"), default=default_page),
        normalize_per_page(args.get("page_size") or args.get("per_page"), default=default_per_page, max_per_page=max_per_page),
    )


def parse_sort(args, allowed_fields, default_field=None, default_direction="asc"):
    sort_field = args.get("sort") or args.get("sort_by") or default_field
    sort_direction = (args.get("direction") or args.get("sort_dir") or default_direction).lower()

    if sort_field and sort_field not in allowed_fields:
        raise ApiError(
            f"Invalid sort field: {sort_field}. Allowed: {', '.join(sorted(allowed_fields))}",
            status_code=422,
            code="VALIDATION_ERROR",
        )

    if sort_direction not in ALLOWED_SORT_DIRECTIONS:
        raise ApiError(
            f"Invalid sort direction: {sort_direction}. Allowed: asc, desc",
            status_code=422,
            code="VALIDATION_ERROR",
        )

    return sort_field, sort_direction


def parse_filters(args, allowed_filters):
    filters = {}
    for key in allowed_filters:
        value = args.get(key)
        if value not in (None, ""):
            filters[key] = value
    return filters


def apply_sort(query, model, sort_field, sort_direction):
    if not sort_field:
        return query
    column = getattr(model, sort_field, None)
    if column is None:
        return query
    if sort_direction == "desc":
        return query.order_by(column.desc())
    return query.order_by(column.asc())
