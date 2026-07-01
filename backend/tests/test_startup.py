import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.database_startup import verify_database_connection, verify_migrations
from app.extensions.db import db
from app.models.user import User


class StartupTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_database_connection_retry(self):
        self.assertTrue(
            verify_database_connection(self.app, retries=2, delay_seconds=0)
        )

    def test_migration_verification(self):
        db.session.add(
            User(
                email="startup@test.local",
                role="ADMIN",
                password_hash="hash",
                is_active=True,
            )
        )
        db.session.commit()
        status = verify_migrations(self.app)
        self.assertIn("table_count", status)
        self.assertFalse(status["missing_core_tables"])

    def test_startup_flag_set(self):
        deployment = self.app.extensions.get("dxcon_deployment", {})
        self.assertTrue(deployment.get("startup_complete"))


if __name__ == "__main__":
    unittest.main()
