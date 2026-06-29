from datetime import datetime
import uuid

from app.extensions.db import db


class PartnerCoverageArea(db.Model):

    __tablename__ = "partner_coverage_areas"

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

    branch_id = db.Column(
        db.String(36),
        db.ForeignKey("partner_branches.id"),
    )

    area_name = db.Column(
        db.String(255),
    )

    city = db.Column(
        db.String(100),
    )

    district = db.Column(
        db.String(100),
    )

    radius_km = db.Column(
        db.Float,
    )

    latitude = db.Column(
        db.Float,
    )

    longitude = db.Column(
        db.Float,
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "partner_id": self.partner_id,
            "branch_id": self.branch_id,
            "area_name": self.area_name,
            "city": self.city,
            "district": self.district,
            "radius_km": self.radius_km,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
