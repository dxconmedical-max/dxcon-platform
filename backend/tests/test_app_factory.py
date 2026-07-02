import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"


class AppFactoryTestCase(unittest.TestCase):
    def test_create_app_bootstraps(self):
        from app import create_app
        from app.extensions.db import db

        app = create_app()
        app.config["TESTING"] = True
        with app.app_context():
            db.create_all()
            self.assertTrue(app.config.get("SECRET_KEY"))
            self.assertGreater(len(app.blueprints), 0)
            self.assertGreater(len(list(app.url_map.iter_rules())), 0)

    def test_bootstrap_modules_importable(self):
        from app.bootstrap.extensions import init_extensions
        from app.bootstrap.middleware import register_middleware
        from app.bootstrap.blueprints import register_blueprints
        from app.bootstrap.errors import register_errors

        self.assertTrue(callable(init_extensions))
        self.assertTrue(callable(register_middleware))
        self.assertTrue(callable(register_blueprints))
        self.assertTrue(callable(register_errors))


if __name__ == "__main__":
    unittest.main()
