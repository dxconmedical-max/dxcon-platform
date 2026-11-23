import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.lab_workspace.flags import calculate_abnormal_flag
from app.lab_workspace.reference_fill import format_range, resolve_reference
from app.models.patient import Patient
from app.models.reference_range import ReferenceRange


class ReferenceFillTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        db.session.add(Patient(patient_code="PM", full_name="A", gender="M", date_of_birth="1990-01-01"))
        db.session.add(Patient(patient_code="PX", full_name="B", gender=None, date_of_birth="1990-01-01"))
        db.session.add(Patient(patient_code="PN", full_name="C", gender="M", date_of_birth=None))
        db.session.add(ReferenceRange(test_code="T1", test_name="t", sex="M", age_min=18, age_max=120, unit="u", low_value=1, high_value=5, status="ACTIVE"))
        db.session.add(ReferenceRange(test_code="T2", test_name="t", sex="ALL", age_min=18, age_max=120, unit="mg", low_value=None, high_value=10, status="ACTIVE"))
        db.session.add(ReferenceRange(test_code="T3", test_name="t", sex="ALL", age_min=18, age_max=120, unit="mg", low_value=1, high_value=2, status="DRAFT"))
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_fills_range_and_unit_for_matching_sex_and_age(self):
        self.assertEqual(resolve_reference("T1", "PM"), ("1-5", "u"))
        self.assertEqual(resolve_reference("T2", "PM"), ("<10", "mg"))

    def test_never_guesses(self):
        self.assertIsNone(resolve_reference("T1", "PX"))  # sex unknown, row is male-only
        self.assertIsNone(resolve_reference("T1", "PN"))  # age unknown
        self.assertIsNone(resolve_reference("T3", "PM"))  # draft not used
        self.assertIsNone(resolve_reference("T1", None))

    def test_one_sided_ranges_flag(self):
        self.assertEqual(calculate_abnormal_flag("12", reference_range="<10")[0], "high")
        self.assertEqual(calculate_abnormal_flag("8", reference_range="<10")[0], "normal")
        self.assertEqual(calculate_abnormal_flag("3", reference_range=">5")[0], "low")
        self.assertEqual(calculate_abnormal_flag("6.8", reference_range="3.5-5.5")[0], "high")
        self.assertEqual(format_range(None, 10.0), "<10")


if __name__ == "__main__":
    unittest.main()
