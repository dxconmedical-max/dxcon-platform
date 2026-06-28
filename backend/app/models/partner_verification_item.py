from datetime import datetime
import uuid

from app.extensions.db import db


class PartnerVerificationItem(db.Model):

    __tablename__ = "partner_verification_items"

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

    item_type = db.Column(
        db.String(50),
        nullable=False,
    )

    status = db.Column(
        db.String(50),
        default="MISSING",
        nullable=False,
    )

    note = db.Column(
        db.Text,
    )

    verified_by = db.Column(
        db.String(255),
    )

    verified_at = db.Column(
        db.DateTime,
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
        backref=db.backref(
            "verification_items",
            lazy=True,
            cascade="all, delete-orphan",
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "partner_id": self.partner_id,
            "item_type": self.item_type,
            "status": self.status,
            "note": self.note,
            "verified_by": self.verified_by,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
