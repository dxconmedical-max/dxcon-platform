from datetime import datetime
import uuid

from app.extensions.db import db


class IntegrationMessage(db.Model):

    __tablename__ = "integration_messages"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    message_code = db.Column(db.String(50), unique=True, nullable=False)

    connection_id = db.Column(
        db.String(36),
        db.ForeignKey("integration_connections.id"),
        nullable=False,
    )

    message_type = db.Column(db.String(50), nullable=False)

    direction = db.Column(db.String(20), default="INBOUND")

    payload_json = db.Column(db.Text, default="{}")

    status = db.Column(db.String(50), default="RECEIVED")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    processed_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "message_code": self.message_code,
            "connection_id": self.connection_id,
            "message_type": self.message_type,
            "direction": self.direction,
            "payload_json": self.payload_json,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
        }
