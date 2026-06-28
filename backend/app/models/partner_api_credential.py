from datetime import datetime
import uuid

from app.extensions.db import db


class PartnerApiCredential(db.Model):

    __tablename__ = "partner_api_credentials"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    partner_id = db.Column(
        db.String(36),
        db.ForeignKey("partners.id"),
        nullable=False,
    )

    client_id = db.Column(
        db.String(100),
        unique=True,
        nullable=False,
    )

    client_secret_hash = db.Column(
        db.String(255),
        nullable=False,
    )

    api_key_hash = db.Column(
        db.String(255),
        nullable=False,
    )

    status = db.Column(
        db.String(50),
        default="ACTIVE",
        nullable=False,
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
    )

    revoked_at = db.Column(
        db.DateTime,
    )

    partner = db.relationship(
        "Partner",
        backref=db.backref(
            "api_credentials",
            lazy=True,
            cascade="all, delete-orphan",
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "partner_id": self.partner_id,
            "client_id": self.client_id,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
        }
