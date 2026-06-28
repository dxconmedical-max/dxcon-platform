from datetime import datetime
import uuid

from app.extensions.db import db


class PartnerServiceMapping(db.Model):

    __tablename__ = "partner_service_mappings"

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

    diagnostic_service_id = db.Column(
        db.String(36),
        db.ForeignKey("diagnostic_services.id"),
        nullable=False,
    )

    partner_service_code = db.Column(
        db.String(50),
        nullable=False,
    )

    partner_service_name = db.Column(
        db.String(255),
        nullable=False,
    )

    price = db.Column(
        db.Float,
        nullable=False,
    )

    currency = db.Column(
        db.String(10),
        default="VND",
    )

    turnaround_hours = db.Column(
        db.Float,
    )

    home_collection_available = db.Column(
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

    partner = db.relationship(
        "Partner",
        backref=db.backref("service_mappings", lazy=True),
    )

    diagnostic_service = db.relationship(
        "DiagnosticService",
        backref=db.backref("partner_mappings", lazy=True),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "partner_id": self.partner_id,
            "diagnostic_service_id": self.diagnostic_service_id,
            "partner_service_code": self.partner_service_code,
            "partner_service_name": self.partner_service_name,
            "price": self.price,
            "currency": self.currency,
            "turnaround_hours": self.turnaround_hours,
            "home_collection_available": self.home_collection_available,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
