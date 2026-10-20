import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_tmp = tempfile.NamedTemporaryFile(prefix="dxcon_staff_", suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"


class StaffProfilesApiTests(unittest.TestCase):
    def setUp(self):
        from app import create_app
        from app.extensions.db import db

        self.app = create_app()
        self.app.config["TESTING"] = True
        with self.app.app_context():
            db.create_all()
        self.client = self.app.test_client()

    def test_registered(self):
        rules = {r.rule for r in self.app.url_map.iter_rules()}
        self.assertIn("/api/v1/staff-profiles", rules)
        self.assertIn("/api/v1/staff-profiles/<email>", rules)

    def test_anonymous_is_rejected(self):
        self.assertIn(self.client.get("/api/v1/staff-profiles").status_code, (401, 403))
        r = self.client.put("/api/v1/staff-profiles/a@b.vn", json={"full_name": "X"})
        self.assertIn(r.status_code, (401, 403))


if __name__ == "__main__":
    unittest.main()
