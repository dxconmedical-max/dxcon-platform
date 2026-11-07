import os
import sys
import tempfile
import unittest
import uuid
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_tmp = tempfile.NamedTemporaryFile(prefix="dxcon_clinicres_", suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

BASE = "/api/v1/clinic-results"


class ClinicResultsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import create_app
        from app.business_engine import service as biz
        from app.business_engine.statuses import RESULT_RELEASED
        from app.core.passwords import hash_password
        from app.extensions.db import db
        from app.models.biz_order import BizResult
        from app.models.partner_foundation import OrganizationUser, PartnerOrganization
        from app.models.user import User
        from app.partner_foundation.service import seed_organization_roles

        cls.app = create_app()
        cls.app.config["TESTING"] = True
        tag = uuid.uuid4().hex[:6].upper()
        cls.emails, cls.users, cls.orgs, cls.orders = {}, {}, {}, {}
        with cls.app.app_context():
            db.create_all()
            seed_organization_roles()
            catalog = biz.ensure_test_catalog_seed()
            for key in ("A", "B"):
                org = PartnerOrganization(
                    organization_code=f"TST-{key}-{tag}", organization_name=f"Clinic {key}", organization_type="CLINIC"
                )
                db.session.add(org)
                db.session.flush()
                cls.orgs[key] = org.id
            for key in ("A", "B", "N"):
                email = f"viewer-{key}-{tag}@placeholder.dxcon.test".lower()
                user = User(
                    email=email, role="DOCTOR", password_hash=hash_password("Str0ng-pass-123"), is_active=True,
                    organization_id=cls.orgs.get(key),
                )
                db.session.add(user)
                db.session.flush()
                if key in cls.orgs:
                    db.session.add(OrganizationUser(
                        organization_id=cls.orgs[key], user_id=user.id, role_code="VIEWER", active=True
                    ))
                cls.users[key], cls.emails[key] = user.id, email
            n = 0
            for key, released in (("A", True), ("A_DRAFT", False), ("B", True)):
                n += 1
                org_id = cls.orgs[key[0]]
                patient = biz.create_patient(full_name=f"Test {key}", phone=f"0907{n:06d}", organization_id=org_id)
                order = biz.create_order(
                    patient_code=patient.patient_code, test_catalog_ids=[catalog[0].id], actor="test", organization_id=org_id
                )
                db.session.flush()
                db.session.add(BizResult(
                    result_code=f"RS-{tag}-{key}", order_id=order.id,
                    status=RESULT_RELEASED if released else "testing", patient_visible=released,
                    released_at=datetime.utcnow() if released else None, html_content=f"<p>report {key}</p>",
                ))
                cls.orders[key] = order.order_code
            db.session.commit()

    def _client(self, key):
        client = self.app.test_client()
        with client.session_transaction() as s:
            s["user_id"] = self.users[key]
            s["role"] = "DOCTOR"
            s["email"] = self.emails[key]
        return client

    def test_clinic_sees_only_its_own_released_reports(self):
        r = self._client("A").get(BASE + "/reports")
        body = r.get_data(as_text=True)
        self.assertEqual(r.status_code, 200, body[:300])
        self.assertIn(self.orders["A"], body)
        self.assertNotIn(self.orders["A_DRAFT"], body)
        self.assertNotIn(self.orders["B"], body)

    def test_detail_own_ok_foreign_and_unreleased_not_found(self):
        c = self._client("A")
        ok = c.get(f"{BASE}/reports/{self.orders['A']}")
        self.assertEqual(ok.status_code, 200, ok.get_data(as_text=True)[:300])
        self.assertIn("report A", ok.get_data(as_text=True))
        for key in ("B", "A_DRAFT"):
            self.assertEqual(c.get(f"{BASE}/reports/{self.orders[key]}").status_code, 404, key)

    def test_org_selector_cannot_reach_a_foreign_org(self):
        c = self._client("A")
        headers = {"X-Organization-ID": self.orgs["B"]}
        listing = c.get(BASE + "/reports", headers=headers)
        self.assertNotIn(self.orders["B"], listing.get_data(as_text=True))
        detail = c.get(f"{BASE}/reports/{self.orders['B']}", headers=headers)
        self.assertNotEqual(detail.status_code, 200)

    def test_anonymous_is_rejected(self):
        r = self.app.test_client().get(BASE + "/reports")
        self.assertIn(r.status_code, (401, 403))

    def test_user_without_membership_is_forbidden(self):
        self.assertEqual(self._client("N").get(BASE + "/reports").status_code, 403)


if __name__ == "__main__":
    unittest.main()
