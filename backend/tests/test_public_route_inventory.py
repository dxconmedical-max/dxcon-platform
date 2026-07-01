import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from scripts.security_preflight_lib import PUBLIC_ROUTE_PREFIXES, inventory_public_routes


class PublicRouteInventoryTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True

    def test_public_inventory_contains_health_and_auth(self):
        report = inventory_public_routes(self.app)
        paths = {item["path"] for item in report["public_routes"]}
        self.assertIn("/api/v1/system/health", paths)
        self.assertIn("/api/v1/auth/login", paths)
        self.assertIn("/live", paths)

    def test_public_prefixes_documented(self):
        self.assertIn("/api/v1/auth/login", PUBLIC_ROUTE_PREFIXES)

    def test_inventory_counts(self):
        report = inventory_public_routes(self.app)
        self.assertGreater(report["public_count"], 5)
        self.assertGreater(report["protected_count"], 0)


if __name__ == "__main__":
    unittest.main()
