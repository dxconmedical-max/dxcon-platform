from datetime import datetime
import uuid

from app.extensions.db import db


class LISOrderMessage(db.Model):

    __tablename__ = "lis_order_messages"

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

    external_order_id = db.Column(db.String(100), nullable=False)

    patient_code = db.Column(db.String(100))

    test_codes_json = db.Column(db.Text, default="[]")

    status = db.Column(db.String(50), default="PENDING")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "message_id": self.message_id,
            "external_order_id": self.external_order_id,
            "patient_code": self.patient_code,
            "test_codes_json": self.test_codes_json,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
