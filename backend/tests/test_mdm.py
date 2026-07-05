import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.mdm.import_engine import import_from_bytes
from app.mdm.registry import ENTITY_TYPES
from app.mdm.service import dashboard_stats, get_record
from app.mdm.validation import validate_row
from app.models.mdm import MdmMasterRecord


class MdmTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_entity_registry_has_18_modules(self):
        self.assertEqual(len(ENTITY_TYPES), 18)

    def test_validate_required_fields(self):
        status, errors = validate_row("test_catalog", {"code": "", "name": "Test"})
        self.assertNotEqual(status, "valid")
        self.assertTrue(errors)

    def test_import_and_dashboard(self):
        csv_content = b"code,name,category,price\nMDM-T1,MDM Test,Lab,100\n"
        batch = import_from_bytes(
            "test_catalog",
            csv_content,
            file_name="test.csv",
            actor="test@dxcon.test",
            auto_approve=True,
            auto_commit=True,
        )
        db.session.commit()
        self.assertGreaterEqual(batch.committed_rows, 1)
        record = get_record("test_catalog", "MDM-T1")
        self.assertIsNotNone(record)
        stats = dashboard_stats()
        self.assertGreaterEqual(stats["totals"]["records"], 1)

    def test_duplicate_rejected_on_commit(self):
        csv_content = b"code,name\nDUP-1,First\n"
        import_from_bytes("sample_type", csv_content, file_name="a.csv", auto_approve=True, auto_commit=True)
        db.session.commit()
        batch2 = import_from_bytes("sample_type", csv_content, file_name="b.csv")
        db.session.commit()
        self.assertGreaterEqual(batch2.duplicate_rows, 1)


if __name__ == "__main__":
    unittest.main()
