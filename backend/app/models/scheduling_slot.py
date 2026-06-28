from datetime import datetime
import uuid

from app.extensions.db import db


class SchedulingSlot(db.Model):

    __tablename__ = "scheduling_slots"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    calendar_id = db.Column(
        db.String(36),
        db.ForeignKey("scheduling_calendars.id"),
        nullable=False,
    )

    slot_date = db.Column(
        db.String(20),
        nullable=False,
    )

    start_time = db.Column(
        db.String(10),
        nullable=False,
    )

    end_time = db.Column(
        db.String(10),
        nullable=False,
    )

    slot_type = db.Column(
        db.String(50),
        default="COLLECTION",
        nullable=False,
    )

    capacity = db.Column(
        db.Integer,
        default=1,
        nullable=False,
    )

    booked_count = db.Column(
        db.Integer,
        default=0,
        nullable=False,
    )

    status = db.Column(
        db.String(50),
        default="AVAILABLE",
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

    __table_args__ = (
        db.UniqueConstraint(
            "calendar_id",
            "slot_date",
            "start_time",
            "end_time",
            "slot_type",
            name="uq_scheduling_slot_window",
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "calendar_id": self.calendar_id,
            "slot_date": self.slot_date,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "slot_type": self.slot_type,
            "capacity": self.capacity,
            "booked_count": self.booked_count,
            "remaining_capacity": max(0, self.capacity - self.booked_count),
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
