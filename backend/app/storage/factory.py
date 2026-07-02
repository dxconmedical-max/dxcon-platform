"""Storage provider factory."""

from __future__ import annotations

from flask import Flask

from app.storage.providers.base import StorageProvider
from app.storage.providers.local import LocalStorageProvider
from app.storage.providers.s3 import MinIOStorageProvider, S3StorageProvider

_EXTENSION_KEY = "dxcon_storage_provider"


def build_storage_provider(app: Flask) -> StorageProvider:
    provider = (app.config.get("STORAGE_PROVIDER") or app.config.get("STORAGE_BACKEND") or "local").lower()
    if provider in {"s3", "s3-compatible"}:
        return S3StorageProvider(
            bucket=app.config.get("S3_BUCKET", ""),
            region=app.config.get("S3_REGION", "us-east-1"),
            access_key=app.config.get("S3_ACCESS_KEY", ""),
            secret_key=app.config.get("S3_SECRET_KEY", ""),
            endpoint_url=app.config.get("S3_ENDPOINT_URL") or None,
        )
    if provider == "minio":
        return MinIOStorageProvider(
            bucket=app.config.get("S3_BUCKET", ""),
            access_key=app.config.get("S3_ACCESS_KEY", ""),
            secret_key=app.config.get("S3_SECRET_KEY", ""),
            endpoint_url=app.config.get("S3_ENDPOINT_URL", ""),
            region=app.config.get("S3_REGION", "us-east-1"),
        )
    return LocalStorageProvider(app.config.get("STORAGE_PATH", "uploads"))


def init_storage_platform(app: Flask) -> StorageProvider:
    provider = build_storage_provider(app)
    app.extensions[_EXTENSION_KEY] = provider
    return provider


def get_storage_provider(app=None) -> StorageProvider:
    from flask import current_app

    app = app or current_app._get_current_object()
    provider = app.extensions.get(_EXTENSION_KEY)
    if provider is None:
        provider = init_storage_platform(app)
    return provider
