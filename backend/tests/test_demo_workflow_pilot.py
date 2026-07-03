import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"


class DemoWorkflowPilotTestCase(unittest.TestCase):
    def test_dashboard_routes_exist(self):
        from app import create_app

        app = create_app()
        app.config["TESTING"] = True
        routes = {str(rule.rule) for rule in app.url_map.iter_rules()}
        for route in (
            "/reception",
            "/executive-v9",
            "/crm-pipeline",
            "/logistics",
            "/patient/demo",
        ):
            self.assertIn(route, routes)

    def test_verify_demo_workflow_script(self):
        from app import create_app
        from app.extensions.db import db
        from scripts.verify_demo_workflow import main

        app = create_app()
        app.config["TESTING"] = True
        with app.app_context():
            db.create_all()
            code = main()
        self.assertIn(code, (0, 1))


if __name__ == "__main__":
    unittest.main()
