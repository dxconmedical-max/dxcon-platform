"""Patient Marketplace ORM models — Epic 5."""

from __future__ import annotations

import json
import uuid
from datetime import datetime

from app.extensions.db import db


class MpProvider(db.Model):
    __tablename__ = "mp_providers"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), nullable=False, index=True)
    partner_id = db.Column(db.String(36), db.ForeignKey("partners.id"))
    provider_code = db.Column(db.String(80), unique=True, nullable=False)
    provider_name = db.Column(db.String(255), nullable=False)
    provider_type = db.Column(db.String(50), nullable=False)
    verified = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text)
    address = db.Column(db.Text)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    working_hours_json = db.Column(db.Text, default="{}")
    service_areas_json = db.Column(db.Text, default="[]")
    certifications_json = db.Column(db.Text, default="[]")
    specialties_json = db.Column(db.Text, default="[]")
    rating_avg = db.Column(db.Float, default=0.0)
    rating_count = db.Column(db.Integer, default=0)
    turnaround_hours = db.Column(db.Integer)
    collection_methods_json = db.Column(db.Text, default="[]")
    payment_methods_json = db.Column(db.Text, default="[]")
    cancellation_policy = db.Column(db.Text)
    public_status = db.Column(db.String(30), default="ACTIVE")
    featured = db.Column(db.Boolean, default=False)
    city = db.Column(db.String(100))
    category = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def public_dict(self) -> dict:
        return {
            "id": self.id,
            "provider_code": self.provider_code,
            "provider_name": self.provider_name,
            "provider_type": self.provider_type,
            "verified": self.verified,
            "description": self.description,
            "address": self.address,
            "coordinates": {"lat": self.latitude, "lng": self.longitude} if self.latitude else None,
            "rating_avg": self.rating_avg,
            "rating_count": self.rating_count,
            "turnaround_hours": self.turnaround_hours,
            "collection_methods": json.loads(self.collection_methods_json or "[]"),
            "payment_methods": json.loads(self.payment_methods_json or "[]"),
            "cancellation_policy": self.cancellation_policy,
            "city": self.city,
            "category": self.category,
            "featured": self.featured,
        }


class MpService(db.Model):
    __tablename__ = "mp_services"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), nullable=False, index=True)
    service_code = db.Column(db.String(80), nullable=False)
    service_name = db.Column(db.String(255), nullable=False)
    service_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    preparation_instructions = db.Column(db.Text)
    sample_requirements = db.Column(db.Text)
    duration_minutes = db.Column(db.Integer, default=30)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("organization_id", "service_code", name="uq_mp_service_org_code"),)


class MpListing(db.Model):
    __tablename__ = "mp_listings"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), nullable=False, index=True)
    provider_id = db.Column(db.String(36), db.ForeignKey("mp_providers.id"), nullable=False)
    service_id = db.Column(db.String(36), db.ForeignKey("mp_services.id"), nullable=False)
    listing_code = db.Column(db.String(80), unique=True, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(30), default="DRAFT", nullable=False)
    base_price = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    currency = db.Column(db.String(3), default="VND")
    home_collection_available = db.Column(db.Boolean, default=False)
    service_radius_km = db.Column(db.Float)
    price_updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    partner_consent = db.Column(db.Boolean, default=False)
    turnaround_hours = db.Column(db.Integer)
    featured = db.Column(db.Boolean, default=False)
    category = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    provider = db.relationship("MpProvider")
    service = db.relationship("MpService")

    def public_dict(self) -> dict:
        return {
            "id": self.id,
            "listing_code": self.listing_code,
            "title": self.title,
            "status": self.status,
            "base_price": float(self.base_price or 0),
            "currency": self.currency,
            "home_collection_available": self.home_collection_available,
            "price_updated_at": self.price_updated_at.isoformat() if self.price_updated_at else None,
            "provider": self.provider.public_dict() if self.provider else None,
            "service_type": self.service.service_type if self.service else None,
            "service_name": self.service.service_name if self.service else None,
            "turnaround_hours": self.turnaround_hours or (self.provider.turnaround_hours if self.provider else None),
            "category": self.category,
            "featured": self.featured,
        }


