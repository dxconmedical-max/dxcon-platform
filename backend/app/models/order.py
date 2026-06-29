from app.extensions.db import db
from datetime import datetime
import uuid


class Order(db.Model):

    __tablename__ = "orders"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    order_code = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    patient_id = db.Column(
        db.String(36),
        nullable=False
    )

    laboratory_id = db.Column(
        db.String(36)
    )

    company_id = db.Column(
        db.String(36)
    )

    contract_id = db.Column(
        db.String(36)
    )

    marketplace_booking_id = db.Column(
        db.String(36),
        db.ForeignKey("marketplace_bookings.id"),
        unique=True,
        nullable=True,
    )

    status = db.Column(
        db.String(50),
        default="PENDING"
    )

    total_amount = db.Column(
        db.Float,
        default=0
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "order_code": self.order_code,
            "patient_id": self.patient_id,
            "laboratory_id": self.laboratory_id,
            "company_id": self.company_id,
            "contract_id": self.contract_id,
            "marketplace_booking_id": self.marketplace_booking_id,
            "status": self.status,
            "total_amount": self.total_amount,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
