import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.models.diagnostic_category import DiagnosticCategory
from app.models.diagnostic_service import DiagnosticService
from app.models.marketplace_booking import MarketplaceBooking
from app.models.marketplace_booking_timeline import MarketplaceBookingTimeline
from app.models.partner_availability import PartnerAvailability
from app.models.partner_service_mapping import PartnerServiceMapping
from app.models.service_package import ServicePackage
from app.services.marketplace_booking import MarketplaceBookingService
from scripts.seed_marketplace_demo import seed_marketplace_demo


def verify_models_import():
    models = [
        DiagnosticCategory,
        DiagnosticService,
        ServicePackage,
        PartnerServiceMapping,
        MarketplaceBooking,
        PartnerAvailability,
        MarketplaceBookingTimeline,
    ]
    for model in models:
        assert model.__tablename__
    print("OK: marketplace models import")


def verify_routes(app):
    routes = {str(rule) for rule in app.url_map.iter_rules()}
    required = [
        "/api/v1/marketplace/search",
        "/api/v1/marketplace/bookings",
        "/api/v1/marketplace/bookings/<booking_id>/transition",
        "/api/v1/marketplace/bookings/<booking_id>/timeline",
        "/marketplace",
        "/marketplace/bookings",
    ]

    for route in required:
        if route in routes:
            print("OK:", route)
        else:
            print("MISSING:", route)
            return False

    detail_found = any(
        rule.rule.startswith("/marketplace/bookings/<booking_id>")
        for rule in app.url_map.iter_rules()
    )
    if detail_found:
        print("OK: /marketplace/bookings/<booking_id>")
    else:
        print("MISSING: booking detail route")
        return False

    booking_detail_api = "/api/v1/marketplace/bookings/<booking_id>" in routes
    if booking_detail_api:
        print("OK: /api/v1/marketplace/bookings/<booking_id>")
    else:
        print("MISSING: booking detail API")
        return False

    return True


def verify_seed_and_booking_flow():
    with app.app_context():
        db.create_all()
        summary = seed_marketplace_demo()

        if summary["categories_total"] < 10:
            print("MISSING: expected at least 10 categories")
            return False
        print("OK: seeded categories")

        if summary["services_total"] < 100:
            print("MISSING: expected at least 100 services")
            return False
        print("OK: seeded services")

        if summary["packages_total"] < 10:
            print("MISSING: expected at least 10 packages")
            return False
        print("OK: seeded packages")

        if summary["mappings_total"] < 10:
            print("MISSING: expected partner service mappings")
            return False
        print("OK: seeded partner service mappings")

        if PartnerAvailability.query.count() < 1:
            print("MISSING: expected partner availability records")
            return False
        print("OK: seeded partner availability")

        mapping = PartnerServiceMapping.query.first()
        if not mapping:
            print("MISSING: mapping required for booking flow check")
            return False

        booking = MarketplaceBookingService.create_booking(
            {
                "partner_service_mapping_id": mapping.id,
                "patient_name": "Verify Patient",
                "patient_phone": "0900000000",
                "requested_date": "2026-06-26",
            }
        )
        timeline = MarketplaceBookingTimeline.query.filter_by(
            booking_id=booking.id,
            event_type="CREATED",
        ).first()
        if not timeline:
            print("MISSING: booking timeline CREATED event")
            return False
        print("OK: booking timeline CREATED event")

        return True


app = create_app()

print("\n=== DXCON MARKETPLACE VERIFY ===\n")

errors = 0

try:
    verify_models_import()
except Exception as exc:
    print("MISSING: marketplace models import", exc)
    errors += 1

if not verify_routes(app):
    errors += 1

if not verify_seed_and_booking_flow():
    errors += 1

if errors:
    print("\nFAILED:", errors, "issue(s)")
    sys.exit(1)

print("\nMARKETPLACE VERIFY PASSED\n")
