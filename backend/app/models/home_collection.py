from app.extensions.db import db
from datetime import datetime
import uuid


class HomeCollection(db.Model):

    __tablename__ = "home_collections"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    patient_id = db.Column(
        db.String(36),
        nullable=False
    )

    collector_id = db.Column(
        db.String(36)
    )

    address = db.Column(
        db.Text
    )

    scheduled_time = db.Column(
        db.String(100)
    )

    status = db.Column(
        db.String(50),
        default="REQUESTED"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "collector_id": self.collector_id,
            "address": self.address,
            "scheduled_time": self.scheduled_time,
            "status": self.status
        }
