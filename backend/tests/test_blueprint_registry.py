import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"


class BlueprintRegistryTestCase(unittest.TestCase):
    def test_blueprint_registry_verification(self):
        from scripts.blueprint_registry_lib import run_blueprint_registry_verification

        result = run_blueprint_registry_verification()
        self.assertTrue(result["ok"], result)


if __name__ == "__main__":
    unittest.main()
