import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["FEDERATION_SEED_LABS"] = "6"
os.environ["FEDERATION_SEED_CAPABILITIES"] = "12"

from app import create_app
from app.extensions.db import db
from app.models.federation_core import FederatedLab
from scripts.seed_federation_demo import seed_federation_demo


def smoke_test():
    with app.app_context():
        db.create_all()
        seed_federation_demo()
        lab = FederatedLab.query.first()

        steps = [
            ("GET labs", "get", "/api/v1/federation/labs", None),
            ("POST connect", "post", f"/api/v1/federation/labs/{lab.id}/connect", None),
            ("GET capacity", "get", "/api/v1/federation/capacity", None),
            ("POST route", "post", "/api/v1/federation/route", {"test_code": "GLU", "origin_latitude": 10.8, "origin_longitude": 106.7}),
            ("POST failover", "post", "/api/v1/federation/failover/check", {"federated_lab_id": lab.id}),
            ("GET dashboard", "get", "/federation", None),
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
print("\n=== DXCON FEDERATION SMOKE TEST ===\n")
if not smoke_test():
    print("\nFEDERATION SMOKE TEST FAILED\n")
    sys.exit(1)
print("\nFEDERATION SMOKE TEST PASSED\n")
