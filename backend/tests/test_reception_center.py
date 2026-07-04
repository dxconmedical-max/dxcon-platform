import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"


class ReceptionCenterTestCase(unittest.TestCase):
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
            email="demo-reception-01@demo.dxcon.test",
            role="RECEPTION",
            password_hash=hash_password("DemoPass123!"),
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()
        with self.client.session_transaction() as sess:
            sess["user_id"] = user.id
            sess["role"] = user.role
            sess["email"] = user.email

    def tearDown(self):
        from app.extensions.db import db

        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_reception_routes_registered(self):
        routes = {str(rule.rule) for rule in self.app.url_map.iter_rules()}
        for route in (
            "/reception",
            "/reception/search",
            "/reception/register/quick",
            "/reception/register/walk-in",
            "/reception/check-in",
            "/reception/activity",
            "/reception/kpi",
            "/api/v1/reception/dashboard",
        ):
            self.assertIn(route, routes)

    def test_reception_dashboard_requires_role_and_renders(self):
        response = self.client.get("/reception")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Reception Center", body)
        self.assertIn("Waiting Queue", body)

    def test_quick_registration_and_queue_number(self):
        from app.models.reception_queue_entry import ReceptionQueueEntry

        response = self.client.post(
            "/reception/register/quick",
            data={"full_name": "Test Patient", "phone": "0900111222", "gender": "M"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        entries = ReceptionQueueEntry.query.all()
        self.assertTrue(len(entries) >= 1)
        self.assertTrue(entries[0].queue_number.startswith("Q"))

    def test_patient_search(self):
        from app.extensions.db import db
        from app.models.patient import Patient

        db.session.add(
            Patient(
                patient_code="RC-TEST-001",
                full_name="Search Me",
                phone="0900333444",
                national_id="999888777",
            )
        )
        db.session.commit()
        response = self.client.get("/reception/search?name=Search")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Search Me", response.get_data(as_text=True))

    def test_walk_in_and_check_in_out(self):
        from app.extensions.db import db
        from app.models.patient import Patient
        from app.models.reception_queue_entry import ReceptionQueueEntry
        from app.services.reception_service import STATUS_CHECKED_IN, STATUS_CHECKED_OUT, create_queue_entry

        patient = Patient(patient_code="WI-TEST-001", full_name="Walk In", phone="0900555666")
        db.session.add(patient)
        db.session.commit()
        entry = create_queue_entry(patient.patient_code, actor_email="test@demo.dxcon.test")
        db.session.commit()
        response = self.client.post(f"/reception/queue/{entry.id}/check-in", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        updated = ReceptionQueueEntry.query.get(entry.id)
        self.assertEqual(updated.status, STATUS_CHECKED_IN)
        response = self.client.post(f"/reception/queue/{entry.id}/check-out", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        updated = ReceptionQueueEntry.query.get(entry.id)
        self.assertEqual(updated.status, STATUS_CHECKED_OUT)

    def test_reception_api_dashboard(self):
        response = self.client.get("/api/v1/reception/dashboard")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("kpis", payload)


if __name__ == "__main__":
    unittest.main()
