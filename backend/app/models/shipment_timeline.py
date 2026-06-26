from app.extensions.db import db
from datetime import datetime
import uuid


class ShipmentTimeline(db.Model):
    __tablename__ = "shipment_timelines"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    shipment_id = db.Column(db.String(36), nullable=False)
    event_type = db.Column(db.String(100), nullable=False)
    note = db.Column(db.Text)
    actor = db.Column(db.String(255))
    gps_location = db.Column(db.String(255))
    temperature = db.Column(db.String(50))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "shipment_id": self.shipment_id,
            "event_type": self.event_type,
            "note": self.note,
            "actor": self.actor,
            "gps_location": self.gps_location,
            "temperature": self.temperature,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
