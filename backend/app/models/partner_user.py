from datetime import datetime
import uuid

from app.extensions.db import db


class PartnerUser(db.Model):

    __tablename__ = "partner_users"

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

    user_id = db.Column(
        db.String(36),
    )

    email = db.Column(
        db.String(255),
    )

    role = db.Column(
        db.String(50),
        nullable=False,
    )

    status = db.Column(
        db.String(50),
        default="INVITED",
        nullable=False,
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    partner = db.relationship(
        "Partner",
        backref=db.backref("users", lazy=True, cascade="all, delete-orphan"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "partner_id": self.partner_id,
            "user_id": self.user_id,
            "email": self.email,
            "role": self.role,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
