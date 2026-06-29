from app.extensions.db import db
from datetime import datetime
import uuid

class Driver(db.Model):

    __tablename__ = "drivers"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    driver_code = db.Column(db.String(50), unique=True, nullable=False)

    full_name = db.Column(db.String(255), nullable=False)

    phone = db.Column(db.String(30))

    vehicle_no = db.Column(db.String(50))

    email = db.Column(db.String(255))

    license_number = db.Column(db.String(100))

    home_city = db.Column(db.String(100))

    active_vehicle_id = db.Column(db.String(36))

    ops_status = db.Column(db.String(50), default="ACTIVE")

    status = db.Column(db.String(50), default="ACTIVE")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "driver_code": self.driver_code,
            "full_name": self.full_name,
            "phone": self.phone,
            "email": self.email,
            "vehicle_no": self.vehicle_no,
            "license_number": self.license_number,
            "home_city": self.home_city,
            "active_vehicle_id": self.active_vehicle_id,
            "ops_status": self.ops_status,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
