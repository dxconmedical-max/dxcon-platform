from datetime import datetime, timedelta

from app.core.statuses import (
    COLLECTOR_AVAILABLE,
    SLOT_AVAILABLE,
    SLOT_TYPE_COLLECTION,
)
from app.extensions.db import db
from app.models.collector_availability import CollectorAvailability
from app.models.partner_operating_hour import PartnerOperatingHour
from app.models.scheduling_slot import SchedulingSlot
from app.services.scheduling import SchedulingService


class SlotGenerationService:

    DEFAULT_WINDOWS = [
        ("08:00", "10:00"),
        ("10:00", "12:00"),
        ("13:00", "15:00"),
        ("15:00", "17:00"),
    ]

    @staticmethod
    def _operating_windows(partner_id, slot_date):
        day_of_week = datetime.strptime(slot_date, "%Y-%m-%d").weekday()
        hours = PartnerOperatingHour.query.filter_by(
            partner_id=partner_id,
            day_of_week=day_of_week,
            is_closed=False,
        ).all()

        if not hours:
            return SlotGenerationService.DEFAULT_WINDOWS

        windows = []
        for item in hours:
            open_time = item.open_time or "08:00"
            close_time = item.close_time or "17:00"
            windows.append((open_time, close_time))
        return windows

    @staticmethod
    def generate_partner_daily_slots(
        partner_id,
        days=7,
        slot_type=SLOT_TYPE_COLLECTION,
        slot_capacity=5,
        start_date=None,
    ):
        calendar = SchedulingService.get_or_create_partner_calendar(partner_id)
        start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else datetime.utcnow()
        created = 0

        for offset in range(days):
            slot_date = (start + timedelta(days=offset)).strftime("%Y-%m-%d")
            SchedulingService.get_or_create_partner_capacity(
                partner_id,
                slot_date,
                slot_type,
            )

            for start_time, end_time in SlotGenerationService._operating_windows(
                partner_id,
                slot_date,
            ):
                existing = SchedulingSlot.query.filter_by(
                    calendar_id=calendar.id,
                    slot_date=slot_date,
                    start_time=start_time,
                    end_time=end_time,
                    slot_type=slot_type,
                ).first()
                if existing:
                    continue

                db.session.add(
                    SchedulingSlot(
                        calendar_id=calendar.id,
                        slot_date=slot_date,
                        start_time=start_time,
                        end_time=end_time,
                        slot_type=slot_type,
                        capacity=slot_capacity,
                        booked_count=0,
                        status=SLOT_AVAILABLE,
                    )
                )
                created += 1

        db.session.commit()
        return created

    @staticmethod
    def generate_collector_availability(
        collector_id,
        days=7,
        city=None,
        district=None,
        max_jobs=8,
        start_date=None,
    ):
        start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else datetime.utcnow()
        created = 0

        for offset in range(days):
            slot_date = (start + timedelta(days=offset)).strftime("%Y-%m-%d")
            for start_time, end_time in SlotGenerationService.DEFAULT_WINDOWS[:2]:
                existing = CollectorAvailability.query.filter_by(
                    collector_id=collector_id,
                    date=slot_date,
                    start_time=start_time,
                    end_time=end_time,
                ).first()
                if existing:
                    continue

                db.session.add(
                    CollectorAvailability(
                        collector_id=collector_id,
                        date=slot_date,
                        start_time=start_time,
                        end_time=end_time,
                        city=city,
                        district=district,
                        status=COLLECTOR_AVAILABLE,
                        max_jobs=max_jobs,
                        assigned_jobs=0,
                    )
                )
                created += 1

        db.session.commit()
        return created
