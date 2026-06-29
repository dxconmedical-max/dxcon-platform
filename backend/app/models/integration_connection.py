from datetime import datetime
import uuid

from app.extensions.db import db


class IntegrationConnection(db.Model):

    __tablename__ = "integration_connections"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    connection_code = db.Column(db.String(50), unique=True, nullable=False)

    partner_id = db.Column(
        db.String(36),
        db.ForeignKey("integration_partners.id"),
        nullable=False,
    )

    protocol = db.Column(db.String(50), default="HL7_FHIR")

    auth_type = db.Column(db.String(50), default="API_KEY")

    config_json = db.Column(db.Text, default="{}")

    status = db.Column(db.String(20), default="ACTIVE")

    last_sync_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    partner = db.relationship("IntegrationPartner")

    def to_dict(self):
        return {
            "id": self.id,
            "connection_code": self.connection_code,
            "partner_id": self.partner_id,
            "protocol": self.protocol,
            "auth_type": self.auth_type,
            "config_json": self.config_json,
            "status": self.status,
            "last_sync_at": self.last_sync_at.isoformat() if self.last_sync_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "partner": self.partner.to_dict() if self.partner else None,
        }
