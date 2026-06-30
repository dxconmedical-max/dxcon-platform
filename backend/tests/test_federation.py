import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["FEDERATION_SEED_LABS"] = "5"
os.environ["FEDERATION_SEED_BRANCHES"] = "8"
os.environ["FEDERATION_SEED_CAPABILITIES"] = "15"

from app import create_app
from app.extensions.db import db
from app.models.federation_core import FederatedLab, FederationProvider
from app.services.federation_service import FederationService
from scripts.seed_federation_demo import seed_federation_demo


class FederationTestCase(unittest.TestCase):
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

    def test_federation_apis(self):
        labs = self.client.get("/api/v1/federation/labs")
        self.assertEqual(labs.status_code, 200)
        self.assertGreaterEqual(labs.get_json()["total"], 1)

        lab_id = labs.get_json()["labs"][0]["id"]
        detail = self.client.get(f"/api/v1/federation/labs/{lab_id}")
        self.assertEqual(detail.status_code, 200)

        connect = self.client.post(f"/api/v1/federation/labs/{lab_id}/connect")
        self.assertEqual(connect.status_code, 200)
        self.assertEqual(connect.get_json()["lab"]["connection_status"], "CONNECTED")

        disconnect = self.client.post(f"/api/v1/federation/labs/{lab_id}/disconnect")
        self.assertEqual(disconnect.status_code, 200)

        create_lab = self.client.post(
            "/api/v1/federation/labs",
            json={"name": "New Lab", "city": "Hanoi"},
        )
        self.assertEqual(create_lab.status_code, 201)

        providers = self.client.get("/api/v1/federation/providers")
        self.assertEqual(providers.status_code, 200)

        create_provider = self.client.post(
            "/api/v1/federation/providers",
            json={"name": "New Provider"},
        )
        self.assertEqual(create_provider.status_code, 201)

    def test_federation_services(self):
        provider = FederationProvider.query.first()
        lab = FederationService.create_lab({"name": "Service Lab", "provider_id": provider.id})
        self.assertIsNotNone(FederatedLab.query.get(lab.id))
        FederationService.connect_lab(lab.id)
        payload = FederationService.get_lab(lab.id)
        self.assertEqual(payload["connection_status"], "CONNECTED")


if __name__ == "__main__":
    unittest.main()
