import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["FEDERATION_SEED_LABS"] = "5"
os.environ["FEDERATION_SEED_CAPABILITIES"] = "10"

from app import create_app
from app.extensions.db import db
from app.models.federation_capacity import CapacitySnapshot
from app.services.federation_capacity_service import CapacityCalculatorService, CapacityService
from scripts.seed_federation_demo import seed_federation_demo


class FederationCapacityTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        seed_federation_demo()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_capacity_apis(self):
        capacity = self.client.get("/api/v1/federation/capacity")
        self.assertEqual(capacity.status_code, 200)
        self.assertGreater(capacity.get_json()["labs_total"], 0)

        lab_id = capacity.get_json()["labs"][0]["federated_lab_id"]
        update = self.client.post(
            "/api/v1/federation/capacity/update",
            json={"federated_lab_id": lab_id, "used_capacity": 120},
        )
        self.assertEqual(update.status_code, 200)
        self.assertIn("snapshot", update.get_json())

        history = self.client.get(f"/api/v1/federation/capacity/history?lab_id={lab_id}")
        self.assertEqual(history.status_code, 200)
        self.assertGreaterEqual(history.get_json()["total"], 1)

    def test_capacity_calculator(self):
        lab_id = CapacitySnapshot.query.first().federated_lab_id
        calc = CapacityCalculatorService.calculate_for_lab(lab_id)
        self.assertIn("remaining_capacity", calc)
        self.assertGreater(calc["total_capacity"], 0)
        summary = CapacityService.get_capacity(lab_id)
        self.assertEqual(summary["federated_lab_id"], lab_id)


if __name__ == "__main__":
    unittest.main()
