"""Storage health and metrics."""

from __future__ import annotations

from flask import Flask

from app.extensions.db import db
from app.storage.factory import get_storage_provider
from app.storage.models import FileMetadata


def storage_health(app: Flask | None = None) -> dict:
    from flask import current_app

    app = app or current_app._get_current_object()
    provider = get_storage_provider(app)
    health = provider.health()
    return {
        "status": "OK" if health.get("ok") else "DEGRADED",
        "provider": provider.name,
        "details": health,
    }


def storage_metrics(app: Flask | None = None) -> dict:
    from flask import current_app

    app = app or current_app._get_current_object()
    provider = get_storage_provider(app)
    total = FileMetadata.query.count()
    active = FileMetadata.query.filter_by(status="ACTIVE").count()
    archived = FileMetadata.query.filter_by(status="ARCHIVED").count()
    bytes_total = db.session.query(db.func.coalesce(db.func.sum(FileMetadata.size_bytes), 0)).scalar() or 0
    return {
        "provider": provider.name,
        "files_total": total,
        "files_active": active,
        "files_archived": archived,
        "bytes_total": int(bytes_total),
        "provider_health": provider.health(),
    }
