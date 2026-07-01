from datetime import datetime
import uuid

from app.extensions.db import db


class DriverProfile(db.Model):
    __tablename__ = "logistics_driver_profiles"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_code = db.Column(db.String(50), unique=True, nullable=False)
    driver_id = db.Column(db.String(36), db.ForeignKey("drivers.id"))
    full_name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(30))
    email = db.Column(db.String(255))
    license_number = db.Column(db.String(100))
    hub_city = db.Column(db.String(100))
    status = db.Column(db.String(50), default="ACTIVE")
    rating = db.Column(db.Float, default=5.0)
    active_vehicle_id = db.Column(db.String(36))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "profile_code": self.profile_code,
            "driver_id": self.driver_id,
            "full_name": self.full_name,
            "phone": self.phone,
            "email": self.email,
            "license_number": self.license_number,
            "hub_city": self.hub_city,
            "status": self.status,
            "rating": self.rating,
            "active_vehicle_id": self.active_vehicle_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Vehicle(db.Model):
    __tablename__ = "logistics_vehicles"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    vehicle_code = db.Column(db.String(50), unique=True, nullable=False)
    plate_number = db.Column(db.String(50), nullable=False)
    vehicle_type = db.Column(db.String(50), default="VAN")
    capacity = db.Column(db.Integer, default=20)
    status = db.Column(db.String(50), default="AVAILABLE")
    current_driver_profile_id = db.Column(
        db.String(36), db.ForeignKey("logistics_driver_profiles.id")
    )
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "vehicle_code": self.vehicle_code,
            "plate_number": self.plate_number,
            "vehicle_type": self.vehicle_type,
            "capacity": self.capacity,
            "status": self.status,
            "current_driver_profile_id": self.current_driver_profile_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
