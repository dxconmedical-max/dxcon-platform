import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
_tmp = tempfile.NamedTemporaryFile(prefix="dxcon_prov_", suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

import provision_clinics as pc


def _rows(code, email):
    return [{"organization_code": code, "organization_name": f"Clinic {code}", "contact_name": "x",
             "contact_email": "c@placeholder.dxcon.test", "viewer_email": email}]


class ProvisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import create_app
        from app.extensions.db import db

        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.app.config["EXTERNAL_ROLE_GATE_IN_TESTS"] = True
        with cls.app.app_context():
            db.create_all()

    def test_dry_run_writes_nothing(self):
        from app.models.partner_foundation import PartnerOrganization
        from app.models.user import User

        with self.app.app_context():
            report = pc.provision(_rows("PV-DRY", "dry@placeholder.dxcon.test"), apply=False)
            self.assertEqual(report[0]["org"], "create")
            self.assertIsNone(report[0]["password"])
            self.assertIsNone(PartnerOrganization.query.filter_by(organization_code="PV-DRY").first())
            self.assertIsNone(User.query.filter_by(email="dry@placeholder.dxcon.test").first())

    def test_apply_creates_everything_and_is_idempotent(self):
        from app.core.passwords import verify_password
        from app.extensions.db import db
        from app.models.partner_foundation import OrganizationUser, PartnerOrganization
        from app.models.user import User

        with self.app.app_context():
            first = pc.provision(_rows("PV-ONE", "one@placeholder.dxcon.test"), apply=True)
            db.session.commit()
            password = first[0]["password"]
            self.assertTrue(password)
            user = User.query.filter_by(email="one@placeholder.dxcon.test").first()
            org = PartnerOrganization.query.filter_by(organization_code="PV-ONE").first()
            self.assertEqual(user.role, "CLINIC_VIEWER")
            self.assertEqual(user.organization_id, org.id)
            self.assertNotEqual(user.password_hash, password)
            self.assertTrue(verify_password(user.password_hash, password))
            self.assertEqual(OrganizationUser.query.filter_by(organization_id=org.id, user_id=user.id).count(), 1)

            second = pc.provision(_rows("PV-ONE", "one@placeholder.dxcon.test"), apply=True)
            db.session.commit()
            self.assertIsNone(second[0]["password"])
            self.assertEqual((second[0]["org"], second[0]["user"], second[0]["membership"]), ("exists",) * 3)
            self.assertEqual(OrganizationUser.query.filter_by(organization_id=org.id, user_id=user.id).count(), 1)
            self.assertTrue(verify_password(User.query.filter_by(email="one@placeholder.dxcon.test").first().password_hash, password))

    def test_refuses_to_touch_an_existing_user_with_another_role(self):
        from app.core.passwords import hash_password
        from app.extensions.db import db
        from app.models.user import User

        with self.app.app_context():
            db.session.add(User(email="staff@placeholder.dxcon.test", role="RECEPTION",
                                password_hash=hash_password("Str0ng-pass-123"), is_active=True))
            db.session.commit()
            with self.assertRaises(SystemExit):
                pc.provision(_rows("PV-REF", "staff@placeholder.dxcon.test"), apply=True)
            db.session.rollback()
            self.assertEqual(User.query.filter_by(email="staff@placeholder.dxcon.test").first().role, "RECEPTION")

    def test_created_account_can_use_lookup_but_nothing_else(self):
        from app.extensions.db import db
        from app.models.user import User

        with self.app.app_context():
            pc.provision(_rows("PV-E2E", "e2e@placeholder.dxcon.test"), apply=True)
            db.session.commit()
            uid = User.query.filter_by(email="e2e@placeholder.dxcon.test").first().id
        client = self.app.test_client()
        with client.session_transaction() as s:
            s["user_id"], s["role"], s["email"] = uid, "CLINIC_VIEWER", "e2e@placeholder.dxcon.test"
        listing = client.get("/api/v1/clinic-results/reports")
        self.assertEqual(listing.status_code, 200, listing.get_data(as_text=True)[:300])
        blocked = client.get("/api/v1/patients")
        self.assertEqual(blocked.status_code, 403)
        self.assertIn("can only use the clinic results lookup", blocked.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
