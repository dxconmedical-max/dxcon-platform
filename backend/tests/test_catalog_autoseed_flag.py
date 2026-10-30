import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_tmp = tempfile.NamedTemporaryFile(prefix="dxcon_seed_", suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

from app.business_engine.service import ensure_test_catalog_seed
from app.models.test_catalog import TestCatalog


class AutoseedFlagTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import create_app
        from app.extensions.db import db

        cls.app = create_app()
        cls.app.config["TESTING"] = True
        with cls.app.app_context():
            db.create_all()

    def test_flag_off_leaves_empty_catalog_empty(self):
        with self.app.app_context():
            TestCatalog.query.delete()
            with patch.dict(os.environ, {"TEST_CATALOG_AUTOSEED": "false"}):
                self.assertEqual(ensure_test_catalog_seed(), [])
                self.assertEqual(TestCatalog.query.count(), 0)

    def test_default_still_seeds_for_dev_and_tests(self):
        with self.app.app_context():
            TestCatalog.query.delete()
            with patch.dict(os.environ):
                os.environ.pop("TEST_CATALOG_AUTOSEED", None)
                self.assertEqual(len(ensure_test_catalog_seed()), 3)


if __name__ == "__main__":
    unittest.main()
