import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from scripts.go_live_rc2_lib import (
    GENERATED_DIR,
    build_environment_matrix,
    build_production_cutover_checklist,
    build_rollback_checklist,
    validate_cutover,
)


class Rc2CutoverTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_cutover_validation(self):
        result = validate_cutover(self.app, self.client)
        self.assertGreaterEqual(result["passed"], 8)
        self.assertTrue(result["checks"]["health_probes"]["ok"])
        self.assertTrue(result["checks"]["no_duplicate_routes"]["ok"])

    def test_environment_matrix(self):
        matrix = build_environment_matrix()
        self.assertIn("variables", matrix)
        self.assertGreater(len(matrix["variables"]), 10)

    def test_cutover_checklist(self):
        cutover = {"ok": True, "checks": {"health_probes": {"ok": True}}}
        regression = {"ok": True, "domains": {"auth": {"ok": True}}}
        checklist = build_production_cutover_checklist(cutover, regression)
        self.assertTrue(checklist["ready"])

    def test_rollback_checklist(self):
        checklist = build_rollback_checklist()
        self.assertIn("previous_release_sha", checklist)
        self.assertIn("database_migration_warning", checklist)


if __name__ == "__main__":
    unittest.main()
