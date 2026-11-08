"""PATIENT logins must not read other people's reports through the staff lookup endpoints."""

import os
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_tmp = tempfile.NamedTemporaryFile(prefix="dxcon_ptclosed_", suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

PATHS = [
    "/api/v1/reporting-engine/patient/P-OTHER/reports",
    "/api/v1/lab-workspace/release/ORD-OTHER/html",
]


class PatientReportLookupClosedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import create_app
        from app.core.passwords import hash_password
        from app.extensions.db import db
        from app.models.user import User

        cls.app = create_app()
        cls.app.config["TESTING"] = True
        tag = uuid.uuid4().hex[:6]
        cls.users = {}
        with cls.app.app_context():
            db.create_all()
            for key, role in (("patient", "PATIENT"), ("admin", "ADMIN")):
                email = f"{key}-{tag}@placeholder.dxcon.test"
                user = User(email=email, role=role, password_hash=hash_password("Str0ng-pass-123"), is_active=True)
                db.session.add(user)
                db.session.flush()
                cls.users[key] = (user.id, email, role)
            db.session.commit()

    def _client(self, key):
        client = self.app.test_client()
        uid, email, role = self.users[key]
        with client.session_transaction() as s:
            s["user_id"], s["role"], s["email"] = uid, role, email
        return client

    def test_patient_login_is_denied(self):
        client = self._client("patient")
        for path in PATHS:
            self.assertEqual(client.get(path).status_code, 403, path)

    def test_staff_admin_is_still_allowed(self):
        client = self._client("admin")
        for path in PATHS:
            self.assertNotIn(client.get(path).status_code, (401, 403), path)


if __name__ == "__main__":
    unittest.main()
