from datetime import datetime
import uuid

from app.extensions.db import db


class GPSPing(db.Model):
    __tablename__ = "logistics_gps_pings"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    driver_profile_id = db.Column(
        db.String(36), db.ForeignKey("logistics_driver_profiles.id")
    )
    vehicle_id = db.Column(db.String(36), db.ForeignKey("logistics_vehicles.id"))
    route_plan_id = db.Column(db.String(36), db.ForeignKey("logistics_route_plans.id"))
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    speed = db.Column(db.Float, default=0)
    heading = db.Column(db.Float, default=0)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "driver_profile_id": self.driver_profile_id,
            "vehicle_id": self.vehicle_id,
            "route_plan_id": self.route_plan_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "speed": self.speed,
            "heading": self.heading,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DeliveryProof(db.Model):
    __tablename__ = "logistics_delivery_proofs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assignment_id = db.Column(
        db.String(36), db.ForeignKey("logistics_dispatch_assignments.id")
    )
    route_stop_id = db.Column(db.String(36), db.ForeignKey("logistics_route_stops.id"))
    proof_type = db.Column(db.String(50), default="SIGNATURE")
    proof_url = db.Column(db.String(500))
    recipient_name = db.Column(db.String(255))
    captured_by = db.Column(db.String(255))
    captured_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "assignment_id": self.assignment_id,
            "route_stop_id": self.route_stop_id,
            "proof_type": self.proof_type,
            "proof_url": self.proof_url,
            "recipient_name": self.recipient_name,
            "captured_by": self.captured_by,
            "captured_at": self.captured_at.isoformat() if self.captured_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ChainOfCustodyEvent(db.Model):
    __tablename__ = "logistics_chain_of_custody_events"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_code = db.Column(db.String(50), unique=True, nullable=False)
    event_type = db.Column(db.String(50), nullable=False)
    reference_type = db.Column(db.String(50))
    reference_id = db.Column(db.String(36))
    actor = db.Column(db.String(255), default="SYSTEM")
    location = db.Column(db.String(255))
    metadata_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "event_code": self.event_code,
            "event_type": self.event_type,
            "reference_type": self.reference_type,
            "reference_id": self.reference_id,
            "actor": self.actor,
            "location": self.location,
            "metadata_json": self.metadata_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
