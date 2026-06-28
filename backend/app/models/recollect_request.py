from datetime import datetime
import uuid

from app.extensions.db import db


class RecollectRequest(db.Model):

    __tablename__ = "recollect_requests"

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

    reason = db.Column(db.Text, nullable=False)

    status = db.Column(db.String(50), default="PENDING")

    requested_by = db.Column(db.String(255), default="SYSTEM")

    scheduled_date = db.Column(db.String(20))

    completed_at = db.Column(db.DateTime)

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
            "reason": self.reason,
            "status": self.status,
            "requested_by": self.requested_by,
            "scheduled_date": self.scheduled_date,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
