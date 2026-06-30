import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["FEDERATION_SEED_LABS"] = "6"
os.environ["FEDERATION_SEED_FAILOVER"] = "3"

from app import create_app
from app.extensions.db import db
from app.models.federation_core import FederatedLab
from app.models.federation_failover import FailoverEvent
from app.services.federation_failover_service import FailoverService
from scripts.seed_federation_demo import seed_federation_demo


class FederationFailoverTestCase(unittest.TestCase):
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

    def test_failover_apis(self):
        lab = FederatedLab.query.filter_by(status="OFFLINE").first()
        if not lab:
            lab = FederatedLab.query.first()
            lab.status = "OFFLINE"
            lab.connection_status = "DISCONNECTED"
            db.session.commit()

        check = self.client.post(
            "/api/v1/federation/failover/check",
            json={"federated_lab_id": lab.id, "holiday_mode": True, "sla_timeout": True},
        )
        self.assertEqual(check.status_code, 200)
        self.assertGreater(check.get_json()["events_triggered"], 0)

        events = self.client.get("/api/v1/federation/failover/events")
        self.assertEqual(events.status_code, 200)
        self.assertGreater(events.get_json()["total"], 0)

    def test_failover_service(self):
        lab = FederatedLab.query.first()
        lab.status = "OFFLINE"
        db.session.commit()
        result = FailoverService.check({"federated_lab_id": lab.id})
        self.assertGreater(result["events_triggered"], 0)
        self.assertGreater(FailoverEvent.query.count(), 0)


if __name__ == "__main__":
    unittest.main()
