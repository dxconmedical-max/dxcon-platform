import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_tmp = tempfile.NamedTemporaryFile(prefix="dxcon_wire_", suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

from app.core import patient_scope as ps
from app.core.patient_scope import GLOBAL_SCOPE, PatientScope
from app.core.tenant_authorization import AuthorizedTenant
from app.models.patient import Patient
from app.reception_workspace.service import register_patient

FLAG = "TENANT_ENFORCE_PATIENT_SCOPE"


def _tenant(org=None, is_global=False):
    return AuthorizedTenant(
        organization_id=org,
        organization_ids=frozenset([org] if org else []),
        membership_id=None,
        organization_role=None,
        is_global_scope=is_global,
    )


class ResolveScopeTests(unittest.TestCase):
    def test_flag_off_means_legacy(self):
        with patch.dict(os.environ, {FLAG: "false"}):
            self.assertEqual(ps.resolve_patient_scope(), (None, None))

    def test_flag_on_cases(self):
        target = "app.core.tenant_authorization.resolve_authorized_tenant"
        with patch.dict(os.environ, {FLAG: "true"}):
            with patch(target, return_value=_tenant(None, True)):
                self.assertEqual(ps.resolve_patient_scope(), (GLOBAL_SCOPE, None))
            with patch(target, return_value=_tenant("org-a")), patch.object(ps, "is_internal_org", return_value=False):
                self.assertEqual(ps.resolve_patient_scope(), (PatientScope("org-a"), None))
            with patch(target, return_value=_tenant("org-int")), patch.object(ps, "is_internal_org", return_value=True):
                self.assertEqual(ps.resolve_patient_scope(), (GLOBAL_SCOPE, None))
            with patch(target, return_value=({"error": "x"}, 403)):
                scope, err = ps.resolve_patient_scope()
                self.assertIsNone(scope)
                self.assertEqual(err[1], 403)


class RegisterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import create_app
        from app.extensions.db import db

        cls.app = create_app()
        cls.app.config["TESTING"] = True
        with cls.app.app_context():
            db.create_all()

    def test_register_stamps_org_and_scopes_duplicates(self):
        with self.app.app_context():
            r1 = register_patient({"full_name": "Reg A", "phone": "0904000001"}, scope=PatientScope("org-a"))
            self.assertTrue(r1["ok"])
            self.assertEqual(Patient.query.filter_by(full_name="Reg A").first().organization_id, "org-a")
            r2 = register_patient({"full_name": "Reg B", "phone": "0904000001"}, scope=PatientScope("org-b"))
            self.assertTrue(r2["ok"])
            r3 = register_patient({"full_name": "Reg C", "phone": "0904000001"}, scope=PatientScope("org-a"))
            self.assertFalse(r3["ok"])
            self.assertTrue(r3["duplicate"])


if __name__ == "__main__":
    unittest.main()
