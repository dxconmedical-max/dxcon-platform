from collections import defaultdict

DEPRECATED_PREFIXES = (
    "/api/v2/",
    "/api/v1/notification-templates",
    "/api/v1/admin-security",
)

INTERNAL_PREFIXES = (
    "/api/v1/_observability/",
    "/api/v1/system/metrics",
)

UNSTABLE_PREFIXES = (
    "/api/v1/developer/",
    "/api/v1/sandbox/",
    "/api/v1/api-platform/",
)


def _methods(rule):
    return sorted(m for m in rule.methods if m not in {"HEAD", "OPTIONS"})


def _blueprint_name(endpoint):
    return endpoint.split(".")[0] if "." in endpoint else endpoint


def scan_routes(app):
    routes = []
    duplicates = []
    deprecated = []
    internal = []
    unstable = []
    route_map = defaultdict(list)

    for rule in app.url_map.iter_rules():
        path = str(rule)
        if not path.startswith("/api/v1/"):
            continue
        methods = _methods(rule)
        entry = {
            "path": path,
            "methods": methods,
            "endpoint": rule.endpoint,
            "blueprint": _blueprint_name(rule.endpoint),
        }
        routes.append(entry)
        route_map[(path, tuple(methods))].extend([rule.endpoint])

        if any(path.startswith(prefix) for prefix in DEPRECATED_PREFIXES):
            deprecated.append(entry)
        if any(prefix in path for prefix in INTERNAL_PREFIXES):
            internal.append(entry)
        if any(path.startswith(prefix) for prefix in UNSTABLE_PREFIXES):
            unstable.append(entry)

    for key, endpoints in route_map.items():
        if len(endpoints) > 1:
            duplicates.append({"path": key[0], "methods": list(key[1]), "endpoints": endpoints})

    return {
        "routes": routes,
        "count": len(routes),
        "duplicates": duplicates,
        "deprecated": deprecated,
        "internal": internal,
        "unstable": unstable,
        "summary": {
            "total": len(routes),
            "duplicate_count": len(duplicates),
            "deprecated_count": len(deprecated),
            "internal_count": len(internal),
            "unstable_count": len(unstable),
        },
    }
