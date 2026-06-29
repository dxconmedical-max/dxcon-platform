import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.models.company import Company
from app.models.integration_message import IntegrationMessage
from app.services.integration_service import IntegrationGatewayService
from scripts.seed_integrations_demo import seed_integrations_demo


def verify_routes(app):
    routes = {str(rule) for rule in app.url_map.iter_rules()}
    required = [
        "/api/v1/integrations/connections",
        "/api/v1/integrations/lis/orders",
        "/api/v1/integrations/lis/results",
        "/api/v1/integrations/his/patients",
        "/api/v1/integrations/messages",
        "/api/v1/integrations/audit",
        "/integrations",
        "/integrations/connections",
        "/integrations/messages",
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
        if not Company.query.first():
            db.session.add(Company(company_code="DX-INT", company_name="DxCon", tax_code="01"))
            db.session.commit()
        demo = seed_integrations_demo()
        if not demo.get("connection_id"):
            print("MISSING: integrations demo flow")
            return False
        print("OK: integrations demo seed")

        connections = IntegrationGatewayService.list_connections()
        if connections["count"] < 1:
            print("MISSING: integration connections")
            return False
        print("OK: integration connections")

        messages = IntegrationGatewayService.list_messages()
        if messages["count"] < 1:
            print("MISSING: integration messages")
            return False
        print("OK: integration messages")

        if IntegrationMessage.query.count() < 1:
            print("MISSING: integration message records")
            return False
        print("OK: integration message records")
        return True


app = create_app()
print("\n=== DXCON INTEGRATIONS VERIFY ===\n")
errors = 0
if not verify_routes(app):
    errors += 1
if not verify_seed_and_flow():
    errors += 1
if errors:
    print("\nFAILED:", errors, "issue(s)")
    sys.exit(1)
print("\nINTEGRATIONS VERIFY PASSED\n")
