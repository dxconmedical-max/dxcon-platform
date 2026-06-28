from datetime import datetime

from app.core.statuses import (
    CALENDAR_OWNER_PARTNER,
    SLOT_AVAILABLE,
    SLOT_BLOCKED,
    SLOT_CANCELLED,
    SLOT_FULL,
    SLOT_TYPE_COLLECTION,
)
from app.extensions.db import db
from app.models.partner import Partner
from app.models.partner_capacity import PartnerCapacity
from app.models.partner_operating_hour import PartnerOperatingHour
from app.models.scheduling_calendar import SchedulingCalendar
from app.models.scheduling_slot import SchedulingSlot


class SchedulingError(Exception):

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class SchedulingService:

    DEFAULT_OPEN = "08:00"
    DEFAULT_CLOSE = "17:00"

    @staticmethod
    def _get_partner_or_raise(partner_id):
        partner = Partner.query.get(partner_id)
        if not partner:
            raise SchedulingError("Partner not found", 404)
        return partner

    @staticmethod
    def get_or_create_partner_calendar(partner_id):
        partner = SchedulingService._get_partner_or_raise(partner_id)
        calendar = SchedulingCalendar.query.filter_by(
            owner_type=CALENDAR_OWNER_PARTNER,
            owner_id=partner.id,
        ).first()

        if not calendar:
            calendar = SchedulingCalendar(
                owner_type=CALENDAR_OWNER_PARTNER,
                owner_id=partner.id,
                name=f"{partner.display_name} Calendar",
                timezone="Asia/Ho_Chi_Minh",
                is_active=True,
            )
            db.session.add(calendar)
            db.session.flush()

        return calendar

    @staticmethod
    def _refresh_slot_status(slot):
        if slot.status == SLOT_BLOCKED or slot.status == SLOT_CANCELLED:
            return slot

        if slot.booked_count >= slot.capacity:
            slot.status = SLOT_FULL
        else:
            slot.status = SLOT_AVAILABLE

        slot.updated_at = datetime.utcnow()
        return slot

    @staticmethod
    def check_operating_hours(partner_id, slot_date, start_time, end_time):
        partner = SchedulingService._get_partner_or_raise(partner_id)
        day_of_week = datetime.strptime(slot_date, "%Y-%m-%d").weekday()
        hours = PartnerOperatingHour.query.filter_by(
            partner_id=partner.id,
            day_of_week=day_of_week,
            is_closed=False,
        ).all()

        if not hours:
            return True

        for item in hours:
            open_time = item.open_time or SchedulingService.DEFAULT_OPEN
            close_time = item.close_time or SchedulingService.DEFAULT_CLOSE
            if start_time >= open_time and end_time <= close_time:
                return True

        raise SchedulingError(
            f"Requested slot {start_time}-{end_time} is outside partner operating hours",
            409,
        )

    @staticmethod
    def get_or_create_partner_capacity(partner_id, slot_date, service_type=SLOT_TYPE_COLLECTION):
        capacity = PartnerCapacity.query.filter_by(
            partner_id=partner_id,
            date=slot_date,
            service_type=service_type,
        ).first()

        if not capacity:
            capacity = PartnerCapacity(
                partner_id=partner_id,
                date=slot_date,
                service_type=service_type,
                maximum_capacity=20,
                booked_count=0,
                remaining_capacity=20,
            )
            db.session.add(capacity)
            db.session.flush()

        return capacity

    @staticmethod
    def check_partner_capacity(partner_id, slot_date, service_type=SLOT_TYPE_COLLECTION):
        capacity = SchedulingService.get_or_create_partner_capacity(
            partner_id,
            slot_date,
            service_type,
        )
        if capacity.remaining_capacity <= 0:
            raise SchedulingError(
                f"Partner capacity exhausted for {slot_date} ({service_type})",
                409,
            )
        return capacity

    @staticmethod
    def list_available_slots(
        partner_id,
        slot_date=None,
        slot_type=SLOT_TYPE_COLLECTION,
        include_full=False,
    ):
        calendar = SchedulingService.get_or_create_partner_calendar(partner_id)
        query = SchedulingSlot.query.filter_by(
            calendar_id=calendar.id,
            slot_type=slot_type,
        )

        if slot_date:
            query = query.filter(SchedulingSlot.slot_date == slot_date)

        if not include_full:
            query = query.filter(SchedulingSlot.status == SLOT_AVAILABLE)

        return query.order_by(
            SchedulingSlot.slot_date.asc(),
            SchedulingSlot.start_time.asc(),
        ).all()

    @staticmethod
    def _get_slot_for_partner(partner_id, slot_id):
        calendar = SchedulingService.get_or_create_partner_calendar(partner_id)
        slot = SchedulingSlot.query.filter_by(
            id=slot_id,
            calendar_id=calendar.id,
        ).first()
        if not slot:
            raise SchedulingError("Scheduling slot not found for partner", 404)
        return slot

    @staticmethod
    def validate_slot_for_booking(partner_id, slot_id, requested_date=None, requested_time_slot=None):
        slot = SchedulingService._get_slot_for_partner(partner_id, slot_id)

        if slot.status not in (SLOT_AVAILABLE, SLOT_FULL):
            raise SchedulingError(f"Slot is not available (status: {slot.status})", 409)

        if slot.booked_count >= slot.capacity:
            raise SchedulingError("Slot is full", 409)

        if requested_date and slot.slot_date != requested_date:
            raise SchedulingError("Slot date does not match requested date", 409)

        if requested_time_slot:
            expected = f"{slot.start_time}-{slot.end_time}"
            if requested_time_slot != expected and requested_time_slot != slot.start_time:
                raise SchedulingError("Slot time does not match requested time slot", 409)

        SchedulingService.check_operating_hours(
            partner_id,
            slot.slot_date,
            slot.start_time,
            slot.end_time,
        )
        SchedulingService.check_partner_capacity(
            partner_id,
            slot.slot_date,
            slot.slot_type,
        )
        return slot

    @staticmethod
    def reserve_slot(slot_id, partner_id, booking_id=None, service_type=SLOT_TYPE_COLLECTION):
        slot = SchedulingService._get_slot_for_partner(partner_id, slot_id)
        SchedulingService.check_operating_hours(
            partner_id,
            slot.slot_date,
            slot.start_time,
            slot.end_time,
        )
        capacity = SchedulingService.check_partner_capacity(
            partner_id,
            slot.slot_date,
            service_type,
        )

        if slot.booked_count >= slot.capacity:
            raise SchedulingError("Slot is full", 409)

        slot.booked_count += 1
        SchedulingService._refresh_slot_status(slot)

        capacity.booked_count += 1
        capacity.remaining_capacity = max(0, capacity.maximum_capacity - capacity.booked_count)
        capacity.updated_at = datetime.utcnow()

        db.session.flush()
        return slot

    @staticmethod
    def release_slot(slot_id, partner_id, service_type=SLOT_TYPE_COLLECTION):
        slot = SchedulingService._get_slot_for_partner(partner_id, slot_id)

        if slot.booked_count > 0:
            slot.booked_count -= 1
        SchedulingService._refresh_slot_status(slot)

        capacity = SchedulingService.get_or_create_partner_capacity(
            partner_id,
            slot.slot_date,
            service_type,
        )
        if capacity.booked_count > 0:
            capacity.booked_count -= 1
        capacity.remaining_capacity = max(0, capacity.maximum_capacity - capacity.booked_count)
        capacity.updated_at = datetime.utcnow()

        db.session.flush()
        return slot
