import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"


class EnterpriseHardeningTestCase(unittest.TestCase):
    def test_centralized_exceptions(self):
        from app.core.exceptions import ApiError, DxConError, NotFoundError

        err = NotFoundError("missing")
        self.assertIsInstance(err, ApiError)
        self.assertIsInstance(err, DxConError)
        self.assertEqual(err.status_code, 404)

    def test_architecture_consistency_report(self):
        from scripts.enterprise_hardening_lib import run_architecture_consistency_report

        report = run_architecture_consistency_report()
        self.assertTrue(report["ok"], report)

    def test_production_standard_report(self):
        from app import create_app
        from scripts.enterprise_hardening_lib import run_production_standard_report

        app = create_app()
        app.config["TESTING"] = True
        report = run_production_standard_report(app)
        self.assertTrue(report["ok"], report)


if __name__ == "__main__":
    unittest.main()
