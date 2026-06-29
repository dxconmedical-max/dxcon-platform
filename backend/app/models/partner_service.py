from datetime import datetime
import uuid

from app.extensions.db import db


class PartnerService(db.Model):

    __tablename__ = "partner_services"

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

    service_code = db.Column(
        db.String(50),
        nullable=False,
    )

    service_name = db.Column(
        db.String(255),
        nullable=False,
    )

    catalog_item_code = db.Column(
        db.String(50),
    )

    description = db.Column(
        db.Text,
    )

    status = db.Column(
        db.String(50),
        default="ACTIVE",
    )

    average_result_time_hours = db.Column(
        db.Float,
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
            "service_code": self.service_code,
            "service_name": self.service_name,
            "catalog_item_code": self.catalog_item_code,
            "description": self.description,
            "status": self.status,
            "average_result_time_hours": self.average_result_time_hours,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
