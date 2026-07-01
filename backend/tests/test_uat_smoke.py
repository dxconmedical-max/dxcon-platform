import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from scripts.staging_monitoring_lib import (
    run_monitoring_verification,
    verify_alertmanager_placeholder,
    verify_grafana_provisioning,
    verify_loki_placeholder,
    verify_prometheus_config,
)
from scripts.uat_smoke import run_uat_smoke


class UatSmokeTestCase(unittest.TestCase):
    def test_monitoring_configs_present(self):
        self.assertTrue(verify_prometheus_config()["ok"])
        self.assertTrue(verify_grafana_provisioning()["ok"])
        self.assertTrue(verify_loki_placeholder()["ok"])
        self.assertTrue(verify_alertmanager_placeholder()["ok"])

    def test_uat_smoke_journey(self):
        result = run_uat_smoke()
        self.assertTrue(result["ok"], result)
        self.assertTrue(result["steps"]["register_login"])
        self.assertTrue(result["steps"]["create_patient"])

    def test_monitoring_verification(self):
        result = run_monitoring_verification()
        self.assertGreaterEqual(result["passed"], 5, result)


if __name__ == "__main__":
    unittest.main()
