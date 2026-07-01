from datetime import datetime, timezone

API_VERSION = "v1"
API_STABILITY = "stable"
API_SUNSET = None

DEPRECATION_METADATA = {
    "/api/v1/notification-templates": {
        "deprecated": True,
        "sunset": "2026-12-31",
        "successor": "/api/v1/templates",
    },
    "/api/v1/admin-security": {
        "deprecated": True,
        "sunset": "2026-12-31",
        "successor": "/api/v1/security/",
    },
}


def v1_policy():
    return {
        "version": API_VERSION,
        "stability": API_STABILITY,
        "prefix": "/api/v1",
        "sunset": API_SUNSET,
        "deprecation_supported": True,
    }


def route_metadata(path: str):
    for prefix, meta in DEPRECATION_METADATA.items():
        if path == prefix or path.startswith(prefix + "/"):
            return meta
    return {"deprecated": False}


def apply_version_headers(response, path: str):
    response.headers["X-API-Version"] = API_VERSION
    response.headers["X-API-Stability"] = API_STABILITY
    meta = route_metadata(path)
    if meta.get("deprecated"):
        response.headers["Deprecation"] = "true"
        if meta.get("sunset"):
            response.headers["Sunset"] = meta["sunset"]
        if meta.get("successor"):
            response.headers["Link"] = f'<{meta["successor"]}>; rel="successor-version"'
    return response


def version_info():
    return {
        "version": API_VERSION,
        "stability": API_STABILITY,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "policy": v1_policy(),
        "deprecated_routes": len(DEPRECATION_METADATA),
    }
