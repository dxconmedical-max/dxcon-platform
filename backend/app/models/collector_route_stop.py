from datetime import datetime
import uuid

from app.extensions.db import db


class CollectorRouteStop(db.Model):

    __tablename__ = "collector_route_stops"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    route_id = db.Column(
        db.String(36),
        db.ForeignKey("collector_routes.id"),
        nullable=False,
    )

    booking_id = db.Column(db.String(36), db.ForeignKey("marketplace_bookings.id"))

    assignment_id = db.Column(db.String(36), db.ForeignKey("booking_assignments.id"))

    sequence_no = db.Column(db.Integer, default=1)

    patient_name = db.Column(db.String(255))

    address = db.Column(db.Text)

    latitude = db.Column(db.String(50))

    longitude = db.Column(db.String(50))

    status = db.Column(db.String(50), default="PENDING")

    estimated_arrival = db.Column(db.String(20))

    arrived_at = db.Column(db.DateTime)

    completed_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "route_id": self.route_id,
            "booking_id": self.booking_id,
            "assignment_id": self.assignment_id,
            "sequence_no": self.sequence_no,
            "patient_name": self.patient_name,
            "address": self.address,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "status": self.status,
            "estimated_arrival": self.estimated_arrival,
            "arrived_at": self.arrived_at.isoformat() if self.arrived_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
