from datetime import datetime
import uuid

from app.extensions.db import db


class LISResultMessage(db.Model):

    __tablename__ = "lis_result_messages"

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

    result_code = db.Column(db.String(100))

    result_value = db.Column(db.String(255))

    status = db.Column(db.String(50), default="PENDING")

    released_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "message_id": self.message_id,
            "external_order_id": self.external_order_id,
            "result_code": self.result_code,
            "result_value": self.result_value,
            "status": self.status,
            "released_at": self.released_at.isoformat() if self.released_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
