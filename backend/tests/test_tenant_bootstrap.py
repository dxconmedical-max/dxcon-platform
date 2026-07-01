import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.models.enterprise_platform import EnterpriseTenant
from app.models.user import User
from scripts.uat_tenant_lib import UAT, bootstrap_tenant, reset_staging_data


class TenantBootstrapTestCase(unittest.TestCase):
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

    def test_bootstrap_creates_tenant_and_users(self):
        result = bootstrap_tenant()
        self.assertEqual(result["tenant_code"], UAT["tenant_code"])
        tenant = EnterpriseTenant.query.filter_by(tenant_code=UAT["tenant_code"]).first()
        self.assertIsNotNone(tenant)
        admin = User.query.filter_by(email=UAT["admin_email"]).first()
        self.assertIsNotNone(admin)
        self.assertEqual(admin.role, "ADMIN")


if __name__ == "__main__":
    unittest.main()
