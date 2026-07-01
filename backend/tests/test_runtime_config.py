import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.runtime.deployment_profile import current_profile, profile_settings
from app.runtime.environment import Environment
from app.runtime.feature_flags import FeatureFlags
from app.runtime.runtime_config import RuntimeConfig


class RuntimeConfigTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_profiles(self):
        for profile in ("development", "staging", "production", "testing"):
            settings = profile_settings(profile)
            self.assertEqual(settings["profile"], profile)

    def test_runtime_config_load(self):
        config = RuntimeConfig.load(self.app)
        self.assertIn("profile", config)
        self.assertIn("environment", config)
        self.assertIn("feature_flags", config)

    def test_runtime_config_validate(self):
        result = RuntimeConfig.validate(self.app)
        self.assertTrue(result["valid"])

    def test_environment_summary(self):
        summary = Environment.summary()
        self.assertIn("provider", summary)

    def test_feature_flags(self):
        flags = FeatureFlags.all()
        self.assertIsInstance(flags, dict)


if __name__ == "__main__":
    unittest.main()
