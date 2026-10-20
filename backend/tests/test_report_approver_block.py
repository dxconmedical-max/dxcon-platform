import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app.business_engine.service import render_report_html


def _fake(approved_by="dr@x.vn"):
    item = SimpleNamespace(test_name="T1", result_value="1", unit="", reference_range="", flag="N")
    result = SimpleNamespace(items=[item], released_at="2026-10-20", doctor_note="ok",
                             approved_by=approved_by, approved_at="2026-10-20 16:00")
    order = SimpleNamespace(order_code="ORD-1", patient_name="Lê Văn Thắng")
    return result, order


class ApproverBlockTests(unittest.TestCase):
    def test_block_shows_approver_and_time(self):
        html = render_report_html(*_fake())
        self.assertIn("Validated / approved by", html)
        self.assertIn("dr@x.vn", html)
        self.assertIn("2026-10-20 16:00", html)

    def test_no_block_without_approver_and_still_escaped(self):
        self.assertNotIn("Validated / approved by", render_report_html(*_fake(approved_by=None)))
        html = render_report_html(*_fake(approved_by="<script>x</script>"))
        self.assertNotIn("<script>", html)


if __name__ == "__main__":
    unittest.main()
