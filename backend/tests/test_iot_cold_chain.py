import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.models.cold_chain_alert import ColdChainAlert
from app.models.company import Company
from scripts.seed_iot_cold_chain_demo import seed_iot_cold_chain_demo


class IoTColdChainTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        from tests.p06_auth_helper import attach_admin_client
        attach_admin_client(self)
        db.session.add(Company(company_code="DX", company_name="DxCon", tax_code="01"))
        db.session.commit()
        self.demo = seed_iot_cold_chain_demo()
        self.device_id = self.demo["device_id"]
        from app.core.iot_device_auth import DEFAULT_IOT_DEVICE_INGEST_SECRET
        self.device_secret = DEFAULT_IOT_DEVICE_INGEST_SECRET

    def _device_headers(self, device_id: str):
        return {"X-Device-Id": device_id, "X-Device-Secret": self.device_secret}

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_iot_cold_chain_apis(self):
        devices = self.client.get("/api/v1/iot/devices")
        self.assertEqual(devices.status_code, 200)
        self.assertGreaterEqual(devices.get_json()["count"], 1)

        create = self.client.post(
            "/api/v1/iot/devices",
            json={
                "device_code": "IOT-COLD-TEST",
                "box_code": "BOX-TEST",
                "device_type": "COLD_BOX",
                "ingest_secret": self.device_secret,
            },
        )
        self.assertEqual(create.status_code, 201)
        test_device_id = create.get_json()["device"]["id"]

        temp = self.client.post(
            "/api/v1/iot/readings/temperature",
            headers=self._device_headers(test_device_id),
            json={"device_id": test_device_id, "celsius": 4.5, "event_id": "evt-temp-1"},
        )
        self.assertEqual(temp.status_code, 201)

        humidity = self.client.post(
            "/api/v1/iot/readings/humidity",
            headers=self._device_headers(test_device_id),
            json={"device_id": test_device_id, "humidity_percent": 50.0, "event_id": "evt-hum-1"},
        )
        self.assertEqual(humidity.status_code, 201)

        gps = self.client.post(
            "/api/v1/iot/readings/gps",
            headers=self._device_headers(test_device_id),
            json={"device_id": test_device_id, "latitude": 10.0, "longitude": 106.0, "event_id": "evt-gps-1"},
        )
        self.assertEqual(gps.status_code, 201)

        shock = self.client.post(
            "/api/v1/iot/readings/shock",
            headers=self._device_headers(test_device_id),
            json={"device_id": test_device_id, "g_force": 4.5, "event_id": "evt-shock-1"},
        )
        self.assertEqual(shock.status_code, 201)
        self.assertIn("alert", shock.get_json())

        alerts = self.client.get("/api/v1/iot/alerts")
        self.assertEqual(alerts.status_code, 200)
        self.assertGreaterEqual(alerts.get_json()["count"], 1)

        status = self.client.get("/api/v1/iot/cold-chain/status")
        self.assertEqual(status.status_code, 200)
        self.assertGreaterEqual(status.get_json()["count"], 1)
        self.assertGreaterEqual(ColdChainAlert.query.count(), 1)

    def test_iot_cold_chain_web_routes(self):
        routes = {str(r) for r in self.app.url_map.iter_rules()}
        for route in ["/iot", "/iot/devices", "/iot/cold-chain", "/iot/alerts"]:
            self.assertIn(route, routes)


if __name__ == "__main__":
    unittest.main()
