import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"


class PilotReadinessTestCase(unittest.TestCase):
    def test_pilot_pages_registered(self):
        from app import create_app

        app = create_app()
        routes = {str(rule.rule) for rule in app.url_map.iter_rules()}
        for route in (
            "/demo-accounts",
            "/workflow-demo",
            "/pilot-checklist",
            "/doctor-workbench",
            "/patient-portal",
            "/executive-v9",
        ):
            self.assertIn(route, routes)

    def test_crm_and_logistics_do_not_500(self):
        from app import create_app
        from app.extensions.db import db

        app = create_app()
        app.config["TESTING"] = True
        with app.app_context():
            db.create_all()
            client = app.test_client()
            for route in ("/crm-pipeline", "/logistics"):
                response = client.get(route)
                self.assertEqual(response.status_code, 200, route)


if __name__ == "__main__":
    unittest.main()
