import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from scripts.staging_stack_lib import (
    REQUIRED_ENV_KEYS,
    run_staging_verification,
    validate_env_file,
    verify_docker_stack,
    verify_nginx_config,
)


class StagingStackTestCase(unittest.TestCase):
    def test_required_env_keys(self):
        self.assertIn("DATABASE_URL", REQUIRED_ENV_KEYS)
        self.assertIn("STORAGE_PATH", REQUIRED_ENV_KEYS)

    def test_staging_env_template(self):
        report = validate_env_file(ROOT / ".env.staging.example")
        self.assertTrue(report["ok"], report)

    def test_docker_stack_files(self):
        report = verify_docker_stack()
        self.assertTrue(report["ok"], report)

    def test_nginx_config(self):
        report = verify_nginx_config()
        self.assertTrue(report["ok"], report)
        self.assertTrue(report["checks"]["gzip"])
        self.assertTrue(report["checks"]["health_route"])

    def test_full_verification(self):
        result = run_staging_verification()
        self.assertGreaterEqual(result["passed"], 8, result)


if __name__ == "__main__":
    unittest.main()
