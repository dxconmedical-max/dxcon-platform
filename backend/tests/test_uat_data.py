import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from scripts.uat_tenant_lib import reseed_staging_data, reset_staging_data, verify_uat_data


class UatDataTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.rollback()
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_reseed_and_verify(self):
        summary = reseed_staging_data()
        self.assertGreaterEqual(summary["patients_created"], 0)
        self.assertGreaterEqual(summary["orders_created"], 3)
        result = verify_uat_data(self.app)
        self.assertTrue(result["ok"], result)

    def test_reset_clears_uat_patients(self):
        reseed_staging_data()
        reset_staging_data()
        result = verify_uat_data(self.app)
        self.assertFalse(result["checks"]["patients"]["ok"])


if __name__ == "__main__":
    unittest.main()
