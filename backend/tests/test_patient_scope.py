import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_tmp = tempfile.NamedTemporaryFile(prefix="dxcon_scope_", suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

from app.business_engine.service import create_patient
from app.core.patient_scope import GLOBAL_SCOPE, PatientScope, patient_in_scope
from app.models.patient import Patient
from app.reception_workspace.service import duplicate_warnings, fast_search_patients

A, B, LEGACY = "Zq7Scope Alpha", "Zq7Scope Beta", "Zq7Scope Legacy"


class PatientScopeFilterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import create_app
        from app.extensions.db import db

        cls.app = create_app()
        cls.app.config["TESTING"] = True
        with cls.app.app_context():
            db.create_all()
            create_patient(full_name=A, phone="0903000001", organization_id="org-a")
            create_patient(full_name=B, phone="0903000002", organization_id="org-b")
            create_patient(full_name=LEGACY, phone="0903000003")
            db.session.commit()

    def _names(self, scope):
        with self.app.app_context():
            rows = fast_search_patients("Zq7Scope", scope=scope)["data"]
            return {r["full_name"] for r in rows}

    def test_search_is_limited_to_the_scope_organization(self):
        self.assertEqual(self._names(PatientScope("org-a")), {A})
        self.assertEqual(self._names(PatientScope("org-b")), {B})

    def test_global_and_legacy_scopes_see_everything(self):
        everything = {A, B, LEGACY}
        self.assertEqual(self._names(GLOBAL_SCOPE), everything)
        self.assertEqual(self._names(None), everything)

    def test_scope_without_organization_matches_nothing(self):
        self.assertEqual(self._names(PatientScope(None)), set())

    def test_empty_query_listing_is_scoped_too(self):
        with self.app.app_context():
            rows = fast_search_patients("", scope=PatientScope("org-a"), limit=100)["data"]
            self.assertTrue(all(r["full_name"] == A for r in rows if str(r["full_name"]).startswith("Zq7Scope")))
            self.assertNotIn(B, {r["full_name"] for r in rows})

    def test_duplicate_warning_does_not_leak_other_orgs(self):
        with self.app.app_context():
            phone_b = Patient.query.filter_by(full_name=B).first().phone
            self.assertEqual(duplicate_warnings(phone=phone_b, scope=PatientScope("org-a")), [])
            self.assertEqual(len(duplicate_warnings(phone=phone_b, scope=PatientScope("org-b"))), 1)
            self.assertEqual(len(duplicate_warnings(phone=phone_b)), 1)

    def test_patient_in_scope(self):
        with self.app.app_context():
            a = Patient.query.filter_by(full_name=A).first()
            self.assertTrue(patient_in_scope(a, PatientScope("org-a")))
            self.assertFalse(patient_in_scope(a, PatientScope("org-b")))
            self.assertFalse(patient_in_scope(a, PatientScope(None)))
            self.assertTrue(patient_in_scope(a, GLOBAL_SCOPE))
            self.assertFalse(patient_in_scope(None, GLOBAL_SCOPE))


if __name__ == "__main__":
    unittest.main()
