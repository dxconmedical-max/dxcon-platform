from datetime import datetime
import uuid

from app.extensions.db import db


class PartnerOperatingHour(db.Model):

    __tablename__ = "partner_operating_hours"

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

    day_of_week = db.Column(
        db.Integer,
        nullable=False,
    )

    open_time = db.Column(
        db.String(10),
    )

    close_time = db.Column(
        db.String(10),
    )

    is_closed = db.Column(
        db.Boolean,
        default=False,
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
            "day_of_week": self.day_of_week,
            "open_time": self.open_time,
            "close_time": self.close_time,
            "is_closed": self.is_closed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
