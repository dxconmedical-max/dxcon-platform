"""Object storage platform package."""

from app.storage.attachment_service import AttachmentService
from app.storage.factory import get_storage_provider, init_storage_platform
from app.storage.metrics import storage_health, storage_metrics

__all__ = [
    "AttachmentService",
    "init_storage_platform",
    "get_storage_provider",
    "storage_health",
    "storage_metrics",
]
