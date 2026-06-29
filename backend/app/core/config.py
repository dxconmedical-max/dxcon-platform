import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "dxcon-dev-secret",
    )

    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY",
        "dxcon-dev-jwt",
    )

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///dxcon.db",
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    APP_ENV = os.getenv(
        "APP_ENV",
        "development",
    )

    LOG_LEVEL = os.getenv(
        "LOG_LEVEL",
        "INFO",
    )

    LOG_FORMAT = os.getenv(
        "LOG_FORMAT",
        "text",
    )

    REQUEST_ID_HEADER = os.getenv(
        "REQUEST_ID_HEADER",
        "X-Request-ID",
    )

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        hours=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_HOURS", "1"))
    )

    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        days=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES_DAYS", "30"))
    )

    JWT_BLOCKLIST_ENABLED = True

    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(1024 * 1024)))

    RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX", "120"))
    RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))

    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS",
        "*",
    )

    SECURITY_HEADERS_ENABLED = os.getenv(
        "SECURITY_HEADERS_ENABLED",
        "true",
    ).lower() in {"1", "true", "yes", "on"}

    RATE_LIMIT_ENABLED = os.getenv(
        "RATE_LIMIT_ENABLED",
        "true",
    ).lower() in {"1", "true", "yes", "on"}

    DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
    DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "280"))

    CACHE_DEFAULT_TTL_SECONDS = int(os.getenv("CACHE_DEFAULT_TTL_SECONDS", "60"))
    SLOW_QUERY_THRESHOLD_MS = float(os.getenv("SLOW_QUERY_THRESHOLD_MS", "100"))
    BACKGROUND_TASK_WORKERS = int(os.getenv("BACKGROUND_TASK_WORKERS", "4"))
