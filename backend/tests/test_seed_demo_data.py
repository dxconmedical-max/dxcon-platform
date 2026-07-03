import inspect
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"


class SeedDemoDataTestCase(unittest.TestCase):
    def test_script_imports(self):
        import scripts.seed_demo_data  # noqa: F401
        import scripts.demo_seed_lib as lib

        self.assertTrue(hasattr(lib, "run_seed"))
        self.assertTrue(hasattr(lib, "demo_email"))
        self.assertTrue(hasattr(lib, "demo_code"))

    def test_deterministic_identifiers(self):
        from scripts.demo_seed_lib import DEMO_DOMAIN, demo_code, demo_email

        self.assertEqual(demo_email("superadmin", 1), f"demo-superadmin@{DEMO_DOMAIN}")
        self.assertEqual(demo_email("doctor", 3), f"demo-doctor-03@{DEMO_DOMAIN}")
        self.assertEqual(demo_code("PAT", 42), "DEMO-PAT-042")

    def test_no_destructive_delete_helpers(self):
        from scripts import demo_seed_lib

        source = inspect.getsource(demo_seed_lib)
        lowered = source.lower()
        self.assertNotIn("delete(", lowered)
        self.assertNotIn("drop_all", lowered)
        self.assertNotIn("truncate", lowered)
        self.assertNotIn(".delete()", lowered)

    def test_seed_script_guards_create_all(self):
        source = Path(ROOT / "scripts" / "seed_demo_data.py").read_text(encoding="utf-8")
        self.assertIn("apply_create_all_guard", source)
        self.assertIn("create_all_meta = apply_create_all_guard(app, args.allow_create_all)", source)
        guard_fn = source.split("def apply_create_all_guard")[1].split("def main")[0]
        self.assertEqual(guard_fn.count("db.create_all()"), 1)

    def test_schema_helpers_detect_missing_patient_id(self):
        from app import create_app
        from app.extensions.db import db
        from app.infrastructure.schema_introspection import (
            fk_target_compatible,
            inspect_seed_schema,
            patient_reference_column,
        )

        self.assertEqual(patient_reference_column({"patient_code", "full_name"}), "patient_code")

        app = create_app()
        app.config["TESTING"] = True
        with app.app_context():
            db.create_all()
            self.assertTrue(fk_target_compatible("patient_profiles", "patient_id", "patients", "patient_code"))
            schema = inspect_seed_schema()
            self.assertIn("patients", schema["tables"])
            self.assertEqual(schema["tables"]["patients"]["primary_key"], ["patient_code"])

    def test_create_all_guard_blocks_strict_env(self):
        from app import create_app
        from scripts.seed_demo_data import apply_create_all_guard

        app = create_app()
        app.config["APP_ENV"] = "production"
        with app.app_context():
            meta = apply_create_all_guard(app, allow_create_all=True)
        self.assertFalse(meta["executed"])
        self.assertIn("forbidden", meta["reason"])

    def test_dry_run_works(self):
        from app import create_app
        from app.extensions.db import db
        from scripts.demo_seed_lib import run_seed

        app = create_app()
        app.config["TESTING"] = True
        with app.app_context():
            db.create_all()
            report = run_seed(dry_run=True)
        self.assertEqual(report["mode"], "dry_run")
        self.assertTrue(report["ok"])
        self.assertGreater(sum(report["created_counts"].values()), 0)

    def test_apply_is_idempotent(self):
        from app import create_app
        from app.extensions.db import db
        from scripts.demo_seed_lib import demo_email, run_seed

        app = create_app()
        app.config["TESTING"] = True
        with app.app_context():
            db.create_all()
            first = run_seed(dry_run=False)
            second = run_seed(dry_run=False)
            from app.models.user import User

            super_admin = User.query.filter_by(email=demo_email("superadmin", 1)).all()
        self.assertEqual(len(super_admin), 1)
        self.assertGreater(first["created_counts"].get("users", 0), 0)
        self.assertEqual(second["created_counts"].get("users", 0), 0)


if __name__ == "__main__":
    unittest.main()
