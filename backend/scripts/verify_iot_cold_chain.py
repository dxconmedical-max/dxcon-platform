import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.models.company import Company
from app.services.iot_cold_chain_service import ColdChainService, IoTDeviceService
from scripts.seed_iot_cold_chain_demo import seed_iot_cold_chain_demo


def verify_routes(app):
    routes = {str(rule) for rule in app.url_map.iter_rules()}
    required = [
        "/api/v1/iot/devices",
        "/api/v1/iot/readings/temperature",
        "/api/v1/iot/readings/humidity",
        "/api/v1/iot/readings/gps",
        "/api/v1/iot/readings/shock",
        "/api/v1/iot/alerts",
        "/api/v1/iot/cold-chain/status",
        "/iot",
        "/iot/devices",
        "/iot/cold-chain",
        "/iot/alerts",
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
            db.session.add(Company(company_code="DX-IOT", company_name="DxCon", tax_code="01"))
            db.session.commit()
        demo = seed_iot_cold_chain_demo()
        if not demo.get("device_id"):
            print("MISSING: iot cold chain demo flow")
            return False
        print("OK: iot cold chain demo seed")

        devices = IoTDeviceService.list_devices()
        if devices["count"] < 1:
            print("MISSING: iot devices")
            return False
        print("OK: iot devices")

        status = ColdChainService.get_status()
        if status["count"] < 1:
            print("MISSING: cold chain status")
            return False
        print("OK: cold chain status")
        return True


app = create_app()
print("\n=== DXCON IOT COLD CHAIN VERIFY ===\n")
errors = 0
if not verify_routes(app):
    errors += 1
if not verify_seed_and_flow():
    errors += 1
if errors:
    print("\nFAILED:", errors, "issue(s)")
    sys.exit(1)
print("\nIOT COLD CHAIN VERIFY PASSED\n")
