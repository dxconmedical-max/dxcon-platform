SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": "default-src 'self'",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}

RATE_LIMIT_EXEMPT_PATHS = {
    "/api/v1/system/health",
    "/api/v1/system/live",
    "/api/v1/system/ready",
    "/api/v1/system/metrics",
    "/api/v1/system/version",
    "/api/v1/system/build",
}


# Explicit browser origins for deployed API (never wildcard with credentials).
PRODUCTION_CORS_ORIGINS = (
    "https://dxcon.com.vn,"
    "https://www.dxcon.com.vn,"
    "https://app.dxcon.com.vn"
)
STAGING_CORS_ORIGINS = (
    "https://staging.dxcon.com.vn,"
    "https://app-staging.dxcon.com.vn"
)


def init_security(app):
    from flask_cors import CORS

    from app.core.errors import build_error_response
    from app.core.rate_limit import check_rate_limit
    from app.infrastructure.production_readiness import app_env, is_relaxed_env, is_strict_env

    cors_origins = (app.config.get("CORS_ORIGINS") or "*").strip()
    env = app_env(app)
    # In staging/production, never leave CORS empty after rejecting "*".
    # Empty origins omit Access-Control-Allow-Origin and break browser login.
    # Use is_strict_env (APP_ENV) so unit tests with TESTING=True still exercise this path.
    if is_strict_env(app) and (cors_origins == "*" or not cors_origins):
        cors_origins = (
            STAGING_CORS_ORIGINS if env == "staging" else PRODUCTION_CORS_ORIGINS
        )
        app.config["CORS_ORIGINS"] = cors_origins
    if cors_origins == "*":
        CORS(
            app,
            resources={r"/api/*": {"origins": "*"}},
            supports_credentials=False,
        )
    else:
        origins = [
            origin.strip()
            for origin in cors_origins.split(",")
            if origin.strip()
        ]
        CORS(
            app,
            resources={r"/api/*": {"origins": origins}},
            supports_credentials=True,
            allow_headers=[
                "Authorization",
                "Content-Type",
                "X-Organization-ID",
                "X-Correlation-ID",
                "X-Request-ID",
                "Idempotency-Key",
            ],
            expose_headers=["X-Correlation-ID", "X-Request-ID"],
            methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        )

    if not app.config.get("MAX_CONTENT_LENGTH"):
        app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024

    @app.after_request
    def apply_security_headers(response):
        if not app.config.get("SECURITY_HEADERS_ENABLED", True):
            return response

        for header, value in SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)
        return response

    @app.before_request
    def enforce_rate_limit():
        if not app.config.get("RATE_LIMIT_ENABLED", True):
            return None

        if app.config.get("TESTING"):
            return None

        from flask import request

        if not request.path.startswith("/api/"):
            return None

        if request.path in RATE_LIMIT_EXEMPT_PATHS:
            return None

        client_key = request.headers.get("X-Forwarded-For", request.remote_addr) or "unknown"
        if not check_rate_limit(app, client_key):
            return build_error_response(
                "RATE_LIMIT_EXCEEDED",
                "Too many requests",
                429,
            )

        return None