class MpPromotion(db.Model):
    __tablename__ = "mp_promotions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), nullable=False, index=True)
    promotion_code = db.Column(db.String(50), nullable=False)
    promotion_type = db.Column(db.String(30), default="PLATFORM")
    discount_percent = db.Column(db.Numeric(5, 2))
    discount_amount = db.Column(db.Numeric(12, 2))
    min_order_amount = db.Column(db.Numeric(12, 2), default=0)
    usage_limit = db.Column(db.Integer)
    per_patient_limit = db.Column(db.Integer, default=1)
    usage_count = db.Column(db.Integer, default=0)
    starts_at = db.Column(db.DateTime)
    ends_at = db.Column(db.DateTime)
    stacking_policy = db.Column(db.String(20), default="NONE")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("organization_id", "promotion_code", name="uq_mp_promo_org_code"),)


class MpPricingSnapshot(db.Model):
    __tablename__ = "mp_pricing_snapshots"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), nullable=False)
    listing_id = db.Column(db.String(36), db.ForeignKey("mp_listings.id"))
    components_json = db.Column(db.Text, nullable=False)
    rule_versions_json = db.Column(db.Text, default="{}")
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)
    currency = db.Column(db.String(3), default="VND")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class MpBooking(db.Model):
    __tablename__ = "mp_bookings"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_code = db.Column(db.String(50), unique=True, nullable=False)
    patient_id = db.Column(db.String(36))
    patient_user_id = db.Column(db.String(36))
    organization_id = db.Column(db.String(36), nullable=False, index=True)
    provider_id = db.Column(db.String(36), db.ForeignKey("mp_providers.id"), nullable=False)
    listing_id = db.Column(db.String(36), db.ForeignKey("mp_listings.id"), nullable=False)
    service_type = db.Column(db.String(50))
    appointment_type = db.Column(db.String(50))
    scheduled_start = db.Column(db.DateTime)
    scheduled_end = db.Column(db.DateTime)
    pickup_address = db.Column(db.Text)
    clinic_address = db.Column(db.Text)
    contact_phone = db.Column(db.String(30))
    preparation_acknowledged = db.Column(db.Boolean, default=False)
    consent_status = db.Column(db.String(30), default="PENDING")
    pricing_snapshot_id = db.Column(db.String(36), db.ForeignKey("mp_pricing_snapshots.id"))
    booking_status = db.Column(db.String(30), default="DRAFT")
    order_id = db.Column(db.String(36))
    collection_job_id = db.Column(db.String(36))
    idempotency_key = db.Column(db.String(80), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    listing = db.relationship("MpListing")
    provider = db.relationship("MpProvider")
    pricing_snapshot = db.relationship("MpPricingSnapshot")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "booking_code": self.booking_code,
            "booking_status": self.booking_status,
            "organization_id": self.organization_id,
            "provider_id": self.provider_id,
            "listing_id": self.listing_id,
            "scheduled_start": self.scheduled_start.isoformat() if self.scheduled_start else None,
            "pricing_snapshot_id": self.pricing_snapshot_id,
            "order_id": self.order_id,
            "collection_job_id": self.collection_job_id,
        }


class MpAvailability(db.Model):
    __tablename__ = "mp_availability"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), nullable=False, index=True)
    provider_id = db.Column(db.String(36), db.ForeignKey("mp_providers.id"), nullable=False)
    slot_start = db.Column(db.DateTime, nullable=False)
    slot_end = db.Column(db.DateTime, nullable=False)
    capacity = db.Column(db.Integer, default=1)
    reserved = db.Column(db.Integer, default=0)
    is_blocked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("provider_id", "slot_start", name="uq_mp_avail_provider_slot"),
    )


