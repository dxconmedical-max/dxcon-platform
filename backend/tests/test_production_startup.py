import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"


class ProductionStartupTestCase(unittest.TestCase):
    def test_gunicorn_config_loads(self):
        config_path = ROOT / "gunicorn.conf.py"
        scope = {}
        exec(config_path.read_text(encoding="utf-8"), scope)
        self.assertEqual(scope["proc_name"], "dxcon-api")
        self.assertGreater(scope["timeout"], 0)

    def test_production_start_api_exec(self):
        import production_start

        with mock.patch.object(production_start, "_run_api") as run_api:
            code = production_start.main(["api"])
            self.assertEqual(code, 0)
            run_api.assert_called_once()

    def test_production_start_worker_placeholder(self):
        import production_start

        with mock.patch.object(production_start.time, "sleep", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                production_start._run_placeholder("worker")

    def test_dockerfile_uses_production_start(self):
        dockerfile = ROOT / "Dockerfile"
        text = dockerfile.read_text(encoding="utf-8")
        self.assertIn("production_start.py", text)
        self.assertIn("HEALTHCHECK", text)


if __name__ == "__main__":
    unittest.main()
