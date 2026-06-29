from datetime import datetime

from app.core.audit import write_audit
from app.core.events import write_event
from app.core.statuses import (
    ASSIGNMENT_ASSIGNED,
    ASSIGNMENT_PENDING,
    BOOKING_TIMELINE_COLLECTOR_ASSIGNED,
    BOOKING_TIMELINE_COLLECTOR_ASSIGNMENT_PENDING,
    COLLECTOR_AVAILABLE,
    MARKETPLACE_BOOKING_ASSIGNED,
)
from app.extensions.db import db
from app.models.booking_assignment import BookingAssignment
from app.models.collector_availability import CollectorAvailability
from app.models.marketplace_booking import MarketplaceBooking
from app.services.marketplace_booking import MarketplaceBookingService
from app.services.scheduling import SchedulingService


class BookingAssignmentError(Exception):

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class BookingAssignmentService:

    @staticmethod
    def _get_booking_or_raise(booking_id):
        booking = MarketplaceBooking.query.get(booking_id)
        if not booking:
            raise BookingAssignmentError("Booking not found", 404)
        return booking

    @staticmethod
    def _find_collector_availability(collector_id, booking):
        query = CollectorAvailability.query.filter_by(
            collector_id=collector_id,
            date=booking.requested_date,
            status=COLLECTOR_AVAILABLE,
        )
        if booking.city:
            query = query.filter(CollectorAvailability.city.ilike(f"%{booking.city}%"))
        return query.order_by(CollectorAvailability.start_time.asc()).first()

    @staticmethod
    def assign_collector(
        booking_id,
        collector_id,
        note=None,
        actor_email="SYSTEM",
        ip_address="",
    ):
        booking = BookingAssignmentService._get_booking_or_raise(booking_id)

        if not collector_id:
            raise BookingAssignmentError("collector_id is required")

        availability = BookingAssignmentService._find_collector_availability(
            collector_id,
            booking,
        )
        if availability and availability.assigned_jobs >= availability.max_jobs:
            raise BookingAssignmentError("Collector has no remaining job capacity", 409)

        MarketplaceBookingService.write_timeline_event(
            booking,
            BOOKING_TIMELINE_COLLECTOR_ASSIGNMENT_PENDING,
            message=f"Collector assignment pending for booking {booking.booking_code}",
            actor_email=actor_email,
            audit_action="BOOKING_COLLECTOR_ASSIGNMENT_PENDING",
            ip_address=ip_address,
        )

        assignment = BookingAssignment.query.filter_by(
            booking_id=booking.id,
            assignment_status=ASSIGNMENT_PENDING,
        ).first()

        if not assignment:
            assignment = BookingAssignment(
                booking_id=booking.id,
                partner_id=booking.partner_id,
                scheduled_slot_id=booking.scheduled_slot_id,
                assignment_status=ASSIGNMENT_PENDING,
            )
            db.session.add(assignment)
            db.session.flush()

        assignment.collector_id = collector_id
        assignment.assignment_status = ASSIGNMENT_ASSIGNED
        assignment.assigned_at = datetime.utcnow()
        assignment.note = note
        assignment.updated_at = datetime.utcnow()

        if availability:
            availability.assigned_jobs += 1
            availability.updated_at = datetime.utcnow()

        booking.status = MARKETPLACE_BOOKING_ASSIGNED
        booking.updated_at = datetime.utcnow()

        MarketplaceBookingService.write_timeline_event(
            booking,
            BOOKING_TIMELINE_COLLECTOR_ASSIGNED,
            message=f"Collector {collector_id} assigned to booking {booking.booking_code}",
            actor_email=actor_email,
            audit_action="BOOKING_COLLECTOR_ASSIGNED",
            ip_address=ip_address,
        )

        write_audit(
            action="BOOKING_COLLECTOR_ASSIGNED",
            object_type="BookingAssignment",
            object_id=assignment.id,
            user_email=actor_email,
            ip_address=ip_address,
        )
        write_event(
            event_type="BOOKING_COLLECTOR_ASSIGNED",
            object_type="BookingAssignment",
            object_id=assignment.id,
            message=f"Booking {booking.booking_code} assigned to collector {collector_id}",
        )

        db.session.commit()
        return assignment

    @staticmethod
    def reserve_slot_for_booking(
        booking_id,
        slot_id,
        actor_email="SYSTEM",
        ip_address="",
    ):
        from app.core.statuses import BOOKING_TIMELINE_SLOT_RESERVED

        booking = BookingAssignmentService._get_booking_or_raise(booking_id)
        slot = SchedulingService.validate_slot_for_booking(
            booking.partner_id,
            slot_id,
            requested_date=booking.requested_date,
            requested_time_slot=booking.requested_time_slot,
        )

        SchedulingService.reserve_slot(
            slot.id,
            booking.partner_id,
            booking_id=booking.id,
            service_type=slot.slot_type,
        )

        booking.scheduled_slot_id = slot.id
        booking.requested_date = slot.slot_date
        booking.requested_time_slot = f"{slot.start_time}-{slot.end_time}"
        booking.updated_at = datetime.utcnow()

        MarketplaceBookingService.write_timeline_event(
            booking,
            BOOKING_TIMELINE_SLOT_RESERVED,
            message=f"Slot {slot.start_time}-{slot.end_time} reserved for booking {booking.booking_code}",
            actor_email=actor_email,
            audit_action="BOOKING_SLOT_RESERVED",
            ip_address=ip_address,
        )

        db.session.commit()
        return booking, slot

    @staticmethod
    def list_collector_availability(city=None, district=None, date=None):
        query = CollectorAvailability.query

        if city:
            query = query.filter(CollectorAvailability.city.ilike(f"%{city.strip()}%"))

        if district:
            query = query.filter(CollectorAvailability.district.ilike(f"%{district.strip()}%"))

        if date:
            query = query.filter(CollectorAvailability.date == date)

        return query.order_by(
            CollectorAvailability.date.asc(),
            CollectorAvailability.start_time.asc(),
        ).all()

    @staticmethod
    def get_assignment_for_booking(booking_id):
        return BookingAssignment.query.filter_by(booking_id=booking_id).order_by(
            BookingAssignment.created_at.desc()
        ).first()
