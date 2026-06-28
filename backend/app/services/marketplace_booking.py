from datetime import datetime

from sqlalchemy.exc import IntegrityError

from app.core.audit import write_audit
from app.core.events import write_event
from app.core.statuses import (
    BOOKING_EVENT_STATUS_MAP,
    BOOKING_TIMELINE_CREATED,
    MAPPING_ACTIVE,
    MARKETPLACE_BOOKING_CREATED,
    MARKETPLACE_VISIBLE_PARTNER_STATUSES,
    VALID_BOOKING_TIMELINE_EVENTS,
    VALID_MARKETPLACE_BOOKING_STATUSES,
)
from app.extensions.db import db
from app.models.marketplace_booking import MarketplaceBooking
from app.models.marketplace_booking_timeline import MarketplaceBookingTimeline
from app.models.partner import Partner
from app.models.partner_service_mapping import PartnerServiceMapping
from app.services.partner_availability import PartnerAvailabilityService


class MarketplaceBookingError(Exception):

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class MarketplaceBookingService:

    @staticmethod
    def _generate_booking_code():
        count = MarketplaceBooking.query.count()
        return f"DXM-{count + 1:06d}"

    @staticmethod
    def _get_booking_or_raise(booking_id):
        booking = MarketplaceBooking.query.get(booking_id)
        if not booking:
            raise MarketplaceBookingError("Booking not found", 404)
        return booking

    @staticmethod
    def _write_timeline(
        booking,
        event_type,
        message=None,
        actor_email="SYSTEM",
    ):
        if event_type not in VALID_BOOKING_TIMELINE_EVENTS:
            raise MarketplaceBookingError(
                f"Invalid timeline event. Must be one of: {', '.join(VALID_BOOKING_TIMELINE_EVENTS)}"
            )

        timeline = MarketplaceBookingTimeline(
            booking_id=booking.id,
            event_type=event_type,
            message=message or f"Booking {booking.booking_code} reached {event_type}",
            actor_email=actor_email,
        )
        db.session.add(timeline)
        return timeline

    @staticmethod
    def write_timeline_event(
        booking,
        event_type,
        message=None,
        actor_email="SYSTEM",
        audit_action=None,
        ip_address="",
        write_event_log=True,
    ):
        timeline = MarketplaceBookingService._write_timeline(
            booking,
            event_type,
            message=message,
            actor_email=actor_email,
        )

        if audit_action:
            write_audit(
                action=audit_action,
                object_type="MarketplaceBooking",
                object_id=booking.id,
                user_email=actor_email,
                ip_address=ip_address,
            )

        if write_event_log:
            write_event(
                event_type=audit_action or f"MARKETPLACE_BOOKING_{event_type}",
                object_type="MarketplaceBooking",
                object_id=booking.id,
                message=message or f"Booking {booking.booking_code} reached {event_type}",
            )

        return timeline

    @staticmethod
    def transition_booking(
        booking_id,
        event_type,
        message=None,
        actor_email="SYSTEM",
        ip_address="",
        update_status=True,
    ):
        booking = MarketplaceBookingService._get_booking_or_raise(booking_id)

        MarketplaceBookingService._write_timeline(
            booking,
            event_type,
            message=message,
            actor_email=actor_email,
        )

        if update_status and event_type in BOOKING_EVENT_STATUS_MAP:
            booking.status = BOOKING_EVENT_STATUS_MAP[event_type]

        booking.updated_at = datetime.utcnow()

        write_audit(
            action=f"MARKETPLACE_BOOKING_{event_type}",
            object_type="MarketplaceBooking",
            object_id=booking.id,
            user_email=actor_email,
            ip_address=ip_address,
        )
        write_event(
            event_type=f"MARKETPLACE_BOOKING_{event_type}",
            object_type="MarketplaceBooking",
            object_id=booking.id,
            message=message or f"Booking {booking.booking_code} transitioned to {event_type}",
        )
        db.session.commit()
        return booking

    @staticmethod
    def create_booking(data, actor_email="SYSTEM", ip_address=""):
        mapping_id = data.get("partner_service_mapping_id")
        patient_name = data.get("patient_name")
        patient_phone = data.get("patient_phone")

        if not mapping_id or not patient_name or not patient_phone:
            raise MarketplaceBookingError(
                "partner_service_mapping_id, patient_name, and patient_phone are required"
            )

        mapping = PartnerServiceMapping.query.get(mapping_id)
        if not mapping or mapping.status != MAPPING_ACTIVE:
            raise MarketplaceBookingError("Partner service mapping not found", 404)

        partner = Partner.query.get(mapping.partner_id)
        if not partner or partner.status not in MARKETPLACE_VISIBLE_PARTNER_STATUSES:
            raise MarketplaceBookingError("Partner is not available for booking", 409)

        requested_date = data.get("requested_date") or datetime.utcnow().strftime("%Y-%m-%d")

        availability = PartnerAvailabilityService.get_or_create(partner.id, requested_date)
        if availability.available_slots <= 0:
            raise MarketplaceBookingError(
                "Partner has no available slots for the requested date",
                409,
            )

        booking = MarketplaceBooking(
            booking_code=MarketplaceBookingService._generate_booking_code(),
            patient_name=patient_name,
            patient_phone=patient_phone,
            patient_email=data.get("patient_email"),
            patient_address=data.get("patient_address"),
            province=data.get("province") or partner.province,
            city=data.get("city") or partner.city,
            district=data.get("district") or partner.district,
            partner_id=mapping.partner_id,
            diagnostic_service_id=mapping.diagnostic_service_id,
            partner_service_mapping_id=mapping.id,
            requested_date=requested_date,
            requested_time_slot=data.get("requested_time_slot"),
            status=data.get("status", MARKETPLACE_BOOKING_CREATED),
            note=data.get("note"),
        )

        if booking.status not in VALID_MARKETPLACE_BOOKING_STATUSES:
            raise MarketplaceBookingError(
                f"Invalid status. Must be one of: {', '.join(VALID_MARKETPLACE_BOOKING_STATUSES)}"
            )

        try:
            db.session.add(booking)
            db.session.flush()
            PartnerAvailabilityService.reserve_slot(partner.id, requested_date)
            MarketplaceBookingService._write_timeline(
                booking,
                BOOKING_TIMELINE_CREATED,
                message=f"Booking {booking.booking_code} created",
                actor_email=actor_email,
            )
            write_audit(
                action="MARKETPLACE_BOOKING_CREATED",
                object_type="MarketplaceBooking",
                object_id=booking.id,
                user_email=actor_email,
                ip_address=ip_address,
            )
            write_event(
                event_type="MARKETPLACE_BOOKING_CREATED",
                object_type="MarketplaceBooking",
                object_id=booking.id,
                message=f"Marketplace booking {booking.booking_code} created",
            )
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise MarketplaceBookingError("Could not create booking", 409)

        return booking

    @staticmethod
    def list_bookings(status=None, partner_id=None):
        query = MarketplaceBooking.query

        if status:
            query = query.filter(MarketplaceBooking.status == status)

        if partner_id:
            query = query.filter(MarketplaceBooking.partner_id == partner_id)

        return query.order_by(MarketplaceBooking.created_at.desc()).all()

    @staticmethod
    def get_booking(booking_id):
        return MarketplaceBookingService._get_booking_or_raise(booking_id)

    @staticmethod
    def list_booking_timeline(booking_id):
        MarketplaceBookingService._get_booking_or_raise(booking_id)
        return MarketplaceBookingTimeline.query.filter_by(booking_id=booking_id).order_by(
            MarketplaceBookingTimeline.created_at.asc()
        ).all()

    @staticmethod
    def get_booking_detail(booking_id):
        booking = MarketplaceBookingService._get_booking_or_raise(booking_id)
        payload = booking.to_dict()
        payload["partner"] = booking.partner.to_dict() if booking.partner else None
        payload["service"] = (
            booking.diagnostic_service.to_dict() if booking.diagnostic_service else None
        )
        payload["mapping"] = (
            booking.partner_service_mapping.to_dict()
            if booking.partner_service_mapping
            else None
        )
        payload["timeline"] = [
            event.to_dict()
            for event in MarketplaceBookingService.list_booking_timeline(booking_id)
        ]
        return payload
