from datetime import datetime
import uuid

from app.extensions.db import db


class SampleIncident(db.Model):

    __tablename__ = "sample_incidents"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    medical_order_id = db.Column(
        db.String(36),
        db.ForeignKey("medical_orders.id"),
        nullable=False,
    )

    sample_id = db.Column(
        db.String(36),
        db.ForeignKey("medical_samples.id"),
    )

    incident_type = db.Column(db.String(100), nullable=False)

    severity = db.Column(db.String(50), default="MEDIUM")

    status = db.Column(db.String(50), default="OPEN")

    description = db.Column(db.Text, nullable=False)

    resolution_note = db.Column(db.Text)

    reported_by = db.Column(db.String(255), default="SYSTEM")

    resolved_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "medical_order_id": self.medical_order_id,
            "sample_id": self.sample_id,
            "incident_type": self.incident_type,
            "severity": self.severity,
            "status": self.status,
            "description": self.description,
            "resolution_note": self.resolution_note,
            "reported_by": self.reported_by,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
