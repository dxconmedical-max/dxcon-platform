import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"


class IoTLogisticsTestCase(unittest.TestCase):
    def setUp(self):
        from app import create_app
        from app.core.passwords import hash_password
        from app.extensions.db import db
        from app.models.user import User

        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()
        user = User(
            email="demo-collector-iot@demo.dxcon.test",
            role="COLLECTOR",
            password_hash=hash_password("DemoPass123!"),
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()
        with self.client.session_transaction() as sess:
            sess["user_id"] = user.id
            sess["role"] = user.role
            sess["email"] = user.email

        from app.services.iot_logistics_service import ensure_logistics

        ensure_logistics()
        devices = self.client.get("/api/v1/iot-logistics/devices").get_json()
        self.device_id = devices["devices"][0]["id"]

    def tearDown(self):
        from app.extensions.db import db

        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_iot_logistics_routes_registered(self):
        routes = {str(rule.rule) for rule in self.app.url_map.iter_rules()}
        for route in (
            "/iot-logistics",
            "/iot-logistics/devices",
            "/iot-logistics/ingest",
            "/api/v1/iot-logistics/dashboard",
            "/api/v1/iot-logistics/ingest",
        ):
            self.assertIn(route, routes)

    def test_dashboard_renders(self):
        response = self.client.get("/iot-logistics")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Logistics IoT Dashboard", response.get_data(as_text=True))

    def test_adapter_ingestion_and_timeline(self):
        response = self.client.post(
            "/api/v1/iot-logistics/ingest",
            json={
                "adapter_type": "GENERIC",
                "payload": {
                    "event_type": "TEMPERATURE",
                    "device_id": self.device_id,
                    "celsius": 4.5,
                },
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["ingested"])
        self.assertIn("chain_of_custody", payload)

        timeline = self.client.get(f"/api/v1/iot-logistics/timeline/{self.device_id}").get_json()
        self.assertGreaterEqual(timeline["count"], 1)

    def test_offline_buffer_sync(self):
        buffer_resp = self.client.post(
            "/api/v1/iot-logistics/ingest",
            json={
                "adapter_type": "DEMO_SENSOR",
                "offline": True,
                "payload": {
                    "type": "GPS",
                    "deviceId": self.device_id,
                    "lat": 10.5,
                    "lng": 106.5,
                    "offline": True,
                },
            },
        )
        self.assertEqual(buffer_resp.status_code, 200)
        self.assertTrue(buffer_resp.get_json()["buffered"])

        sync = self.client.post(
            "/api/v1/iot-logistics/offline-buffer/sync",
            json={"device_id": self.device_id},
        )
        self.assertEqual(sync.status_code, 200)
        self.assertGreaterEqual(sync.get_json()["synced_count"], 1)

    def test_device_health_and_breach(self):
        health = self.client.get(f"/api/v1/iot-logistics/device-health/{self.device_id}")
        self.assertEqual(health.status_code, 200)
        self.assertIn("health_score", health.get_json())

        breach = self.client.post(
            "/api/v1/iot-logistics/temperature-breach",
            json={"device_id": self.device_id, "celsius": 11.0},
        )
        self.assertEqual(breach.status_code, 200)
        self.assertTrue(breach.get_json()["breach"])


if __name__ == "__main__":
    unittest.main()
