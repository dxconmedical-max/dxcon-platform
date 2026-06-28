from datetime import datetime
import uuid

from app.extensions.db import db


class CollectorAvailability(db.Model):

    __tablename__ = "collector_availabilities"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    collector_id = db.Column(
        db.String(36),
        nullable=False,
    )

    date = db.Column(
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

    district = db.Column(
        db.String(100),
    )

    city = db.Column(
        db.String(100),
    )

    status = db.Column(
        db.String(50),
        default="AVAILABLE",
        nullable=False,
    )

    max_jobs = db.Column(
        db.Integer,
        default=8,
        nullable=False,
    )

    assigned_jobs = db.Column(
        db.Integer,
        default=0,
        nullable=False,
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    __table_args__ = (
        db.UniqueConstraint(
            "collector_id",
            "date",
            "start_time",
            "end_time",
            name="uq_collector_availability_window",
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "collector_id": self.collector_id,
            "date": self.date,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "district": self.district,
            "city": self.city,
            "status": self.status,
            "max_jobs": self.max_jobs,
            "assigned_jobs": self.assigned_jobs,
            "remaining_jobs": max(0, self.max_jobs - self.assigned_jobs),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
