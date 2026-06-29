from datetime import datetime
import uuid

from app.extensions.db import db


class IntegrationPartner(db.Model):

    __tablename__ = "integration_partners"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    partner_code = db.Column(db.String(50), unique=True, nullable=False)

    partner_name = db.Column(db.String(255), nullable=False)

    integration_type = db.Column(db.String(50), nullable=False)

    endpoint_url = db.Column(db.String(500))

    status = db.Column(db.String(20), default="ACTIVE")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "partner_code": self.partner_code,
            "partner_name": self.partner_name,
            "integration_type": self.integration_type,
            "endpoint_url": self.endpoint_url,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
