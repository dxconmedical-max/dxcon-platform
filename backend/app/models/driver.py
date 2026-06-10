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

    status = db.Column(db.String(50), default="ACTIVE")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "driver_code": self.driver_code,
            "full_name": self.full_name,
            "phone": self.phone,
            "vehicle_no": self.vehicle_no,
            "status": self.status
        }
