import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from scripts.security_preflight_lib import (
    check_jwt_cors_rate_limit,
    check_production_config_safety,
    run_security_preflight,
    scan_plaintext_secrets,
    verify_admin_route_protection,
)


class SecurityPreflightTestCase(unittest.TestCase):
    def test_plaintext_secret_scan(self):
        report = scan_plaintext_secrets()
        self.assertTrue(report["ok"], report)

    def test_production_debug_disabled(self):
        report = check_production_config_safety()
        self.assertTrue(report["debug_disabled"])
        self.assertTrue(report["ok"], report)

    def test_wildcard_cors_blocked(self):
        report = check_jwt_cors_rate_limit()
        self.assertTrue(report["wildcard_cors_blocked"])
        self.assertTrue(report["ok"], report)

    def test_full_preflight(self):
        app = create_app()
        app.config["TESTING"] = True
        result = run_security_preflight(app)
        self.assertTrue(result["ok"], result)


class AdminSecurityPreflightTestCase(unittest.TestCase):
    def test_admin_routes_reviewed(self):
        app = create_app()
        app.config["TESTING"] = True
        report = verify_admin_route_protection(app)
        self.assertTrue(report["ok"], report)


if __name__ == "__main__":
    unittest.main()
