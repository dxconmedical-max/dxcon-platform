from datetime import datetime
import uuid

from app.extensions.db import db


class MedicalOrderEvent(db.Model):

    __tablename__ = "medical_order_events"

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

    event_type = db.Column(db.String(100), nullable=False)

    from_status = db.Column(db.String(50))

    to_status = db.Column(db.String(50))

    message = db.Column(db.Text)

    actor_email = db.Column(db.String(255), default="SYSTEM")

    metadata_json = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "medical_order_id": self.medical_order_id,
            "event_type": self.event_type,
            "from_status": self.from_status,
            "to_status": self.to_status,
            "message": self.message,
            "actor_email": self.actor_email,
            "metadata_json": self.metadata_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
