import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app.lab_workspace.service import ensure_approver_block

R = SimpleNamespace(approved_by="dr@x.vn", approved_at="2026-10-20 16:00")


class ServeApproverTests(unittest.TestCase):
    def test_injects_into_old_stored_html(self):
        out = ensure_approver_block("<html><body><p>x</p></body></html>", R)
        self.assertIn("Validated / approved by", out)
        self.assertLess(out.index("Validated"), out.index("</body>"))

    def test_idempotent_and_skips_without_approver(self):
        once = ensure_approver_block("<html><body></body></html>", R)
        self.assertEqual(ensure_approver_block(once, R), once)
        plain = "<html><body></body></html>"
        self.assertEqual(ensure_approver_block(plain, SimpleNamespace(approved_by=None, approved_at=None)), plain)


if __name__ == "__main__":
    unittest.main()
