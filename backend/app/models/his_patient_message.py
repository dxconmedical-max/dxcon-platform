from datetime import datetime
import uuid

from app.extensions.db import db


class HISPatientMessage(db.Model):

    __tablename__ = "his_patient_messages"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    message_id = db.Column(
        db.String(36),
        db.ForeignKey("integration_messages.id"),
        nullable=False,
    )

    external_patient_id = db.Column(db.String(100), nullable=False)

    full_name = db.Column(db.String(255))

    phone = db.Column(db.String(30))

    date_of_birth = db.Column(db.String(20))

    status = db.Column(db.String(50), default="PENDING")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "message_id": self.message_id,
            "external_patient_id": self.external_patient_id,
            "full_name": self.full_name,
            "phone": self.phone,
            "date_of_birth": self.date_of_birth,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
