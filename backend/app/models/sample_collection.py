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

    # Authoritative routing: AT_RECEPTION | HOME_COLLECTION | CLINIC_COLLECTION
    collection_mode = db.Column(db.String(50))

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

    # Field collection request metadata (HOME / CLINIC)
    pickup_address = db.Column(db.String(500))
    pickup_city = db.Column(db.String(100))
    pickup_province = db.Column(db.String(100))
    pickup_district = db.Column(db.String(100))
    pickup_ward = db.Column(db.String(100))
    contact_person = db.Column(db.String(255))
    contact_phone = db.Column(db.String(50))
    requested_date = db.Column(db.String(20))
    requested_time_window = db.Column(db.String(100))
    pickup_latitude = db.Column(db.String(50))
    pickup_longitude = db.Column(db.String(50))
    collection_request_note = db.Column(db.Text)
    clinic_name = db.Column(db.String(255))
    priority = db.Column(db.String(50))

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def to_dict(self):
        def _iso(value):
            if value is None:
                return None
            if hasattr(value, "isoformat"):
                return value.isoformat()
            return str(value)

        return {
            "id": self.id,
            "order_id": self.order_id,
            "marketplace_booking_id": self.marketplace_booking_id,
            "collection_mode": self.collection_mode,
            "collector_id": self.collector_id,
            "sample_tracking_id": self.sample_tracking_id,
            "collector_name": self.collector_name,
            "status": self.status,
            "collected_at": _iso(self.collected_at),
            "created_at": _iso(self.created_at),
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
            "picked_up_at": _iso(self.picked_up_at),
            "dispatched_at": _iso(self.dispatched_at),
            "handoff_at": _iso(self.handoff_at),
            "arrived_at_lab": _iso(self.arrived_at_lab),
            "vehicle_id": self.vehicle_id,
            "driver_id": self.driver_id,
            "transport_box_id": self.transport_box_id,
            "distance_km": self.distance_km,
            "eta_minutes": self.eta_minutes,
            "temperature_c": self.temperature_c,
            "iot_device_id": self.iot_device_id,
            "pickup_address": self.pickup_address,
            "pickup_city": self.pickup_city,
            "pickup_province": self.pickup_province,
            "pickup_district": self.pickup_district,
            "pickup_ward": self.pickup_ward,
            "contact_person": self.contact_person,
            "contact_phone": self.contact_phone,
            "requested_date": _iso(self.requested_date) if not isinstance(self.requested_date, str) else self.requested_date,
            "requested_time_window": self.requested_time_window,
            "pickup_latitude": self.pickup_latitude,
            "pickup_longitude": self.pickup_longitude,
            "collection_request_note": self.collection_request_note,
            "clinic_name": self.clinic_name,
            "priority": self.priority,
            "updated_at": _iso(self.updated_at),
        }
