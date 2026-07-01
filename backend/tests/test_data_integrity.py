import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from scripts.go_live_rc1_lib import find_duplicate_routes, verify_data_integrity


class DataIntegrityTestCase(unittest.TestCase):
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

    def test_no_duplicate_routes(self):
        duplicates = find_duplicate_routes(self.app)
        self.assertEqual(len(duplicates), 0)

    def test_data_integrity_checks(self):
        result = verify_data_integrity(self.app)
        self.assertIn("checks", result)
        self.assertTrue(result["checks"]["duplicate_routes"]["ok"])
        self.assertTrue(result["checks"]["required_configuration"]["ok"])


if __name__ == "__main__":
    unittest.main()
