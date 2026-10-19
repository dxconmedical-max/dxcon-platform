import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app.business_engine.service import render_report_html


def _fake(name="Lê Văn Thắng", note="ok"):
    item = SimpleNamespace(test_name="Demo <b>Test</b>", result_value="10", unit="mg%",
                           reference_range="3.5-5.5", flag="HIGH")
    result = SimpleNamespace(items=[item], released_at="2026-10-19", doctor_note=note)
    order = SimpleNamespace(order_code="ORD-1", patient_name=name)
    return result, order


class ReportHtmlTests(unittest.TestCase):
    def test_declares_utf8_and_keeps_vietnamese(self):
        html = render_report_html(*_fake())
        self.assertIn('<meta charset="utf-8">', html)
        self.assertIn("Lê Văn Thắng", html)

    def test_escapes_html_in_user_fields(self):
        html = render_report_html(*_fake(name="<script>alert(1)</script>", note="<img src=x>"))
        self.assertNotIn("<script>", html)
        self.assertNotIn("<img src=x>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<b>Test</b>", html)


if __name__ == "__main__":
    unittest.main()
