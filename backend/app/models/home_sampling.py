from app.extensions.db import db
from datetime import datetime
import uuid


class HomeSampling(db.Model):

    __tablename__ = "home_sampling_requests"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    patient_id = db.Column(
        db.String(36),
        nullable=False
    )

    address = db.Column(
        db.Text
    )

    preferred_time = db.Column(
        db.String(255)
    )

    status = db.Column(
        db.String(50),
        default="PENDING"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "address": self.address,
            "preferred_time": self.preferred_time,
            "status": self.status
        }
