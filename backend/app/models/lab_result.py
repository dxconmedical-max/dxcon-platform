from datetime import datetime
import uuid

from app.extensions.db import db


class LabResult(db.Model):

    __tablename__ = "lab_results"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    result_code = db.Column(db.String(50), unique=True, nullable=False)

    medical_order_id = db.Column(
        db.String(36),
        db.ForeignKey("medical_orders.id"),
        nullable=False,
    )

    partner_id = db.Column(db.String(36))

    patient_id = db.Column(db.String(36))

    patient_name = db.Column(db.String(255))

    source_type = db.Column(db.String(50), default="MANUAL", nullable=False)

    status = db.Column(db.String(50), default="DRAFT", nullable=False)

    version = db.Column(db.Integer, default=1)

    released_version = db.Column(db.Integer)

    analyzer_payload_json = db.Column(db.Text)

    summary = db.Column(db.Text)

    is_locked = db.Column(db.Boolean, default=False)

    released_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    items = db.relationship(
        "LabResultItem",
        backref="lab_result",
        lazy=True,
        cascade="all, delete-orphan",
    )

    attachments = db.relationship(
        "ResultAttachment",
        backref="lab_result",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def to_dict(self, include_items=True, include_attachments=False):
        payload = {
            "id": self.id,
            "result_code": self.result_code,
            "medical_order_id": self.medical_order_id,
            "partner_id": self.partner_id,
            "patient_id": self.patient_id,
            "patient_name": self.patient_name,
            "source_type": self.source_type,
            "status": self.status,
            "version": self.version,
            "released_version": self.released_version,
            "summary": self.summary,
            "is_locked": self.is_locked,
            "released_at": self.released_at.isoformat() if self.released_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_items:
            payload["items"] = [item.to_dict() for item in self.items]
        if include_attachments:
            payload["attachments"] = [item.to_dict() for item in self.attachments]
        return payload