class MpPayment(db.Model):
    __tablename__ = "mp_payments"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), nullable=False, index=True)
    booking_id = db.Column(db.String(36), db.ForeignKey("mp_bookings.id"), nullable=False)
    payment_reference = db.Column(db.String(80), unique=True, nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    currency = db.Column(db.String(3), default="VND")
    payment_method = db.Column(db.String(30), default="QR_BANK_TRANSFER")
    status = db.Column(db.String(30), default="CREATED")
    qr_payload = db.Column(db.Text)
    provider_code = db.Column(db.String(50))
    expires_at = db.Column(db.DateTime)
    webhook_idempotency_key = db.Column(db.String(80), unique=True)
    reconciliation_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    booking = db.relationship("MpBooking")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "payment_reference": self.payment_reference,
            "amount": float(self.amount),
            "currency": self.currency,
            "status": self.status,
            "payment_method": self.payment_method,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "qr_payload": self.qr_payload,
        }


class MpReview(db.Model):
    __tablename__ = "mp_reviews"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), nullable=False)
    booking_id = db.Column(db.String(36), db.ForeignKey("mp_bookings.id"), unique=True)
    provider_id = db.Column(db.String(36), db.ForeignKey("mp_providers.id"))
    patient_user_id = db.Column(db.String(36))
    rating = db.Column(db.Integer, nullable=False)
    review_text = db.Column(db.Text)
    moderation_status = db.Column(db.String(20), default="PENDING")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class MpAuditEvent(db.Model):
    __tablename__ = "mp_audit_events"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), nullable=False, index=True)
    event_type = db.Column(db.String(80), nullable=False)
    actor_id = db.Column(db.String(36))
    resource_type = db.Column(db.String(50))
    resource_id = db.Column(db.String(36))
    outcome = db.Column(db.String(30))
    details_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class MpSlotHold(db.Model):
    __tablename__ = "mp_slot_holds"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), nullable=False, index=True)
    provider_id = db.Column(db.String(36), db.ForeignKey("mp_providers.id"), nullable=False)
    availability_id = db.Column(db.String(36), db.ForeignKey("mp_availability.id"))
    patient_user_id = db.Column(db.String(36))
    hold_token = db.Column(db.String(64), unique=True, nullable=False)
    slot_start = db.Column(db.DateTime, nullable=False)
    slot_end = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(30), default="HELD")
    expires_at = db.Column(db.DateTime, nullable=False)
    booking_id = db.Column(db.String(36))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class MpPatientAddress(db.Model):
    __tablename__ = "mp_patient_addresses"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), nullable=False, index=True)
    patient_user_id = db.Column(db.String(36), nullable=False, index=True)
    label = db.Column(db.String(50), default="Home")
    address_line = db.Column(db.Text, nullable=False)
    building = db.Column(db.String(100))
    apartment = db.Column(db.String(50))
    city = db.Column(db.String(100))
    district = db.Column(db.String(100))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    contact_instructions = db.Column(db.Text)
    collector_notes = db.Column(db.Text)
    preferred_window_start = db.Column(db.String(10))
    preferred_window_end = db.Column(db.String(10))
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "address_line": self.address_line,
            "building": self.building,
            "apartment": self.apartment,
            "city": self.city,
            "district": self.district,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "contact_instructions": self.contact_instructions,
            "collector_notes": self.collector_notes,
            "preferred_window_start": self.preferred_window_start,
            "preferred_window_end": self.preferred_window_end,
            "is_default": self.is_default,
        }


class MpHoliday(db.Model):
    __tablename__ = "mp_holidays"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), nullable=False, index=True)
    provider_id = db.Column(db.String(36), db.ForeignKey("mp_providers.id"))
    holiday_date = db.Column(db.Date, nullable=False)
    name = db.Column(db.String(255))
    is_closed = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class MpPackageItem(db.Model):
    __tablename__ = "mp_package_items"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), nullable=False)
    package_listing_id = db.Column(db.String(36), db.ForeignKey("mp_listings.id"), nullable=False)
    service_id = db.Column(db.String(36), db.ForeignKey("mp_services.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    sort_order = db.Column(db.Integer, default=0)
