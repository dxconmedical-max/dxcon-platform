from app.extensions.db import db
from datetime import datetime
import uuid


class Shipment(db.Model):

    __tablename__ = "shipments"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    shipment_code = db.Column(db.String(100), unique=True, nullable=False)

    collector_id = db.Column(db.String(36))
    transport_box_id = db.Column(db.String(36))
    lab_name = db.Column(db.String(255))

    status = db.Column(db.String(50), default="CREATED")

    sample_count = db.Column(db.Integer, default=0)
    temperature = db.Column(db.String(50))
    gps_location = db.Column(db.String(255))

    departed_at = db.Column(db.DateTime)
    arrived_at = db.Column(db.DateTime)
    received_at = db.Column(db.DateTime)

    received_by = db.Column(db.String(255))
    receiver_note = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def qr_payload(self):
        return f"DXCON:SHIPMENT:{self.shipment_code}"

    def to_dict(self):
        return {
            "id": self.id,
            "shipment_code": self.shipment_code,
            "qr_payload": self.qr_payload(),
            "collector_id": self.collector_id,
            "transport_box_id": self.transport_box_id,
            "lab_name": self.lab_name,
            "status": self.status,
            "sample_count": self.sample_count,
            "temperature": self.temperature,
            "gps_location": self.gps_location,
            "departed_at": self.departed_at.isoformat() if self.departed_at else None,
            "arrived_at": self.arrived_at.isoformat() if self.arrived_at else None,
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "received_by": self.received_by,
            "receiver_note": self.receiver_note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
