import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
_tmp = tempfile.NamedTemporaryFile(prefix="dxcon_provstaff_", suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

import provision_staff as ps


def _rows(*specs):
    return [{"full_name": f"Nguoi {i}", "email": email, "role": role} for i, (email, role) in enumerate(specs)]


class ProvisionStaffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import create_app
        from app.extensions.db import db
        from app.models.partner_foundation import PartnerOrganization

        cls.app = create_app()
        cls.app.config["TESTING"] = True
        with cls.app.app_context():
            db.create_all()
            org = PartnerOrganization(organization_code="DXCON-INT-T", organization_name="DxCon Internal test",
                                      organization_type="DXCON_INTERNAL")
            db.session.add(org)
            db.session.commit()
            cls.internal_id = org.id

    def test_dry_run_writes_nothing(self):
        from app.models.user import User

        with self.app.app_context():
            report = ps.provision(_rows(("dry@placeholder.dxcon.test", "RECEPTION")), apply=False)
            self.assertEqual(report[0]["user"], "create")
            self.assertIsNone(report[0]["password"])
            self.assertIsNone(User.query.filter_by(email="dry@placeholder.dxcon.test").first())

    def test_apply_creates_staff_with_membership_and_is_idempotent(self):
        from app.core.passwords import verify_password
        from app.extensions.db import db
        from app.models.partner_foundation import OrganizationUser
        from app.models.user import User

        specs = (("rec@placeholder.dxcon.test", "RECEPTION"), ("lab@placeholder.dxcon.test", "LAB"),
                 ("acc@placeholder.dxcon.test", "ACCOUNTING"))
        expected = {"RECEPTION": "RECEPTION", "LAB": "LAB", "ACCOUNTING": "FINANCE"}
        with self.app.app_context():
            first = ps.provision(_rows(*specs), apply=True)
            db.session.commit()
            for item in first:
                self.assertTrue(item["password"])
                user = User.query.filter_by(email=item["email"]).first()
                self.assertEqual(user.role, item["role"])
                self.assertEqual(user.organization_id, self.internal_id)
                self.assertTrue(verify_password(user.password_hash, item["password"]))
                member = OrganizationUser.query.filter_by(user_id=user.id, organization_id=self.internal_id).one()
                self.assertEqual(member.role_code, expected[item["role"]])
            second = ps.provision(_rows(*specs), apply=True)
            db.session.commit()
            self.assertTrue(all(r["password"] is None and r["user"] == "exists" and r["membership"] == "exists" for r in second))
            self.assertEqual(OrganizationUser.query.filter_by(organization_id=self.internal_id).count(),
                             User.query.filter_by(organization_id=self.internal_id).count())

    def test_disallowed_roles_and_duplicates_write_nothing(self):
        from app.models.user import User

        for role in ("SUPER_ADMIN", "SYSTEM_ADMIN", "PATIENT", "CLINIC_VIEWER", "NOBODY"):
            with self.app.app_context():
                with self.assertRaises(SystemExit):
                    ps.provision(_rows(("ok@placeholder.dxcon.test", "RECEPTION"), ("bad@placeholder.dxcon.test", role)), apply=True)
                self.assertIsNone(User.query.filter_by(email="ok@placeholder.dxcon.test").first())
        with self.app.app_context():
            with self.assertRaises(SystemExit):
                ps.provision(_rows(("dup@placeholder.dxcon.test", "LAB"), ("dup@placeholder.dxcon.test", "LAB")), apply=True)

    def test_refuses_existing_user_with_another_role(self):
        from app.core.passwords import hash_password
        from app.extensions.db import db
        from app.models.user import User

        with self.app.app_context():
            db.session.add(User(email="other@placeholder.dxcon.test", role="DOCTOR",
                                password_hash=hash_password("Str0ng-pass-123"), is_active=True))
            db.session.commit()
            with self.assertRaises(SystemExit):
                ps.provision(_rows(("other@placeholder.dxcon.test", "RECEPTION")), apply=True)
            db.session.rollback()
            self.assertEqual(User.query.filter_by(email="other@placeholder.dxcon.test").first().role, "DOCTOR")

    def test_lab_org_role_permissions(self):
        from app.partner_foundation.rbac import org_role_has_permission

        self.assertTrue(org_role_has_permission("LAB", "data.create"))
        self.assertFalse(org_role_has_permission("LAB", "data.approve"))
        self.assertFalse(org_role_has_permission("LAB", "data.delete"))

    def test_provisioned_reception_staff_can_use_the_clinic_picker(self):
        from app.extensions.db import db
        from app.models.user import User

        with self.app.app_context():
            ps.provision(_rows(("e2e@placeholder.dxcon.test", "RECEPTION")), apply=True)
            db.session.commit()
            uid = User.query.filter_by(email="e2e@placeholder.dxcon.test").first().id
        client = self.app.test_client()
        with client.session_transaction() as s:
            s["user_id"], s["role"], s["email"] = uid, "RECEPTION", "e2e@placeholder.dxcon.test"
        r = client.get("/api/v1/reception/workspace/clinics")
        self.assertEqual(r.status_code, 200, r.get_data(as_text=True)[:300])


if __name__ == "__main__":
    unittest.main()
