import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["DATABASE_URL"] = "sqlite:///:memory:"


class ApiExcellenceTestCase(unittest.TestCase):
    def setUp(self):
        from scripts.enterprise_master_lib import create_test_app
        from app.extensions.db import db

        self.app, self.db = create_test_app()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        from app.extensions.db import db

        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_api_review_report(self):
        from scripts.api_excellence_lib import run_api_review

        report = run_api_review(self.app)
        self.assertTrue(report["ok"], report)

    def test_openapi_validation(self):
        from scripts.api_excellence_lib import run_openapi_validation

        report = run_openapi_validation(self.app)
        self.assertTrue(report["ok"], report)

    def test_error_schema(self):
        from scripts.api_excellence_lib import check_error_schema

        result = check_error_schema(self.app)
        self.assertTrue(result["ok"], result)


if __name__ == "__main__":
    unittest.main()
