from app.extensions.db import db
from datetime import datetime
import uuid


class SampleCollection(db.Model):

    __tablename__ = "sample_collections"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    order_id = db.Column(
        db.String(36),
        nullable=False
    )

    marketplace_booking_id = db.Column(
        db.String(36),
        db.ForeignKey("marketplace_bookings.id"),
    )

    collector_id = db.Column(
        db.String(36),
    )

    sample_tracking_id = db.Column(
        db.String(36),
    )

    collector_name = db.Column(
        db.String(255)
    )

    status = db.Column(
        db.String(50),
        default="PENDING"
    )

    collected_at = db.Column(
        db.DateTime
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # Production Sample Collection fields
    specimen_type = db.Column(db.String(100))
    barcode_value = db.Column(db.String(100))
    expected_barcode = db.Column(db.String(100))
    collection_location = db.Column(db.String(255))
    location_city = db.Column(db.String(100))
    notes = db.Column(db.Text)
    quality_status = db.Column(db.String(50))
    rejection_reason = db.Column(db.Text)
    partner_id = db.Column(db.String(36))
    recollect_of_id = db.Column(db.String(36))
    patient_verified = db.Column(db.Boolean, default=False)
    order_verified = db.Column(db.Boolean, default=False)

    picked_up_at = db.Column(db.DateTime)
    dispatched_at = db.Column(db.DateTime)
    handoff_at = db.Column(db.DateTime)
    arrived_at_lab = db.Column(db.DateTime)

    vehicle_id = db.Column(db.String(36))
    driver_id = db.Column(db.String(36))
    transport_box_id = db.Column(db.String(36))
    distance_km = db.Column(db.Float)
    eta_minutes = db.Column(db.Integer)
    temperature_c = db.Column(db.Float)
    iot_device_id = db.Column(db.String(36))

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "marketplace_booking_id": self.marketplace_booking_id,
            "collector_id": self.collector_id,
            "sample_tracking_id": self.sample_tracking_id,
            "collector_name": self.collector_name,
            "status": self.status,
            "collected_at": self.collected_at.isoformat() if self.collected_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "specimen_type": self.specimen_type,
            "barcode_value": self.barcode_value,
            "expected_barcode": self.expected_barcode,
            "collection_location": self.collection_location,
            "location_city": self.location_city,
            "notes": self.notes,
            "quality_status": self.quality_status,
            "rejection_reason": self.rejection_reason,
            "partner_id": self.partner_id,
            "recollect_of_id": self.recollect_of_id,
            "patient_verified": bool(self.patient_verified),
            "order_verified": bool(self.order_verified),
            "picked_up_at": self.picked_up_at.isoformat() if self.picked_up_at else None,
            "dispatched_at": self.dispatched_at.isoformat() if self.dispatched_at else None,
            "handoff_at": self.handoff_at.isoformat() if self.handoff_at else None,
            "arrived_at_lab": self.arrived_at_lab.isoformat() if self.arrived_at_lab else None,
            "vehicle_id": self.vehicle_id,
            "driver_id": self.driver_id,
            "transport_box_id": self.transport_box_id,
            "distance_km": self.distance_km,
            "eta_minutes": self.eta_minutes,
            "temperature_c": self.temperature_c,
            "iot_device_id": self.iot_device_id,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
