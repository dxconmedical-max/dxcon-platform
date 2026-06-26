from app.extensions.db import db
from datetime import datetime
import uuid


class ShipmentItem(db.Model):
    __tablename__ = "shipment_items"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    shipment_id = db.Column(db.String(36), nullable=False)
    order_id = db.Column(db.String(36))
    order_item_id = db.Column(db.String(36))
    sample_tracking_id = db.Column(db.String(36))

    sample_code = db.Column(db.String(100))
    tube_type = db.Column(db.String(100))
    test_name = db.Column(db.String(255))

    status = db.Column(db.String(50), default="CREATED")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def qr_payload(self):
        return f"DXCON:SAMPLE:{self.sample_code or self.id}"

    def to_dict(self):
        return {
            "id": self.id,
            "shipment_id": self.shipment_id,
            "order_id": self.order_id,
            "order_item_id": self.order_item_id,
            "sample_tracking_id": self.sample_tracking_id,
            "sample_code": self.sample_code,
            "tube_type": self.tube_type,
            "test_name": self.test_name,
            "status": self.status,
            "qr_payload": self.qr_payload(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
