from datetime import datetime, timedelta

from app.extensions.db import db
from app.models.partner_availability import PartnerAvailability


class PartnerAvailabilityService:

    DEFAULT_DAILY_CAPACITY = 50
    NEAR_FULL_THRESHOLD = 0.8

    TIME_SLOTS = [
        "08:00-10:00",
        "10:00-12:00",
        "13:00-15:00",
        "15:00-17:00",
    ]

    @staticmethod
    def _normalize_date(date_value=None):
        if date_value:
            return str(date_value)[:10]
        return datetime.utcnow().strftime("%Y-%m-%d")

    @staticmethod
    def _compute_next_available_time(date_value, booked_count, maximum_daily_capacity):
        if booked_count < maximum_daily_capacity:
            slot_index = min(booked_count, len(PartnerAvailabilityService.TIME_SLOTS) - 1)
            return f"{date_value} {PartnerAvailabilityService.TIME_SLOTS[slot_index]}"

        next_date = (
            datetime.strptime(date_value, "%Y-%m-%d") + timedelta(days=1)
        ).strftime("%Y-%m-%d")
        return f"{next_date} {PartnerAvailabilityService.TIME_SLOTS[0]}"

    @staticmethod
    def refresh_availability(availability):
        availability.available_slots = max(
            0,
            availability.maximum_daily_capacity - availability.booked_count,
        )
        availability.next_available_time = PartnerAvailabilityService._compute_next_available_time(
            availability.date,
            availability.booked_count,
            availability.maximum_daily_capacity,
        )
        availability.updated_at = datetime.utcnow()
        return availability

    @staticmethod
    def get_or_create(partner_id, date_value=None, maximum_daily_capacity=None):
        date_key = PartnerAvailabilityService._normalize_date(date_value)
        capacity = maximum_daily_capacity or PartnerAvailabilityService.DEFAULT_DAILY_CAPACITY

        availability = PartnerAvailability.query.filter_by(
            partner_id=partner_id,
            date=date_key,
        ).first()

        if not availability:
            availability = PartnerAvailability(
                partner_id=partner_id,
                date=date_key,
                maximum_daily_capacity=capacity,
                booked_count=0,
            )
            db.session.add(availability)

        PartnerAvailabilityService.refresh_availability(availability)
        return availability

    @staticmethod
    def get_availability(partner_id, date_value=None):
        date_key = PartnerAvailabilityService._normalize_date(date_value)
        availability = PartnerAvailability.query.filter_by(
            partner_id=partner_id,
            date=date_key,
        ).first()
        return availability

    @staticmethod
    def reserve_slot(partner_id, date_value=None):
        availability = PartnerAvailabilityService.get_or_create(partner_id, date_value)
        availability.booked_count += 1
        PartnerAvailabilityService.refresh_availability(availability)
        db.session.flush()
        return availability

    @staticmethod
    def capacity_utilization(availability):
        if not availability or availability.maximum_daily_capacity <= 0:
            return 0.0
        return availability.booked_count / availability.maximum_daily_capacity

    @staticmethod
    def ranking_penalty(availability):
        utilization = PartnerAvailabilityService.capacity_utilization(availability)
        if utilization < PartnerAvailabilityService.NEAR_FULL_THRESHOLD:
            return 0.0

        overload = min(1.0, (utilization - PartnerAvailabilityService.NEAR_FULL_THRESHOLD) / 0.2)
        return round(overload * 5.0, 2)
