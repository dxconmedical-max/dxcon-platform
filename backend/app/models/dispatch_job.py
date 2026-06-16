from app.extensions.db import db
from datetime import datetime
import uuid


class DispatchJob(db.Model):

    __tablename__ = "dispatch_jobs"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    job_code = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    driver_id = db.Column(db.String(36))

    transport_box_id = db.Column(db.String(36))

    status = db.Column(
        db.String(50),
        default="PLANNED"
    )

    start_latitude = db.Column(db.String(50))
    start_longitude = db.Column(db.String(50))

    destination_latitude = db.Column(db.String(50))
    destination_longitude = db.Column(db.String(50))

    total_distance_km = db.Column(
        db.Float,
        default=0
    )

    estimated_minutes = db.Column(
        db.Integer,
        default=0
    )

    priority = db.Column(
        db.String(30),
        default="NORMAL"
    )

    estimated_arrival = db.Column(db.String(100))

    actual_arrival = db.Column(db.String(100))

    delay_minutes = db.Column(
        db.Integer,
        default=0
    )

    route_score = db.Column(
        db.Float,
        default=100
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "job_code": self.job_code,
            "driver_id": self.driver_id,
            "transport_box_id": self.transport_box_id,
            "status": self.status,
            "start_latitude": self.start_latitude,
            "start_longitude": self.start_longitude,
            "destination_latitude": self.destination_latitude,
            "destination_longitude": self.destination_longitude,
            "total_distance_km": self.total_distance_km,
            "estimated_minutes": self.estimated_minutes,
            "priority": self.priority,
            "estimated_arrival": self.estimated_arrival,
            "actual_arrival": self.actual_arrival,
            "delay_minutes": self.delay_minutes,
            "route_score": self.route_score
        }
