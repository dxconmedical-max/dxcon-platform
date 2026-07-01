INSECURE_DEFAULTS = {
    "SECRET_KEY": "dxcon-dev-secret",
    "JWT_SECRET_KEY": "dxcon-dev-jwt",
}


def _cors_strict_safe(app):
    from app.infrastructure.production_readiness import cors_status

    return cors_status(app)["ok"]


def validate_config(app):
    env = (app.config.get("APP_ENV") or "development").lower()
    issues = []

    for key, default in INSECURE_DEFAULTS.items():
        value = app.config.get(key)
        if value == default and env == "production":
            issues.append(f"{key} must be overridden in production")

    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        issues.append("DATABASE_URL must be configured")

    if app.config.get("MAX_CONTENT_LENGTH", 0) <= 0:
        issues.append("MAX_CONTENT_LENGTH must be greater than zero")

    if app.config.get("RATE_LIMIT_MAX", 0) <= 0:
        issues.append("RATE_LIMIT_MAX must be greater than zero")

    if app.config.get("JWT_ACCESS_TOKEN_EXPIRES") is None:
        issues.append("JWT_ACCESS_TOKEN_EXPIRES must be configured")

    if app.config.get("JWT_REFRESH_TOKEN_EXPIRES") is None:
        issues.append("JWT_REFRESH_TOKEN_EXPIRES must be configured")

    if env == "production":
        if not app.config.get("STORAGE_PATH"):
            issues.append("STORAGE_PATH must be configured in production")
        if app.config.get("SMTP_HOST") and not app.config.get("SMTP_FROM"):
            issues.append("SMTP_FROM must be configured when SMTP_HOST is set")

    from app.infrastructure.production_readiness import validate_production_config

    if issues:
        raise RuntimeError("; ".join(issues))

    validate_production_config(app)
    return True


def config_summary(app):
    return {
        "app_env": app.config.get("APP_ENV"),
        "database_configured": bool(app.config.get("SQLALCHEMY_DATABASE_URI")),
        "secret_key_from_env": app.config.get("SECRET_KEY") != INSECURE_DEFAULTS["SECRET_KEY"],
        "jwt_secret_from_env": app.config.get("JWT_SECRET_KEY") != INSECURE_DEFAULTS["JWT_SECRET_KEY"],
        "max_content_length": app.config.get("MAX_CONTENT_LENGTH"),
        "rate_limit_enabled": app.config.get("RATE_LIMIT_ENABLED"),
        "security_headers_enabled": app.config.get("SECURITY_HEADERS_ENABLED"),
        "cors_origins": app.config.get("CORS_ORIGINS"),
        "cors_strict_safe": _cors_strict_safe(app),
        "redis_configured": bool(app.config.get("REDIS_URL")),
        "smtp_configured": bool(app.config.get("SMTP_HOST")),
        "database_dialect": (app.config.get("SQLALCHEMY_DATABASE_URI") or "").split(":", 1)[0],
        "storage_backend": app.config.get("STORAGE_BACKEND"),
        "storage_path": app.config.get("STORAGE_PATH"),
        "api_response_envelope": app.config.get("API_RESPONSE_ENVELOPE"),
        "log_format": app.config.get("LOG_FORMAT"),
    }
