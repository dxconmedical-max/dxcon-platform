from app.extensions.db import db
import uuid


class Driver(db.Model):

    __tablename__ = "drivers"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    full_name = db.Column(
        db.String(255)
    )

    phone = db.Column(
        db.String(30)
    )

    vehicle_number = db.Column(
        db.String(50)
    )

    is_active = db.Column(
        db.Boolean,
        default=True
    )

    def to_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "phone": self.phone,
            "vehicle_number": self.vehicle_number,
            "is_active": self.is_active
        }
