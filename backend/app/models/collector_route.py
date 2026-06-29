from datetime import datetime
import uuid

from app.extensions.db import db


class CollectorRoute(db.Model):

    __tablename__ = "collector_routes"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    route_code = db.Column(db.String(50), unique=True, nullable=False)

    collector_id = db.Column(db.String(36), db.ForeignKey("drivers.id"), nullable=False)

    vehicle_id = db.Column(db.String(36), db.ForeignKey("collector_vehicles.id"))

    transport_box_id = db.Column(db.String(36))

    status = db.Column(db.String(50), default="PLANNED")

    total_stops = db.Column(db.Integer, default=0)

    completed_stops = db.Column(db.Integer, default=0)

    total_distance_km = db.Column(db.Float, default=0)

    estimated_minutes = db.Column(db.Integer, default=0)

    route_score = db.Column(db.Float, default=100)

    start_latitude = db.Column(db.String(50))

    start_longitude = db.Column(db.String(50))

    optimized_at = db.Column(db.DateTime)

    started_at = db.Column(db.DateTime)

    completed_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "route_code": self.route_code,
            "collector_id": self.collector_id,
            "vehicle_id": self.vehicle_id,
            "transport_box_id": self.transport_box_id,
            "status": self.status,
            "total_stops": self.total_stops,
            "completed_stops": self.completed_stops,
            "total_distance_km": self.total_distance_km,
            "estimated_minutes": self.estimated_minutes,
            "route_score": self.route_score,
            "start_latitude": self.start_latitude,
            "start_longitude": self.start_longitude,
            "optimized_at": self.optimized_at.isoformat() if self.optimized_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
