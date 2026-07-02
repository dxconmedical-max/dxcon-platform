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
    QUEUE_PROVIDER = os.getenv("QUEUE_PROVIDER", "memory")
    SCHEDULER_PROVIDER = os.getenv("SCHEDULER_PROVIDER", "apscheduler")
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "")
    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "")

    BUILD_VERSION = os.getenv("BUILD_VERSION", "2.5.0-dev")
    GIT_SHA = os.getenv("GIT_SHA", "local")
    BUILD_TIME = os.getenv("BUILD_TIME", "")

    CORRELATION_ID_HEADER = os.getenv("CORRELATION_ID_HEADER", "X-Correlation-ID")

    DB_CONNECT_RETRIES = int(os.getenv("DB_CONNECT_RETRIES", "5"))
    DB_CONNECT_RETRY_DELAY_SECONDS = float(os.getenv("DB_CONNECT_RETRY_DELAY_SECONDS", "2"))
    STARTUP_VALIDATE_DB = os.getenv("STARTUP_VALIDATE_DB", "true").lower() in {
        "1", "true", "yes", "on",
    }

    API_RESPONSE_ENVELOPE = os.getenv("API_RESPONSE_ENVELOPE", "true").lower() in {
        "1", "true", "yes", "on",
    }

    TRACE_ID_HEADER = os.getenv("TRACE_ID_HEADER", "X-Trace-ID")
    TENANT_ID_HEADER = os.getenv("TENANT_ID_HEADER", "X-Tenant-ID")

    REDIS_URL = os.getenv("REDIS_URL", "")
    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM = os.getenv("SMTP_FROM", "")
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes", "on"}

    STORAGE_PATH = os.getenv("STORAGE_PATH", "uploads")
    STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local")
    STORAGE_PROVIDER = os.getenv("STORAGE_PROVIDER", os.getenv("STORAGE_BACKEND", "local"))
    S3_BUCKET = os.getenv("S3_BUCKET", "")
    S3_REGION = os.getenv("S3_REGION", "us-east-1")
    S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "")
    S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "")
    S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", "")
    SIGNED_URL_TTL_SECONDS = int(os.getenv("SIGNED_URL_TTL_SECONDS", "3600"))
    FILE_MAX_SIZE_BYTES = int(os.getenv("FILE_MAX_SIZE_BYTES", str(10 * 1024 * 1024)))
    FILE_RETENTION_DAYS = int(os.getenv("FILE_RETENTION_DAYS", "365"))

    INTEGRATION_SIGNING_SECRET = os.getenv("INTEGRATION_SIGNING_SECRET", "dxcon-integration-secret")
    WEBHOOK_IDEMPOTENCY_TTL_SECONDS = int(os.getenv("WEBHOOK_IDEMPOTENCY_TTL_SECONDS", "86400"))
    SANDBOX_TOKEN_TTL_SECONDS = int(os.getenv("SANDBOX_TOKEN_TTL_SECONDS", "3600"))
    EVENT_DEDUP_TTL_SECONDS = int(os.getenv("EVENT_DEDUP_TTL_SECONDS", "3600"))
