import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_tmp = tempfile.NamedTemporaryFile(prefix="dxcon_map_", suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

from app.business_engine.service import order_source_from_collection as f


class OrderSourceMappingTests(unittest.TestCase):
    def test_modes(self):
        self.assertEqual(f("AT_RECEPTION")["source_type"], "WALK_IN")
        self.assertEqual(f("desk")["source_type"], "WALK_IN")
        self.assertEqual(f("HOME_COLLECTION")["source_type"], "HOME")
        self.assertEqual(f("HOME")["source_type"], "HOME")

    def test_clinic_keeps_raw_name(self):
        r = f("CLINIC_COLLECTION", "  Phong kham A  ")
        self.assertEqual(r, {"source_type": "CLINIC", "source_org_name_raw": "Phong kham A"})
        self.assertIsNone(f("CLINIC", "")["source_org_name_raw"])

    def test_clinic_name_ignored_for_other_modes(self):
        self.assertIsNone(f("HOME", "Phong kham A")["source_org_name_raw"])

    def test_unknown_or_empty_is_unknown(self):
        for v in (None, "", "weird"):
            self.assertEqual(f(v), {"source_type": None, "source_org_name_raw": None})


if __name__ == "__main__":
    unittest.main()
