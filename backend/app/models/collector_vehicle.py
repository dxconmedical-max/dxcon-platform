from datetime import datetime
import uuid

from app.extensions.db import db


class CollectorVehicle(db.Model):

    __tablename__ = "collector_vehicles"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    vehicle_code = db.Column(db.String(50), unique=True, nullable=False)

    collector_id = db.Column(db.String(36), db.ForeignKey("drivers.id"), nullable=False)

    plate_number = db.Column(db.String(50), nullable=False)

    vehicle_type = db.Column(db.String(50), default="MOTORBIKE")

    brand = db.Column(db.String(100))

    model = db.Column(db.String(100))

    capacity_boxes = db.Column(db.Integer, default=1)

    status = db.Column(db.String(50), default="ACTIVE")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "vehicle_code": self.vehicle_code,
            "collector_id": self.collector_id,
            "plate_number": self.plate_number,
            "vehicle_type": self.vehicle_type,
            "brand": self.brand,
            "model": self.model,
            "capacity_boxes": self.capacity_boxes,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
