import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_tmp = tempfile.NamedTemporaryFile(prefix="dxcon_pat_", suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

from app.business_engine.service import BusinessEngineError, create_patient, update_patient


class PatientOrgScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import create_app
        from app.extensions.db import db

        cls.app = create_app()
        cls.app.config["TESTING"] = True
        with cls.app.app_context():
            db.create_all()

    def test_same_phone_allowed_across_orgs_but_not_within_one(self):
        with self.app.app_context():
            a = create_patient(full_name="Nguyen A", phone="0901000001", organization_id="org-a")
            b = create_patient(full_name="Nguyen B", phone="0901000001", organization_id="org-b")
            self.assertEqual(a.organization_id, "org-a")
            self.assertEqual(b.organization_id, "org-b")
            with self.assertRaises(BusinessEngineError):
                create_patient(full_name="Nguyen C", phone="0901000001", organization_id="org-a")

    def test_same_national_id_allowed_across_orgs_but_not_within_one(self):
        with self.app.app_context():
            create_patient(full_name="Tran A", national_id="079000000001", organization_id="org-a")
            create_patient(full_name="Tran B", national_id="079000000001", organization_id="org-b")
            with self.assertRaises(BusinessEngineError):
                create_patient(full_name="Tran C", national_id="079000000001", organization_id="org-a")

    def test_no_org_keeps_legacy_global_behaviour(self):
        with self.app.app_context():
            create_patient(full_name="Le A", phone="0901000003")
            with self.assertRaises(BusinessEngineError):
                create_patient(full_name="Le B", phone="0901000003")

    def test_update_phone_clash_is_scoped_to_the_patients_org(self):
        with self.app.app_context():
            create_patient(full_name="A", phone="0902000001", organization_id="org-a")
            b = create_patient(full_name="B", phone="0902000002", organization_id="org-b")
            c = create_patient(full_name="C", phone="0902000003", organization_id="org-a")
            update_patient(b.patient_code, phone="0902000001")
            with self.assertRaises(BusinessEngineError):
                update_patient(c.patient_code, phone="0902000001")


if __name__ == "__main__":
    unittest.main()
