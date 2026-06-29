from datetime import datetime
import uuid

from app.extensions.db import db


class Sample(db.Model):

    __tablename__ = "medical_samples"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    sample_code = db.Column(db.String(50), unique=True, nullable=False)

    medical_order_id = db.Column(
        db.String(36),
        db.ForeignKey("medical_orders.id"),
        nullable=False,
    )

    sample_type = db.Column(db.String(100))

    barcode_value = db.Column(db.String(100), unique=True)

    qr_payload = db.Column(db.String(255))

    status = db.Column(db.String(50), default="CREATED")

    collected_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "sample_code": self.sample_code,
            "medical_order_id": self.medical_order_id,
            "sample_type": self.sample_type,
            "barcode_value": self.barcode_value,
            "qr_payload": self.qr_payload,
            "status": self.status,
            "collected_at": self.collected_at.isoformat() if self.collected_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
