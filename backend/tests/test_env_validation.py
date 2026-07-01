import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.infrastructure.production_readiness import cors_status, database_dialect_report, evaluate_go_live_blockers
from scripts.staging_stack_lib import ENV_FILES, REQUIRED_ENV_KEYS, parse_env_file, validate_env_file


class EnvValidationTestCase(unittest.TestCase):
    def test_all_env_templates_present(self):
        for path in ENV_FILES:
            self.assertTrue(path.exists(), path)

    def test_required_keys_in_staging_template(self):
        values = parse_env_file(ROOT / ".env.staging.example")
        for key in REQUIRED_ENV_KEYS:
            self.assertTrue(values.get(key), key)

    def test_production_template_blocks_wildcard_cors(self):
        values = parse_env_file(ROOT / ".env.production.example")
        self.assertNotEqual(values.get("CORS_ORIGINS"), "*")

    def test_staging_go_live_blockers_clear(self):
        values = parse_env_file(ROOT / ".env.staging.example")
        app = create_app()
        app.config.update(
            {
                "TESTING": False,
                "APP_ENV": "staging",
                "CORS_ORIGINS": values["CORS_ORIGINS"],
                "SQLALCHEMY_DATABASE_URI": values["DATABASE_URL"],
                "REDIS_URL": values["REDIS_URL"],
                "SMTP_HOST": values["SMTP_HOST"],
                "SMTP_PORT": int(values["SMTP_PORT"]),
                "SMTP_FROM": values["SMTP_FROM"],
            }
        )
        report = evaluate_go_live_blockers(app)
        self.assertTrue(report["ready"], report["blockers"])

    def test_production_blocks_sqlite_and_wildcard_cors(self):
        app = create_app()
        app.config.update(
            {
                "TESTING": False,
                "APP_ENV": "production",
                "CORS_ORIGINS": "*",
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            }
        )
        self.assertFalse(database_dialect_report(app)["ok"])
        self.assertFalse(cors_status(app)["ok"])

    def test_validate_env_file_helper(self):
        report = validate_env_file(ROOT / ".env.production.example")
        self.assertTrue(report["ok"], report)


if __name__ == "__main__":
    unittest.main()
