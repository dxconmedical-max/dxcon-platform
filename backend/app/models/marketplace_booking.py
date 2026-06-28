from datetime import datetime
import uuid

from app.extensions.db import db


class MarketplaceBooking(db.Model):

    __tablename__ = "marketplace_bookings"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    booking_code = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
    )

    patient_name = db.Column(
        db.String(255),
        nullable=False,
    )

    patient_phone = db.Column(
        db.String(30),
        nullable=False,
    )

    patient_email = db.Column(
        db.String(255),
    )

    patient_address = db.Column(
        db.Text,
    )

    province = db.Column(
        db.String(100),
    )

    city = db.Column(
        db.String(100),
    )

    district = db.Column(
        db.String(100),
    )

    partner_id = db.Column(
        db.String(36),
        db.ForeignKey("partners.id"),
        nullable=False,
    )

    diagnostic_service_id = db.Column(
        db.String(36),
        db.ForeignKey("diagnostic_services.id"),
        nullable=False,
    )

    partner_service_mapping_id = db.Column(
        db.String(36),
        db.ForeignKey("partner_service_mappings.id"),
        nullable=False,
    )

    requested_date = db.Column(
        db.String(20),
    )

    requested_time_slot = db.Column(
        db.String(50),
    )

    scheduled_slot_id = db.Column(
        db.String(36),
        db.ForeignKey("scheduling_slots.id"),
    )

    status = db.Column(
        db.String(50),
        default="CREATED",
        nullable=False,
    )

    note = db.Column(
        db.Text,
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    partner = db.relationship("Partner", backref=db.backref("marketplace_bookings", lazy=True))
    diagnostic_service = db.relationship("DiagnosticService")
    partner_service_mapping = db.relationship("PartnerServiceMapping")
    scheduled_slot = db.relationship("SchedulingSlot")

    def to_dict(self):
        return {
            "id": self.id,
            "booking_code": self.booking_code,
            "patient_name": self.patient_name,
            "patient_phone": self.patient_phone,
            "patient_email": self.patient_email,
            "patient_address": self.patient_address,
            "province": self.province,
            "city": self.city,
            "district": self.district,
            "partner_id": self.partner_id,
            "diagnostic_service_id": self.diagnostic_service_id,
            "partner_service_mapping_id": self.partner_service_mapping_id,
            "requested_date": self.requested_date,
            "requested_time_slot": self.requested_time_slot,
            "scheduled_slot_id": self.scheduled_slot_id,
            "status": self.status,
            "note": self.note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
