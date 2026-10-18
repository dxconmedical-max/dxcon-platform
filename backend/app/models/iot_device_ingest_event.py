from __future__ import annotations

import uuid
from datetime import datetime

from app.extensions.db import db


class IoTDeviceIngestEvent(db.Model):
    """DB-backed idempotency + replay guard for device ingestion (P0-D)."""

    __tablename__ = "iot_device_ingest_events"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    device_id = db.Column(db.String(36), db.ForeignKey("iot_devices.id"), nullable=False, index=True)

    # Client-provided event identifiers.
    event_id = db.Column(db.String(128), nullable=True)
    nonce = db.Column(db.String(128), nullable=True, index=True)

    # Hash of the raw payload for conflict detection.
    payload_hash = db.Column(db.String(64), nullable=True)

    processed = db.Column(db.Boolean, default=True, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("device_id", "event_id", name="uq_iot_device_event_id"),
        db.UniqueConstraint("device_id", "nonce", name="uq_iot_device_nonce"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "event_id": self.event_id,
            "nonce": self.nonce,
            "payload_hash": self.payload_hash,
            "processed": self.processed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

