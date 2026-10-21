import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_tmp = tempfile.NamedTemporaryFile(prefix="dxcon_src_", suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

from app.business_engine.service import BusinessEngineError, normalize_order_source
from app.models.biz_order import BizOrder


class OrderSourceTests(unittest.TestCase):
    def test_model_has_source_columns(self):
        cols = set(BizOrder.__table__.columns.keys())
        for name in ("source_type", "source_org_code", "source_org_name_raw", "external_ref", "attributes"):
            self.assertIn(name, cols)

    def test_normalize(self):
        self.assertIsNone(normalize_order_source(None))
        self.assertIsNone(normalize_order_source("  "))
        self.assertEqual(normalize_order_source("clinic"), "CLINIC")
        self.assertEqual(normalize_order_source("walk_in"), "WALK_IN")
        with self.assertRaises(BusinessEngineError):
            normalize_order_source("hospital-x")


if __name__ == "__main__":
    unittest.main()
