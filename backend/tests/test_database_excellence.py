import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"


class DatabaseExcellenceTestCase(unittest.TestCase):
    def test_database_review_report(self):
        from scripts.database_excellence_lib import run_database_review
        from scripts.enterprise_master_lib import create_test_app

        app, db = create_test_app()
        report = run_database_review(app, db)
        self.assertTrue(report["checks"]["model_inventory"]["ok"], report)
        self.assertTrue(report["checks"]["schema_metadata"]["ok"], report)

    def test_database_index_report(self):
        from scripts.database_excellence_lib import run_database_index_report
        from scripts.enterprise_master_lib import create_test_app

        app, db = create_test_app()
        report = run_database_index_report(app, db)
        self.assertTrue(report["ok"], report)

    def test_migration_validation(self):
        from scripts.database_excellence_lib import check_migration_validation
        from scripts.enterprise_master_lib import create_test_app

        app, db = create_test_app()
        result = check_migration_validation(app, db)
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["missing_core_tables"], [])

    def test_database_regression_create_all(self):
        from app import create_app
        from app.extensions.db import db
        from sqlalchemy import inspect

        app = create_app()
        app.config["TESTING"] = True
        with app.app_context():
            db.create_all()
            tables = inspect(db.engine).get_table_names()
            self.assertIn("users", tables)
            self.assertIn("orders", tables)
            self.assertGreaterEqual(len(tables), 100)


if __name__ == "__main__":
    unittest.main()
