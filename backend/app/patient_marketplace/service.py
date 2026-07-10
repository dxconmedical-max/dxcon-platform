"""Patient Marketplace service layer — Epic 5."""

from __future__ import annotations

import hashlib
import hmac
import json
import math
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import or_

from app.extensions.db import db
from app.patient_marketplace.constants import (
    BOOKING_STATUSES,
    LISTING_STATUSES,
    MAX_COMPARE_ITEMS,
    QR_EXPIRY_MINUTES,
)
from app.patient_marketplace.models import (
    MpAuditEvent,
    MpAvailability,
    MpBooking,
    MpListing,
    MpPayment,
    MpPricingSnapshot,
    MpPromotion,
    MpProvider,
    MpReview,
    MpService,
)


class MarketplaceError(Exception):
    def __init__(self, message: str, status_code: int = 400, code: str = "MARKETPLACE_ERROR"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


def _audit(org_id: str, event_type: str, actor: str | None, resource_type: str, resource_id: str, outcome: str, details: dict | None = None):
    db.session.add(
        MpAuditEvent(
            organization_id=org_id,
            event_type=event_type,
            actor_id=actor,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome=outcome,
            details_json=json.dumps(details or {}),
        )
    )


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return round(2 * r * math.asin(math.sqrt(a)), 2)


class CatalogService:
    @staticmethod
    def create_listing(data: dict, organization_id: str, actor: str | None = None) -> dict:
        listing = MpListing(
            organization_id=organization_id,
            provider_id=data["provider_id"],
            service_id=data["service_id"],
            listing_code=data.get("listing_code") or f"LST-{uuid.uuid4().hex[:8].upper()}",
            title=data["title"],
            status=data.get("status", "DRAFT"),
            base_price=Decimal(str(data.get("base_price", 0))),
            currency=data.get("currency", "VND"),
            home_collection_available=data.get("home_collection_available", False),
            service_radius_km=data.get("service_radius_km"),
            partner_consent=data.get("partner_consent", False),
        )
        db.session.add(listing)
        db.session.flush()
        _audit(organization_id, "listing_created", actor, "MpListing", listing.id, "SUCCESS")
        return listing.public_dict()

    @staticmethod
    def approve_listing(listing_id: str, organization_id: str, actor: str | None = None) -> dict:
        listing = MpListing.query.filter_by(id=listing_id, organization_id=organization_id).first()
        if not listing:
            raise MarketplaceError("Listing not found", 404, "NOT_FOUND")
        if not listing.partner_consent:
            raise MarketplaceError("Partner consent required", 422, "CONSENT_REQUIRED")
        listing.status = "ACTIVE"
        listing.updated_at = datetime.utcnow()
        _audit(organization_id, "listing_approved", actor, "MpListing", listing.id, "SUCCESS")
        db.session.commit()
        return listing.public_dict()


class SearchService:
    @staticmethod
    def search_listings(
        q: str | None = None,
        city: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        service_type: str | None = None,
        home_collection: bool | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict:
        query = (
            MpListing.query.join(MpProvider).join(MpService)
            .filter(MpListing.status == "ACTIVE")
            .filter(MpProvider.public_status == "ACTIVE")
        )
        if q:
            term = f"%{q.strip()}%"
            query = query.filter(or_(MpListing.title.ilike(term), MpService.service_name.ilike(term)))
        if city:
            query = query.filter(MpProvider.address.ilike(f"%{city}%"))
        if service_type:
            query = query.filter(MpService.service_type == service_type)
        if home_collection is True:
            query = query.filter(MpListing.home_collection_available.is_(True))
        if min_price is not None:
            query = query.filter(MpListing.base_price >= min_price)
        if max_price is not None:
            query = query.filter(MpListing.base_price <= max_price)
        total = query.count()
        items = query.order_by(MpListing.price_updated_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
        return {
            "count": total,
            "page": page,
            "per_page": per_page,
            "listings": [item.public_dict() for item in items],
        }

    @staticmethod
    def provider_profile(provider_id: str) -> dict:
        provider = MpProvider.query.filter_by(id=provider_id, public_status="ACTIVE").first()
        if not provider:
            raise MarketplaceError("Provider not found", 404, "NOT_FOUND")
        return provider.public_dict()


class ComparisonService:
    @staticmethod
    def compare_listings(listing_ids: list[str], patient_lat: float | None = None, patient_lng: float | None = None) -> dict:
        if not listing_ids:
            raise MarketplaceError("listing_ids required", 400)
        if len(listing_ids) > MAX_COMPARE_ITEMS:
            raise MarketplaceError(f"Maximum {MAX_COMPARE_ITEMS} items", 400)
        ts = datetime.utcnow().isoformat()
        rows = []
        for lid in listing_ids:
            listing = MpListing.query.filter_by(id=lid, status="ACTIVE").first()
            if not listing:
                continue
            entry = listing.public_dict()
            entry["comparison_timestamp"] = ts
            if patient_lat and patient_lng and listing.provider and listing.provider.latitude:
                entry["distance_km"] = _haversine_km(
                    patient_lat, patient_lng, listing.provider.latitude, listing.provider.longitude or 0
                )
            rows.append(entry)
        return {"compared_at": ts, "items": rows, "count": len(rows)}


class PricingService:
    @staticmethod
    def quote(listing_id: str, promotion_code: str | None = None, distance_km: float = 0, urgent: bool = False) -> dict:
        listing = MpListing.query.filter_by(id=listing_id, status="ACTIVE").first()
        if not listing:
            raise MarketplaceError("Listing not found", 404)
        base = Decimal(str(listing.base_price))
        components = {"base_price": float(base), "currency": listing.currency}
        total = base
        if listing.home_collection_available and distance_km > 0:
            surcharge = Decimal(str(min(distance_km * 5000, 100000)))
            components["home_collection_fee"] = float(surcharge)
            total += surcharge
        if urgent:
            surcharge = base * Decimal("0.1")
            components["urgent_surcharge"] = float(surcharge)
            total += surcharge
        if promotion_code:
            promo = MpPromotion.query.filter_by(
                organization_id=listing.organization_id,
                promotion_code=promotion_code,
                is_active=True,
            ).first()
            if promo:
                if promo.usage_limit and promo.usage_count >= promo.usage_limit:
                    raise MarketplaceError("Promotion exhausted", 409, "PROMO_EXHAUSTED")
                if promo.discount_percent:
                    disc = total * Decimal(str(promo.discount_percent)) / Decimal("100")
                else:
                    disc = Decimal(str(promo.discount_amount or 0))
                components["promotion_discount"] = float(disc)
                components["promotion_code"] = promotion_code
                total = max(Decimal("0"), total - disc)
        snapshot = MpPricingSnapshot(
            organization_id=listing.organization_id,
            listing_id=listing.id,
            components_json=json.dumps(components),
            total_amount=total,
            currency=listing.currency,
        )
        db.session.add(snapshot)
        db.session.flush()
        _audit(listing.organization_id, "quote_generated", None, "MpPricingSnapshot", snapshot.id, "SUCCESS")
        return {
            "pricing_snapshot_id": snapshot.id,
            "components": components,
            "total_amount": float(total),
            "currency": listing.currency,
            "quoted_at": datetime.utcnow().isoformat(),
        }


class BookingService:
    @staticmethod
    def check_serviceability(provider_id: str, lat: float, lng: float) -> dict:
        provider = MpProvider.query.get(provider_id)
        if not provider or not provider.latitude:
            return {"serviceable": False, "reason": "OUT_OF_ZONE"}
        listings = MpListing.query.filter_by(provider_id=provider_id, status="ACTIVE").all()
        radius = max((l.service_radius_km or 0) for l in listings) if listings else 0
        dist = _haversine_km(lat, lng, provider.latitude, provider.longitude or 0)
        if radius and dist > radius:
            return {"serviceable": False, "distance_km": dist, "reason": "OUT_OF_ZONE"}
        return {"serviceable": True, "distance_km": dist}

    @staticmethod
    def reserve_slot(provider_id: str, slot_start: datetime, organization_id: str) -> MpAvailability:
        slot = MpAvailability.query.filter_by(
            provider_id=provider_id, slot_start=slot_start, organization_id=organization_id
        ).with_for_update().first()
        if not slot:
            raise MarketplaceError("Slot not available", 409, "SLOT_UNAVAILABLE")
        if slot.is_blocked or slot.reserved >= slot.capacity:
            raise MarketplaceError("Slot fully booked", 409, "SLOT_FULL")
        slot.reserved += 1
        return slot

    @staticmethod
    def create_booking(data: dict, organization_id: str, patient_user_id: str | None = None, actor: str | None = None) -> dict:
        idem = data.get("idempotency_key")
        if idem:
            existing = MpBooking.query.filter_by(idempotency_key=idem).first()
            if existing:
                return existing.to_dict()
        listing = MpListing.query.filter_by(id=data["listing_id"], status="ACTIVE").first()
        if not listing:
            raise MarketplaceError("Active listing required", 404)
        if listing.organization_id != organization_id and data.get("allow_cross_org"):
            pass  # platform booking across org
        org_id = listing.organization_id
        snapshot_id = data.get("pricing_snapshot_id")
        if not snapshot_id:
            quote = PricingService.quote(listing.id, data.get("promotion_code"), data.get("distance_km", 0))
            snapshot_id = quote["pricing_snapshot_id"]
        booking = MpBooking(
            booking_code=f"BK-{uuid.uuid4().hex[:10].upper()}",
            patient_user_id=patient_user_id,
            organization_id=org_id,
            provider_id=listing.provider_id,
            listing_id=listing.id,
            service_type=data.get("service_type") or (listing.service.service_type if listing.service else None),
            appointment_type=data.get("appointment_type", "IN_PERSON"),
            scheduled_start=data.get("scheduled_start"),
            pickup_address=data.get("pickup_address"),
            clinic_address=data.get("clinic_address"),
            contact_phone=data.get("contact_phone"),
            preparation_acknowledged=data.get("preparation_acknowledged", False),
            consent_status=data.get("consent_status", "GRANTED"),
            pricing_snapshot_id=snapshot_id,
            booking_status="PRICE_CONFIRMED",
            idempotency_key=idem,
        )
        db.session.add(booking)
        db.session.flush()
        _audit(org_id, "booking_created", actor or patient_user_id, "MpBooking", booking.id, "SUCCESS")
        return booking.to_dict()

    @staticmethod
    def confirm_booking(booking_id: str, organization_id: str, actor: str | None = None) -> dict:
        booking = MpBooking.query.filter_by(id=booking_id, organization_id=organization_id).first()
        if not booking:
            raise MarketplaceError("Booking not found", 404)
        if booking.booking_status not in ("PRICE_CONFIRMED", "PAYMENT_PENDING"):
            raise MarketplaceError("Invalid booking state", 409, "INVALID_STATE_TRANSITION")
        booking.booking_status = "CONFIRMED"
        booking.updated_at = datetime.utcnow()
        _audit(organization_id, "booking_confirmed", actor, "MpBooking", booking.id, "SUCCESS")
        db.session.commit()
        return booking.to_dict()

    @staticmethod
    def cancel_booking(booking_id: str, organization_id: str, reason: str, actor: str | None = None) -> dict:
        booking = MpBooking.query.filter_by(id=booking_id, organization_id=organization_id).first()
        if not booking:
            raise MarketplaceError("Booking not found", 404)
        if booking.booking_status in ("COMPLETED", "CANCELLED", "REFUNDED"):
            raise MarketplaceError("Cannot cancel", 409)
        booking.booking_status = "CANCELLED"
        booking.updated_at = datetime.utcnow()
        _audit(organization_id, "booking_cancelled", actor, "MpBooking", booking.id, "SUCCESS", {"reason": reason})
        db.session.commit()
        return booking.to_dict()


class PaymentService:
    @staticmethod
    def create_qr_payment(booking_id: str, organization_id: str, actor: str | None = None) -> dict:
        booking = MpBooking.query.filter_by(id=booking_id, organization_id=organization_id).first()
        if not booking:
            raise MarketplaceError("Booking not found", 404)
        snapshot = MpPricingSnapshot.query.get(booking.pricing_snapshot_id)
        amount = snapshot.total_amount if snapshot else Decimal("0")
        ref = f"PAY-{uuid.uuid4().hex[:12].upper()}"
        expires = datetime.utcnow() + timedelta(minutes=QR_EXPIRY_MINUTES)
        qr_data = f"DXCON|{ref}|{amount}|{booking.booking_code}"
        payment = MpPayment(
            organization_id=organization_id,
            booking_id=booking.id,
            payment_reference=ref,
            amount=amount,
            currency=snapshot.currency if snapshot else "VND",
            payment_method="QR_BANK_TRANSFER",
            status="PENDING",
            qr_payload=qr_data,
            provider_code="MANUAL_BANK_QR",
            expires_at=expires,
        )
        booking.booking_status = "PAYMENT_PENDING"
        db.session.add(payment)
        db.session.flush()
        _audit(organization_id, "payment_created", actor, "MpPayment", payment.id, "SUCCESS")
        return payment.to_dict()

    @staticmethod
    def handle_webhook(payload: dict, signature: str, secret: str) -> dict:
        ref = payload.get("payment_reference")
        amount = payload.get("amount")
        idem = payload.get("idempotency_key") or payload.get("webhook_id")
        if not ref or amount is None:
            raise MarketplaceError("Invalid webhook payload", 400)
        expected = hmac.new(secret.encode(), f"{ref}:{amount}".encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature or ""):
            raise MarketplaceError("Invalid signature", 401, "INVALID_SIGNATURE")
        if idem:
            dup = MpPayment.query.filter_by(webhook_idempotency_key=idem).first()
            if dup:
                return {"status": dup.status, "duplicate": True}
        payment = MpPayment.query.filter_by(payment_reference=ref).first()
        if not payment:
            raise MarketplaceError("Payment not found", 404)
        if Decimal(str(amount)) != Decimal(str(payment.amount)):
            raise MarketplaceError("Amount mismatch", 409, "AMOUNT_MISMATCH")
        payment.status = "SUCCEEDED"
        payment.webhook_idempotency_key = idem
        payment.updated_at = datetime.utcnow()
        booking = MpBooking.query.get(payment.booking_id)
        if booking:
            booking.booking_status = "CONFIRMED"
            OrderConversionService.convert(booking, actor="webhook")
        _audit(payment.organization_id, "payment_succeeded", "webhook", "MpPayment", payment.id, "SUCCESS")
        db.session.commit()
        return {"status": "SUCCEEDED", "payment_reference": ref}

    @staticmethod
    def payment_status(payment_reference: str, organization_id: str) -> dict:
        payment = MpPayment.query.filter_by(payment_reference=payment_reference, organization_id=organization_id).first()
        if not payment:
            raise MarketplaceError("Payment not found", 404)
        return payment.to_dict()


class OrderConversionService:
    @staticmethod
    def convert(booking: MpBooking, actor: str | None = None) -> dict:
        if booking.order_id:
            return {"order_id": booking.order_id, "already_converted": True}
        order_id = str(uuid.uuid4())
        booking.order_id = order_id
        if booking.pickup_address:
            booking.collection_job_id = str(uuid.uuid4())
        booking.booking_status = "PROVIDER_ACCEPTED"
        _audit(booking.organization_id, "order_converted", actor, "MpBooking", booking.id, "SUCCESS", {"order_id": order_id})
        return {"order_id": order_id, "collection_job_id": booking.collection_job_id}


class ReviewService:
    @staticmethod
    def submit_review(data: dict, organization_id: str, patient_user_id: str) -> dict:
        booking = MpBooking.query.filter_by(id=data["booking_id"], organization_id=organization_id).first()
        if not booking or booking.booking_status != "COMPLETED":
            raise MarketplaceError("Review not eligible", 422, "NOT_ELIGIBLE")
        if booking.patient_user_id and booking.patient_user_id != patient_user_id:
            raise MarketplaceError("Forbidden", 403)
        existing = MpReview.query.filter_by(booking_id=booking.id).first()
        if existing:
            raise MarketplaceError("Duplicate review", 409)
        review = MpReview(
            organization_id=organization_id,
            booking_id=booking.id,
            provider_id=booking.provider_id,
            patient_user_id=patient_user_id,
            rating=data["rating"],
            review_text=data.get("review_text"),
            moderation_status="PENDING",
        )
        db.session.add(review)
        _audit(organization_id, "review_submitted", patient_user_id, "MpReview", review.id, "SUCCESS")
        db.session.commit()
        return {"id": review.id, "moderation_status": review.moderation_status}
