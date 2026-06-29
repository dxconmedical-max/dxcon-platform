from datetime import datetime
import uuid

from app.extensions.db import db


class PartnerBranch(db.Model):

    __tablename__ = "partner_branches"

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

    branch_code = db.Column(
        db.String(50),
        nullable=False,
    )

    branch_name = db.Column(
        db.String(255),
        nullable=False,
    )

    address = db.Column(
        db.Text,
    )

    city = db.Column(
        db.String(100),
    )

    district = db.Column(
        db.String(100),
    )

    phone = db.Column(
        db.String(30),
    )

    email = db.Column(
        db.String(255),
    )

    is_primary = db.Column(
        db.Boolean,
        default=False,
    )

    status = db.Column(
        db.String(50),
        default="ACTIVE",
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

    def to_dict(self):
        return {
            "id": self.id,
            "partner_id": self.partner_id,
            "branch_code": self.branch_code,
            "branch_name": self.branch_name,
            "address": self.address,
            "city": self.city,
            "district": self.district,
            "phone": self.phone,
            "email": self.email,
            "is_primary": self.is_primary,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
