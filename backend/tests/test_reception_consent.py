import os
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_tmp = tempfile.NamedTemporaryFile(prefix="dxcon_consent_", suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

BASE = "/api/v1/reception/workspace"


class ReceptionConsentTests(unittest.TestCase):
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
        cls.tag = uuid.uuid4().hex[:6].upper()
        with cls.app.app_context():
            db.create_all()
            seed_organization_roles()
            biz.ensure_test_catalog_seed()
            org = PartnerOrganization(
                organization_code=f"CS-INT-{cls.tag}", organization_name=f"Consent internal {cls.tag}",
                organization_type="DXCON_INTERNAL",
            )
            db.session.add(org)
            db.session.flush()
            email = f"staff-{cls.tag}@placeholder.dxcon.test".lower()
            user = User(email=email, role="RECEPTION", password_hash=hash_password("Str0ng-pass-123"),
                        is_active=True, organization_id=org.id)
            db.session.add(user)
            db.session.flush()
            db.session.add(OrganizationUser(organization_id=org.id, user_id=user.id, role_code="ORG_OWNER", active=True))
            db.session.commit()
            cls.user = (user.id, email)

    def setUp(self):
        os.environ.pop("CONSENT_REQUIRED_FOR_ORDERS", None)

    def tearDown(self):
        os.environ.pop("CONSENT_REQUIRED_FOR_ORDERS", None)

    def _client(self):
        client = self.app.test_client()
        with client.session_transaction() as s:
            s["user_id"], s["role"], s["email"] = self.user[0], "RECEPTION", self.user[1]
        return client

    def _patient(self):
        from app.business_engine import service as biz
        from app.extensions.db import db

        with self.app.app_context():
            patient = biz.create_patient(full_name=f"CONSENT {uuid.uuid4().hex[:5]}", phone="09" + str(uuid.uuid4().int)[:8])
            db.session.commit()
            return patient.patient_code

    def _order(self, client, code):
        from app.models.test_catalog import TestCatalog

        with self.app.app_context():
            test_id = TestCatalog.query.first().id
        return client.post(BASE + "/orders", json={"patient_code": code, "test_catalog_ids": [test_id]})

    def _record(self, client, code, consents, **extra):
        body = {"consents": consents, "method": "PAPER", "document_ref": "FORM-001"}
        body.update(extra)
        return client.post(f"{BASE}/patients/{code}/consents", json=body)

    def test_record_and_read_back(self):
        client, code = self._client(), self._patient()
        res = self._record(client, code, [
            {"consent_type": "LAB_TEST", "granted": True},
            {"consent_type": "CLINIC_SHARE", "granted": False},
        ])
        self.assertEqual(res.status_code, 201, res.get_data(as_text=True))
        got = client.get(f"{BASE}/patients/{code}/consents").get_json()["data"]["consents"]
        self.assertTrue(got["LAB_TEST"]["granted"])
        self.assertFalse(got["CLINIC_SHARE"]["granted"])
        self.assertIsNone(got["CONTACT"])

    def test_validation(self):
        client, code = self._client(), self._patient()
        self.assertEqual(self._record(client, code, []).status_code, 400)
        self.assertEqual(self._record(client, code, [{"consent_type": "NOPE", "granted": True}]).status_code, 400)
        self.assertEqual(self._record(client, code, [{"consent_type": "LAB_TEST", "granted": "yes"}]).status_code, 400)
        self.assertEqual(
            self._record(client, code, [{"consent_type": "LAB_TEST", "granted": True}], method="VERBAL").status_code, 400)
        dup = [{"consent_type": "LAB_TEST", "granted": True}, {"consent_type": "LAB_TEST", "granted": False}]
        self.assertEqual(self._record(client, code, dup).status_code, 400)
        self.assertEqual(self._record(client, "NO-SUCH", [{"consent_type": "LAB_TEST", "granted": True}]).status_code, 404)

    def test_withdrawal_keeps_history_and_wins(self):
        from app.models.patient_consent import PatientConsent

        client, code = self._client(), self._patient()
        self._record(client, code, [{"consent_type": "CLINIC_SHARE", "granted": True}])
        self._record(client, code, [{"consent_type": "CLINIC_SHARE", "granted": False}])
        got = client.get(f"{BASE}/patients/{code}/consents").get_json()["data"]["consents"]
        self.assertFalse(got["CLINIC_SHARE"]["granted"])
        with self.app.app_context():
            self.assertEqual(PatientConsent.query.filter_by(patient_id=code, consent_type="CLINIC_SHARE").count(), 2)

    def test_gate_off_by_default(self):
        client, code = self._client(), self._patient()
        self.assertEqual(self._order(client, code).status_code, 201)

    def test_gate_on_blocks_until_lab_test_consent(self):
        os.environ["CONSENT_REQUIRED_FOR_ORDERS"] = "true"
        client, code = self._client(), self._patient()
        blocked = self._order(client, code)
        self.assertEqual(blocked.status_code, 409)
        self.assertEqual(blocked.get_json()["code"], "consent_required")
        self._record(client, code, [{"consent_type": "CONTACT", "granted": True}])
        self.assertEqual(self._order(client, code).status_code, 409)
        self._record(client, code, [{"consent_type": "LAB_TEST", "granted": True}])
        self.assertEqual(self._order(client, code).status_code, 201)
        self._record(client, code, [{"consent_type": "LAB_TEST", "granted": False}])
        self.assertEqual(self._order(client, code).status_code, 409)

    def test_guardian_recorded(self):
        import json
        from app.models.patient_consent import PatientConsent

        client, code = self._client(), self._patient()
        res = self._record(client, code, [{"consent_type": "LAB_TEST", "granted": True}],
                           guardian={"name": "Nguyen Van A", "relationship": "Cha", "document": "CCCD"})
        self.assertEqual(res.status_code, 201)
        with self.app.app_context():
            row = PatientConsent.query.filter_by(patient_id=code).first()
            self.assertEqual(json.loads(row.metadata_json)["guardian"]["relationship"], "Cha")


if __name__ == "__main__":
    unittest.main()
