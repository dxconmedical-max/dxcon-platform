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
    "/api/v1/system/metrics",
}


def init_security(app):
    from flask_cors import CORS

    from app.core.errors import build_error_response
    from app.core.rate_limit import check_rate_limit

    cors_origins = app.config.get("CORS_ORIGINS", "*")
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
