import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app.reporting_engine.approver import describe_approver, format_approver


class ApproverTests(unittest.TestCase):
    def test_full_profile(self):
        p = SimpleNamespace(full_name="Nguyễn Văn An", job_title="Bác sĩ chuyên khoa", license_number="12345")
        self.assertEqual(
            format_approver("an@dxcon.com.vn", p),
            "Nguyễn Văn An, Bác sĩ chuyên khoa (CCHN: 12345)",
        )

    def test_name_only_and_missing_profile(self):
        p = SimpleNamespace(full_name="Lê Thị Bình", job_title=None, license_number=None)
        self.assertEqual(format_approver("b@x.vn", p), "Lê Thị Bình")
        self.assertEqual(format_approver("b@x.vn", None), "b@x.vn")
        self.assertIsNone(format_approver(None, p))

    def test_describe_falls_back_without_app_context(self):
        self.assertEqual(describe_approver("someone@x.vn"), "someone@x.vn")
        self.assertIsNone(describe_approver(None))


if __name__ == "__main__":
    unittest.main()
