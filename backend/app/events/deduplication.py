import hashlib
import json
import uuid
from datetime import datetime, timedelta

from flask import current_app

from app.extensions.db import db


class EventDedupRecord(db.Model):
    __tablename__ = "event_dedup_records"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    fingerprint = db.Column(db.String(128), unique=True, nullable=False, index=True)
    event_id = db.Column(db.String(36), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class EventDeduplicationService:
    @staticmethod
    def fingerprint(event_type, payload, correlation_id=None):
        raw = json.dumps(
            {"event_type": event_type, "payload": payload or {}, "correlation_id": correlation_id},
            sort_keys=True,
        )
        return hashlib.sha256(raw.encode()).hexdigest()

    @staticmethod
    def is_duplicate(event_type, payload, correlation_id=None):
        fp = EventDeduplicationService.fingerprint(event_type, payload, correlation_id)
        existing = EventDedupRecord.query.filter_by(fingerprint=fp).first()
        if existing:
            return True, existing.event_id
        return False, None

    @staticmethod
    def register(event_id, event_type, payload, correlation_id=None):
        fp = EventDeduplicationService.fingerprint(event_type, payload, correlation_id)
        ttl = current_app.config.get("EVENT_DEDUP_TTL_SECONDS", 3600)
        cutoff = datetime.utcnow() - timedelta(seconds=int(ttl))
        EventDedupRecord.query.filter(EventDedupRecord.created_at < cutoff).delete()
        existing = EventDedupRecord.query.filter_by(fingerprint=fp).first()
        if existing:
            return {"duplicate": True, "event_id": existing.event_id}
        row = EventDedupRecord(fingerprint=fp, event_id=event_id)
        db.session.add(row)
        db.session.commit()
        return {"duplicate": False, "event_id": event_id}
