import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from scripts.go_live_rc2_lib import build_rollback_package, git_sha


class RollbackPackageTestCase(unittest.TestCase):
    def test_build_rollback_package(self):
        package = build_rollback_package()
        self.assertEqual(package["current_git_sha"], git_sha())
        self.assertTrue(package["previous_release_sha"])
        self.assertIn("rollback_command_recommendation", package)
        self.assertIn("database_migration_warning", package)
        self.assertGreaterEqual(len(package["artifact_checklist"]), 3)

        path = ROOT / "generated_release" / "ROLLBACK_PACKAGE.json"
        self.assertTrue(path.exists())
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["current_git_sha"], git_sha())


if __name__ == "__main__":
    unittest.main()
