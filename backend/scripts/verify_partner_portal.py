import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.models.partner import Partner
from scripts.seed_marketplace_demo import seed_marketplace_demo
from scripts.seed_partner_portal_demo import seed_partner_portal_demo
from scripts.seed_scheduling_demo import seed_scheduling_demo


def verify_routes(app):
    routes = {str(rule) for rule in app.url_map.iter_rules()}
    required = [
        "/api/v1/partner-portal/dashboard",
        "/api/v1/partner-portal/orders",
        "/api/v1/partner-portal/results/upload",
        "/api/v1/partner-portal/revenue",
        "/api/v1/partner-portal/sla",
        "/partner-portal",
        "/partner-portal/orders",
        "/partner-portal/results",
        "/partner-portal/revenue",
        "/partner-portal/sla",
    ]
    for route in required:
        if route in routes:
            print("OK:", route)
        else:
            print("MISSING:", route)
            return False
    return True


def verify_seed_and_flow():
    with app.app_context():
        db.create_all()
        seed_marketplace_demo()
        seed_scheduling_demo()
        summary = seed_partner_portal_demo()
        if summary["orders_created"] < 1:
            print("MISSING: partner portal demo orders")
            return False
        print("OK: partner portal demo seed")
        partner = Partner.query.first()
        if not partner:
            print("MISSING: partner")
            return False
        print("OK: partner portal flow")
        return True


app = create_app()
print("\n=== DXCON PARTNER PORTAL VERIFY ===\n")
errors = 0
if not verify_routes(app):
    errors += 1
if not verify_seed_and_flow():
    errors += 1
if errors:
    print("\nFAILED:", errors, "issue(s)")
    sys.exit(1)
print("\nPARTNER PORTAL VERIFY PASSED\n")
