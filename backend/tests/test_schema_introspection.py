import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"


class SchemaIntrospectionTestCase(unittest.TestCase):
    def test_patient_model_matches_database_primary_key(self):
        from app import create_app
        from app.extensions.db import db
        from app.infrastructure.schema_introspection import compare_model_to_database
        from app.models.patient import Patient

        app = create_app()
        app.config["TESTING"] = True
        with app.app_context():
            db.create_all()
            report = compare_model_to_database(Patient)
        self.assertEqual(report["model_primary_key"], ["patient_code"])
        self.assertTrue(report["primary_key_match"])
        self.assertTrue(report["compatible"])

    def test_schema_compatibility_report_lists_changed_models(self):
        from app import create_app
        from app.infrastructure.schema_introspection import (
            MODEL_SYNC_CHANGES,
            build_schema_compatibility_report,
        )

        app = create_app()
        app.config["TESTING"] = True
        with app.app_context():
            report = build_schema_compatibility_report()
        self.assertGreaterEqual(report["summary"]["models_changed_for_production_schema"], 1)
        changed = {item["model"] for item in MODEL_SYNC_CHANGES}
        self.assertIn("Patient", changed)
        self.assertIn("PatientProfile", changed)


if __name__ == "__main__":
    unittest.main()
