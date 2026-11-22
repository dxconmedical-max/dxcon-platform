import os
import sys
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from flask_jwt_extended import create_access_token

from app import create_app
from app.core.passwords import hash_password
from app.extensions.db import db
from app.models.user import User
from app.services import live_location_store as store


def _headers(role):
    user = User(
        email=f"ll-{role.lower()}-{uuid.uuid4().hex[:8]}@test.local",
        role=role,
        password_hash=hash_password("Password123!"),
        is_active=True,
    )
    db.session.add(user)
    db.session.commit()
    token = create_access_token(
        identity=user.id,
        additional_claims={"role": user.role, "email": user.email},
    )
    return {"Authorization": f"Bearer {token}"}, user


class LiveLocationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["REDIS_URL"] = ""
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        store.clear_memory()

    def tearDown(self):
        store.clear_memory()
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_collector_ping_then_super_admin_sees_it(self):
        ch, collector = _headers("COLLECTOR")
        res = self.client.post(
            "/api/v1/live-location/ping",
            json={"latitude": 10.78, "longitude": 106.7, "accuracy_m": 12},
            headers=ch,
        )
        self.assertEqual(res.status_code, 200)
        ah, _ = _headers("SUPER_ADMIN")
        res = self.client.get("/api/v1/live-location/collectors", headers=ah)
        self.assertEqual(res.status_code, 200)
        items = res.get_json()["collectors"]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["email"], collector.email)
        self.assertAlmostEqual(items[0]["latitude"], 10.78)

    def test_invalid_coordinates_rejected(self):
        ch, _ = _headers("COLLECTOR")
        for body in (
            {"latitude": 91, "longitude": 106},
            {"latitude": 10, "longitude": 181},
            {"latitude": "abc", "longitude": 106},
            {"latitude": float("nan"), "longitude": 106},
            {},
        ):
            res = self.client.post("/api/v1/live-location/ping", json=body, headers=ch)
            self.assertEqual(res.status_code, 400, body)

    def test_stop_removes_position(self):
        ch, _ = _headers("COLLECTOR")
        self.client.post(
            "/api/v1/live-location/ping", json={"latitude": 10, "longitude": 106}, headers=ch
        )
        self.client.delete("/api/v1/live-location/ping", headers=ch)
        ah, _ = _headers("SUPER_ADMIN")
        res = self.client.get("/api/v1/live-location/collectors", headers=ah)
        self.assertEqual(res.get_json()["collectors"], [])

    def test_only_collectors_can_send_and_only_staff_can_view(self):
        dh, _ = _headers("DOCTOR")
        res = self.client.post(
            "/api/v1/live-location/ping", json={"latitude": 10, "longitude": 106}, headers=dh
        )
        self.assertEqual(res.status_code, 403)
        ch, _ = _headers("COLLECTOR")
        self.assertEqual(
            self.client.get("/api/v1/live-location/collectors", headers=ch).status_code, 403
        )
        self.assertEqual(
            self.client.get("/api/v1/live-location/collectors", headers=dh).status_code, 403
        )

    def test_admin_without_internal_org_is_denied(self):
        ah, _ = _headers("ADMIN")
        res = self.client.get("/api/v1/live-location/collectors", headers=ah)
        self.assertEqual(res.status_code, 403)

    def test_requires_login(self):
        self.assertIn(
            self.client.get("/api/v1/live-location/collectors").status_code, (401, 403)
        )


if __name__ == "__main__":
    unittest.main()
