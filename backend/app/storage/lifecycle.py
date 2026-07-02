"""File lifecycle policy helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def retention_expiry(days: int) -> str:
    return (utc_now() + timedelta(days=max(days, 1))).date().isoformat()


def should_archive(status: str, retention_until: str | None) -> bool:
    if status != "ACTIVE" or not retention_until:
        return False
    return retention_until <= utc_now().date().isoformat()


def apply_lifecycle(metadata, *, retention_days: int):
    metadata.retention_until = retention_expiry(retention_days)
    if should_archive(metadata.status, metadata.retention_until):
        metadata.status = "ARCHIVED"
        metadata.updated_at = utc_now().isoformat()
    return metadata
