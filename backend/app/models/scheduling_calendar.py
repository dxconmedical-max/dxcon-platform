from datetime import datetime
import uuid

from app.extensions.db import db


class SchedulingCalendar(db.Model):

    __tablename__ = "scheduling_calendars"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    owner_type = db.Column(
        db.String(50),
        nullable=False,
    )

    owner_id = db.Column(
        db.String(36),
        nullable=False,
    )

    name = db.Column(
        db.String(255),
        nullable=False,
    )

    timezone = db.Column(
        db.String(50),
        default="Asia/Ho_Chi_Minh",
    )

    is_active = db.Column(
        db.Boolean,
        default=True,
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

    slots = db.relationship(
        "SchedulingSlot",
        backref="calendar",
        lazy=True,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        db.UniqueConstraint(
            "owner_type",
            "owner_id",
            name="uq_scheduling_calendar_owner",
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "owner_type": self.owner_type,
            "owner_id": self.owner_id,
            "name": self.name,
            "timezone": self.timezone,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
