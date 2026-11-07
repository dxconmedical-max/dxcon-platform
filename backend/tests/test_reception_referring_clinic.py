import os
import sys
import tempfile
import unittest
import uuid
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_tmp = tempfile.NamedTemporaryFile(prefix="dxcon_refclinic_", suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

BASE = "/api/v1/reception/workspace"
LOOKUP = "/api/v1/clinic-results/reports"


class ReferringClinicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import create_app
        from app.business_engine import service as biz
        from app.core.passwords import hash_password
        from app.extensions.db import db
        from app.models.partner_foundation import OrganizationUser, PartnerOrganization
        from app.models.user import User
        from app.partner_foundation.service import seed_organization_roles

        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.app.config["EXTERNAL_ROLE_GATE_IN_TESTS"] = True
        cls.tag = uuid.uuid4().hex[:6].upper()
        cls.orgs, cls.codes, cls.names, cls.users = {}, {}, {}, {}
        with cls.app.app_context():
            db.create_all()
            seed_organization_roles()
            biz.ensure_test_catalog_seed()
            for key, org_type in (("INT", "DXCON_INTERNAL"), ("A", "CLINIC"), ("B", "CLINIC")):
                org = PartnerOrganization(
                    organization_code=f"RF-{key}-{cls.tag}", organization_name=f"Referring clinic {key} {cls.tag}",
                    organization_type=org_type,
                )
                db.session.add(org)
                db.session.flush()
                cls.orgs[key], cls.codes[key], cls.names[key] = org.id, org.organization_code, org.organization_name
            specs = (
                ("staff", "RECEPTION", "INT", "ORG_OWNER"),
                ("outsider", "RECEPTION", "A", "RECEPTION"),
                ("viewerA", "CLINIC_VIEWER", "A", "VIEWER"),
                ("viewerB", "CLINIC_VIEWER", "B", "VIEWER"),
            )
            for key, role, org_key, org_role in specs:
                email = f"{key}-{cls.tag}@placeholder.dxcon.test".lower()
                user = User(email=email, role=role, password_hash=hash_password("Str0ng-pass-123"),
                            is_active=True, organization_id=cls.orgs[org_key])
                db.session.add(user)
                db.session.flush()
                db.session.add(OrganizationUser(organization_id=cls.orgs[org_key], user_id=user.id,
                                                role_code=org_role, active=True))
                cls.users[key] = (user.id, email, role)
            db.session.commit()

    def _client(self, key):
        client = self.app.test_client()
        uid, email, role = self.users[key]
        with client.session_transaction() as s:
            s["user_id"], s["role"], s["email"] = uid, role, email
        return client

    def _patient(self, label):
        from app.business_engine import service as biz
        from app.extensions.db import db

        with self.app.app_context():
            patient = biz.create_patient(full_name=f"REFTEST {label} {self.tag}", phone="09" + str(uuid.uuid4().int)[:8])
            db.session.commit()
            return patient.patient_code

    def _post_order(self, client, patient_code, **extra):
        from app.models.test_catalog import TestCatalog

        with self.app.app_context():
            test_id = TestCatalog.query.first().id
        body = {"patient_code": patient_code, "test_catalog_ids": [test_id]}
        body.update(extra)
        return client.post(BASE + "/orders", json=body)

    def _order(self, patient_code):
        from app.models.biz_order import BizOrder

        return BizOrder.query.filter_by(patient_code=patient_code).first()

    def test_clinic_list_is_for_dxcon_staff_only(self):
        listing = self._client("staff").get(BASE + "/clinics")
        body = listing.get_data(as_text=True)
        self.assertEqual(listing.status_code, 200, body[:300])
        self.assertIn(self.names["A"], body)
        self.assertIn(self.names["B"], body)
        self.assertNotIn(self.names["INT"], body)
        self.assertEqual(self._client("outsider").get(BASE + "/clinics").status_code, 403)
        blocked = self._client("viewerA").get(BASE + "/clinics")
        self.assertEqual(blocked.status_code, 403)
        self.assertIn("can only use the clinic results lookup", blocked.get_data(as_text=True))

    def test_order_without_referring_clinic_keeps_the_callers_organization(self):
        code = self._patient("PLAIN")
        r = self._post_order(self._client("staff"), code)
        self.assertEqual(r.status_code, 201, r.get_data(as_text=True)[:400])
        with self.app.app_context():
            self.assertEqual(self._order(code).organization_id, self.orgs["INT"])

    def test_referred_order_is_stamped_and_only_that_clinic_sees_it(self):
        from app.business_engine.statuses import RESULT_RELEASED
        from app.extensions.db import db
        from app.models.biz_order import BizResult

        code = self._patient("REF")
        r = self._post_order(self._client("staff"), code, referring_organization_id=self.orgs["A"])
        self.assertEqual(r.status_code, 201, r.get_data(as_text=True)[:400])
        with self.app.app_context():
            order = self._order(code)
            self.assertEqual(order.organization_id, self.orgs["A"])
            self.assertEqual(order.source_org_code, self.codes["A"])
            db.session.add(BizResult(result_code=f"RS-{self.tag}-REF", order_id=order.id, status=RESULT_RELEASED,
                                     patient_visible=True, released_at=datetime.utcnow(), html_content="<p>ref</p>"))
            db.session.commit()
            name = order.patient_name
        self.assertIn(name, self._client("viewerA").get(LOOKUP).get_data(as_text=True))
        self.assertNotIn(name, self._client("viewerB").get(LOOKUP).get_data(as_text=True))

    def test_bad_referring_clinic_is_rejected_and_creates_nothing(self):
        for key, referring, expected in (
            ("staff", str(uuid.uuid4()), 404),
            ("staff", self.orgs["INT"], 404),
            ("outsider", self.orgs["B"], 403),
        ):
            code = self._patient("BAD-" + key)
            r = self._post_order(self._client(key), code, referring_organization_id=referring)
            self.assertEqual(r.status_code, expected, (key, r.get_data(as_text=True)[:300]))
            with self.app.app_context():
                self.assertIsNone(self._order(code))


if __name__ == "__main__":
    unittest.main()
