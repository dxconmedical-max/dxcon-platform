import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app
from app.core.statuses import MARKETPLACE_VISIBLE_PARTNER_STATUSES
from app.extensions.db import db
from app.models.driver import Driver
from app.models.partner import Partner
from app.models.partner_operating_hour import PartnerOperatingHour
from app.models.scheduling_calendar import SchedulingCalendar
from app.services.scheduling import SchedulingService
from app.services.slot_generation import SlotGenerationService


DEMO_COLLECTORS = [
    ("COL-001", "Nguyen Van Collector", "0909111222", "51A-12345", "Ha Noi", "Cau Giay"),
    ("COL-002", "Tran Thi Collector", "0909333444", "51B-67890", "Ho Chi Minh", "District 3"),
    ("COL-003", "Le Van Collector", "0909555666", "43C-24680", "Da Nang", "Hai Chau"),
]


def _ensure_collectors():
    created = 0
    collectors = []

    for code, name, phone, vehicle, city, district in DEMO_COLLECTORS:
        driver = Driver.query.filter_by(driver_code=code).first()
        if not driver:
            driver = Driver(
                driver_code=code,
                full_name=name,
                phone=phone,
                vehicle_no=vehicle,
                status="ACTIVE",
            )
            db.session.add(driver)
            created += 1
        collectors.append((driver, city, district))

    db.session.commit()
    return collectors, created


def _ensure_operating_hours(partners):
    created = 0
    for partner in partners:
        existing = PartnerOperatingHour.query.filter_by(partner_id=partner.id).count()
        if existing:
            continue

        for day in range(0, 6):
            db.session.add(
                PartnerOperatingHour(
                    partner_id=partner.id,
                    day_of_week=day,
                    open_time="08:00",
                    close_time="17:00",
                    is_closed=False,
                )
            )
            created += 1

    db.session.commit()
    return created


def seed_scheduling_demo():
    partners = Partner.query.filter(
        Partner.status.in_(MARKETPLACE_VISIBLE_PARTNER_STATUSES)
    ).limit(3).all()

    if not partners:
        return {
            "partners_total": 0,
            "calendars_created": 0,
            "slots_created": 0,
            "collector_records_created": 0,
            "operating_hours_created": 0,
            "collectors_created": 0,
        }

    operating_hours_created = _ensure_operating_hours(partners)
    calendars_created = 0
    slots_created = 0

    start_date = datetime.utcnow().strftime("%Y-%m-%d")
    for partner in partners:
        before = SchedulingCalendar.query.filter_by(owner_id=partner.id).count()
        SchedulingService.get_or_create_partner_calendar(partner.id)
        after = SchedulingCalendar.query.filter_by(owner_id=partner.id).count()
        if after > before:
            calendars_created += 1

        slots_created += SlotGenerationService.generate_partner_daily_slots(
            partner.id,
            days=7,
            start_date=start_date,
        )

    collectors, collectors_created = _ensure_collectors()
    collector_records_created = 0
    for driver, city, district in collectors:
        collector_records_created += SlotGenerationService.generate_collector_availability(
            driver.id,
            days=7,
            city=city,
            district=district,
            start_date=start_date,
        )

    return {
        "partners_total": len(partners),
        "calendars_created": calendars_created,
        "slots_created": slots_created,
        "collector_records_created": collector_records_created,
        "operating_hours_created": operating_hours_created,
        "collectors_created": collectors_created,
    }


def main():
    app = create_app()

    with app.app_context():
        db.create_all()
        summary = seed_scheduling_demo()

        print("\n=== DXCON SCHEDULING DEMO SEED ===\n")
        for key, value in summary.items():
            print(f"{key}: {value}")
        print("\nSCHEDULING DEMO SEED COMPLETE\n")


if __name__ == "__main__":
    main()
