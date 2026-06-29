from datetime import datetime
import uuid

from app.extensions.db import db


class CollectorHandover(db.Model):

    __tablename__ = "collector_handovers"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    collector_id = db.Column(db.String(36), db.ForeignKey("drivers.id"), nullable=False)

    handover_type = db.Column(db.String(50), nullable=False)

    object_code = db.Column(db.String(100), nullable=False)

    qr_payload = db.Column(db.String(255))

    booking_id = db.Column(db.String(36), db.ForeignKey("marketplace_bookings.id"))

    sample_tracking_id = db.Column(db.String(36))

    transport_box_id = db.Column(db.String(36))

    shipment_id = db.Column(db.String(36))

    recipient_name = db.Column(db.String(255))

    latitude = db.Column(db.String(50))

    longitude = db.Column(db.String(50))

    note = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "collector_id": self.collector_id,
            "handover_type": self.handover_type,
            "object_code": self.object_code,
            "qr_payload": self.qr_payload,
            "booking_id": self.booking_id,
            "sample_tracking_id": self.sample_tracking_id,
            "transport_box_id": self.transport_box_id,
            "shipment_id": self.shipment_id,
            "recipient_name": self.recipient_name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "note": self.note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
