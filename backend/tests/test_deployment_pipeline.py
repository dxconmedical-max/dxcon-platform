import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from deployment.pipeline.deployment_manifest import build_manifest, write_report
from deployment.pipeline.rollback import build_rollback_plan


class DeploymentPipelineTestCase(unittest.TestCase):
    def test_manifest(self):
        manifest = build_manifest("testing", "docker")
        self.assertIn("kubernetes_manifests", manifest)
        self.assertGreaterEqual(len(manifest["kubernetes_manifests"]), 5)

    def test_write_report(self):
        path = ROOT / "deployment" / "reports" / "test-report.json"
        written = write_report(path, {"ok": True})
        self.assertTrue(Path(written).exists())
        payload = json.loads(Path(written).read_text(encoding="utf-8"))
        self.assertTrue(payload["ok"])
        Path(written).unlink(missing_ok=True)

    def test_rollback_plan(self):
        plan = build_rollback_plan()
        self.assertEqual(plan["strategy"], "metadata-only")
        self.assertFalse(plan["destructive"])

    def test_verify_deployment_script(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "deployment" / "pipeline" / "verify_deployment.py"), "pre"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            env={**os.environ, "DATABASE_URL": "sqlite:///:memory:"},
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)


if __name__ == "__main__":
    unittest.main()
