import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app.lab_workspace.service import ensure_utf8_html


class EnsureUtf8Tests(unittest.TestCase):
    def test_adds_meta_to_old_stored_report(self):
        old = "<html><body><p>Patient: Lê Văn Thắng</p></body></html>"
        out = ensure_utf8_html(old)
        self.assertIn('<meta charset="utf-8">', out)
        self.assertIn("Lê Văn Thắng", out)

    def test_keeps_existing_charset(self):
        doc = '<!doctype html><html><head><meta charset="utf-8"></head><body>x</body></html>'
        self.assertEqual(ensure_utf8_html(doc), doc)

    def test_wraps_fragment_and_handles_empty(self):
        self.assertIn("<meta charset", ensure_utf8_html("<p>Thắng</p>"))
        self.assertIn("<meta charset", ensure_utf8_html(None))


if __name__ == "__main__":
    unittest.main()
