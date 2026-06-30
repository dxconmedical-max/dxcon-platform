import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["FEDERATION_SEED_LABS"] = "8"
os.environ["FEDERATION_SEED_CAPABILITIES"] = "24"
os.environ["FEDERATION_SEED_ROUTING"] = "5"

from app import create_app
from app.extensions.db import db
from app.models.federation_core import FederatedLab
from app.services.federation_routing_service import RoutingScoreService, SmartRoutingService
from scripts.seed_federation_demo import seed_federation_demo


class FederationRoutingTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        seed_federation_demo()
        for lab in FederatedLab.query.all():
            lab.status = "ONLINE"
            lab.connection_status = "CONNECTED"
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_routing_apis(self):
        route = self.client.post(
            "/api/v1/federation/route",
            json={
                "test_code": "GLU",
                "origin_latitude": 10.8,
                "origin_longitude": 106.7,
                "request_ref": "REQ-TEST-001",
            },
        )
        self.assertEqual(route.status_code, 200)
        payload = route.get_json()
        self.assertIn("selected_lab", payload)
        self.assertIn("score_total", payload["selected_lab"])

        decisions = self.client.get("/api/v1/federation/routing-decisions")
        self.assertEqual(decisions.status_code, 200)
        self.assertGreater(decisions.get_json()["total"], 0)

        audit = self.client.get("/api/v1/federation/routing-audit")
        self.assertEqual(audit.status_code, 200)

    def test_routing_score_service(self):
        lab = FederatedLab.query.filter_by(status="ONLINE").first()
        score = RoutingScoreService.score_lab(
            lab,
            {"test_code": "GLU", "origin_latitude": 10.8, "origin_longitude": 106.7},
        )
        self.assertGreater(score["score_total"], 0)
        self.assertIn("distance", score["score_breakdown"])

        result = SmartRoutingService.route(
            {"test_code": "GLU", "origin_latitude": 10.8, "origin_longitude": 106.7}
        )
        self.assertIsNotNone(result["decision"]["selected_lab_id"])


if __name__ == "__main__":
    unittest.main()
