import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.models.critical_value_rule import CriticalValueRule
from app.models.reference_range import ReferenceRange


def seed_smoke():
    db.session.add(
        ReferenceRange(
            test_code="GLU",
            test_name="Glucose",
            sex="ALL",
            age_min=0,
            age_max=120,
            low_value=70,
            high_value=100,
            status="ACTIVE",
        )
    )
    db.session.add(
        CriticalValueRule(
            rule_code="CRIT-GLU-SMOKE",
            test_code="GLU",
            panic_low=40,
            panic_high=400,
            message_en="Critical glucose",
            status="ACTIVE",
        )
    )
    db.session.commit()


def smoke_test():
    with app.app_context():
        db.create_all()
        seed_smoke()
        steps = [
            ("GET reference-ranges", "get", "/api/v1/ai/reference-ranges", None),
            (
                "POST interpret",
                "post",
                "/api/v1/ai/interpret",
                {
                    "items": [{"test_code": "GLU", "test_name": "Glucose", "result_value": "180"}],
                },
            ),
            (
                "POST risk",
                "post",
                "/api/v1/ai/risk",
                {"items": [{"test_code": "GLU", "result_value": "140"}, {"test_code": "HBA1C", "result_value": "7.0"}]},
            ),
            (
                "POST recommend",
                "post",
                "/api/v1/ai/recommend",
                {"items": [{"test_code": "GLU", "test_name": "Glucose", "result_value": "180"}]},
            ),
            (
                "POST critical-results",
                "post",
                "/api/v1/ai/critical-results",
                {
                    "items": [{"test_code": "GLU", "result_value": "450"}],
                    "repeated_abnormality": True,
                },
            ),
            ("GET dashboard", "get", "/ai", None),
            ("GET interpreter", "get", "/ai/interpreter", None),
            ("GET risk page", "get", "/ai/risk", None),
            ("GET critical page", "get", "/ai/critical", None),
        ]
        for label, method, path, payload in steps:
            if method == "get":
                response = client.get(path)
            else:
                response = client.post(path, json=payload or {})
            if response.status_code >= 400:
                print("FAIL:", label, response.status_code, response.get_data(as_text=True)[:200])
                return False
            print("OK:", label, response.status_code)
        return True


app = create_app()
app.config["TESTING"] = True
client = app.test_client()
print("\n=== DXCON AI CDS SMOKE TEST ===\n")
if not smoke_test():
    print("\nAI CDS SMOKE TEST FAILED\n")
    sys.exit(1)
print("\nAI CDS SMOKE TEST PASSED\n")
