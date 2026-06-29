from datetime import datetime
import uuid

from app.extensions.db import db


class RoutePlan(db.Model):
    __tablename__ = "logistics_route_plans"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    route_code = db.Column(db.String(50), unique=True, nullable=False)
    driver_profile_id = db.Column(
        db.String(36), db.ForeignKey("logistics_driver_profiles.id")
    )
    vehicle_id = db.Column(db.String(36), db.ForeignKey("logistics_vehicles.id"))
    status = db.Column(db.String(50), default="DRAFT")
    total_stops = db.Column(db.Integer, default=0)
    total_distance_km = db.Column(db.Float, default=0)
    estimated_minutes = db.Column(db.Integer, default=0)
    start_latitude = db.Column(db.Float)
    start_longitude = db.Column(db.Float)
    optimized_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "route_code": self.route_code,
            "driver_profile_id": self.driver_profile_id,
            "vehicle_id": self.vehicle_id,
            "status": self.status,
            "total_stops": self.total_stops,
            "total_distance_km": self.total_distance_km,
            "estimated_minutes": self.estimated_minutes,
            "start_latitude": self.start_latitude,
            "start_longitude": self.start_longitude,
            "optimized_at": self.optimized_at.isoformat() if self.optimized_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class RouteStop(db.Model):
    __tablename__ = "logistics_route_stops"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    route_plan_id = db.Column(
        db.String(36), db.ForeignKey("logistics_route_plans.id"), nullable=False
    )
    stop_sequence = db.Column(db.Integer, default=0)
    address = db.Column(db.String(500))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    status = db.Column(db.String(50), default="PENDING")
    reference_type = db.Column(db.String(50))
    reference_id = db.Column(db.String(36))
    eta_minutes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "route_plan_id": self.route_plan_id,
            "stop_sequence": self.stop_sequence,
            "address": self.address,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "status": self.status,
            "reference_type": self.reference_type,
            "reference_id": self.reference_id,
            "eta_minutes": self.eta_minutes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DispatchAssignment(db.Model):
    __tablename__ = "logistics_dispatch_assignments"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assignment_code = db.Column(db.String(50), unique=True, nullable=False)
    driver_profile_id = db.Column(
        db.String(36), db.ForeignKey("logistics_driver_profiles.id")
    )
    vehicle_id = db.Column(db.String(36), db.ForeignKey("logistics_vehicles.id"))
    route_plan_id = db.Column(db.String(36), db.ForeignKey("logistics_route_plans.id"))
    status = db.Column(db.String(50), default="PENDING")
    priority = db.Column(db.String(20), default="NORMAL")
    reference_type = db.Column(db.String(50))
    reference_id = db.Column(db.String(36))
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "assignment_code": self.assignment_code,
            "driver_profile_id": self.driver_profile_id,
            "vehicle_id": self.vehicle_id,
            "route_plan_id": self.route_plan_id,
            "status": self.status,
            "priority": self.priority,
            "reference_type": self.reference_type,
            "reference_id": self.reference_id,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ETAEstimate(db.Model):
    __tablename__ = "logistics_eta_estimates"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    route_plan_id = db.Column(
        db.String(36), db.ForeignKey("logistics_route_plans.id"), nullable=False
    )
    route_stop_id = db.Column(db.String(36), db.ForeignKey("logistics_route_stops.id"))
    estimated_arrival = db.Column(db.DateTime)
    estimated_minutes = db.Column(db.Integer, default=0)
    confidence = db.Column(db.Float, default=0.9)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "route_plan_id": self.route_plan_id,
            "route_stop_id": self.route_stop_id,
            "estimated_arrival": (
                self.estimated_arrival.isoformat() if self.estimated_arrival else None
            ),
            "estimated_minutes": self.estimated_minutes,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
