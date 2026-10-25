import inspect
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_tmp = tempfile.NamedTemporaryFile(prefix="dxcon_org_", suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

from app.business_engine.service import create_order
from app.models.biz_order import BizOrder
from app.models.patient import Patient


class OrgScopeColumnTests(unittest.TestCase):
    def test_models_have_organization_id(self):
        for model in (Patient, BizOrder):
            self.assertIn("organization_id", model.__table__.columns.keys())

    def test_create_order_accepts_organization_id(self):
        self.assertIn("organization_id", inspect.signature(create_order).parameters)


if __name__ == "__main__":
    unittest.main()
