import os
import sys
import tempfile
import unittest
import uuid
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_tmp = tempfile.NamedTemporaryFile(prefix="dxcon_booking_", suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

PUBLIC = "/api/v1/public/bookings"
LIST = "/api/v1/reception/workspace/booking-requests"


class PublicBookingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import create_app
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
            org = PartnerOrganization(
                organization_code=f"BK-INT-{cls.tag}", organization_name=f"Booking internal {cls.tag}",
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

    def _staff(self):
        client = self.app.test_client()
        with client.session_transaction() as s:
            s["user_id"], s["role"], s["email"] = self.user[0], "RECEPTION", self.user[1]
        return client

    def _body(self, **extra):
        body = {
            "full_name": "Nguyen Van Test",
            "phone": "0901 234 567",
            "address": "12 Test Street, District 1",
            "preferred_date": (date.today() + timedelta(days=1)).isoformat(),
            "preferred_slot": "MORNING",
            "consent_contact": True,
        }
        body.update(extra)
        return body

    def _post(self, body, ip):
        return self.app.test_client().post(PUBLIC, json=body, headers={"X-Forwarded-For": ip})

    def _ip(self):
        return f"10.{uuid.uuid4().int % 250}.{uuid.uuid4().int % 250}.{uuid.uuid4().int % 250}"

    def test_public_create_and_reception_sees_it(self):
        res = self._post(self._body(), self._ip())
        self.assertEqual(res.status_code, 201, res.get_data(as_text=True))
        ref = res.get_json()["data"]["reference"]
        self.assertTrue(ref.startswith("BK-"))
        items = self._staff().get(LIST + "?status=NEW").get_json()["data"]["items"]
        mine = [i for i in items if i["reference"] == ref]
        self.assertEqual(len(mine), 1)
        self.assertEqual(mine[0]["phone"], "0901234567")
        self.assertEqual(mine[0]["status"], "NEW")
        self.assertTrue(mine[0]["consent_at"])

    def test_validation(self):
        ip = self._ip()
        self.assertEqual(self._post(self._body(full_name=""), ip).status_code, 400)
        self.assertEqual(self._post(self._body(phone="12345"), ip).status_code, 400)
        self.assertEqual(self._post(self._body(address="x"), ip).status_code, 400)
        self.assertEqual(self._post(self._body(email="not-an-email"), ip).status_code, 400)
        self.assertEqual(self._post(self._body(preferred_slot="NIGHT"), ip).status_code, 400)
        past = (date.today() - timedelta(days=1)).isoformat()
        self.assertEqual(self._post(self._body(preferred_date=past), ip).status_code, 400)
        self.assertEqual(self._post(self._body(consent_contact=False), ip).status_code, 400)
        no_consent = self._body()
        del no_consent["consent_contact"]
        self.assertEqual(self._post(no_consent, ip).status_code, 400)

    def test_honeypot_stores_nothing(self):
        from app.models.booking_request import BookingRequest

        ip = self._ip()
        res = self._post(self._body(website="http://spam.example"), ip)
        self.assertEqual(res.status_code, 201)
        with self.app.app_context():
            self.assertEqual(BookingRequest.query.filter_by(ip_address=ip).count(), 0)

    def test_per_ip_rate_limit(self):
        ip = self._ip()
        for _ in range(5):
            self.assertEqual(self._post(self._body(), ip).status_code, 201)
        self.assertEqual(self._post(self._body(), ip).status_code, 429)
        self.assertEqual(self._post(self._body(), self._ip()).status_code, 201)

    def test_reception_endpoints_require_login(self):
        anon = self.app.test_client()
        self.assertIn(anon.get(LIST).status_code, (401, 403))
        self.assertIn(anon.post(LIST + "/x/status", json={"status": "DONE"}).status_code, (401, 403))
        self.assertIn(anon.get(LIST + "/x").status_code, (401, 403))

    def test_get_one_and_link_order(self):
        ref = self._post(self._body(), self._ip()).get_json()["data"]["reference"]
        staff = self._staff()
        rid = [i for i in staff.get(LIST).get_json()["data"]["items"] if i["reference"] == ref][0]["id"]
        one = staff.get(f"{LIST}/{rid}")
        self.assertEqual(one.status_code, 200)
        self.assertEqual(one.get_json()["data"]["reference"], ref)
        self.assertEqual(staff.get(f"{LIST}/nope").status_code, 404)
        done = staff.post(f"{LIST}/{rid}/status", json={"status": "SCHEDULED", "order_code": "ORD-123"})
        self.assertEqual(done.get_json()["data"]["status"], "SCHEDULED")
        self.assertIn("ORD-123", done.get_json()["data"]["internal_note"])

    def test_status_update(self):
        ref = self._post(self._body(), self._ip()).get_json()["data"]["reference"]
        staff = self._staff()
        rid = [i for i in staff.get(LIST).get_json()["data"]["items"] if i["reference"] == ref][0]["id"]
        bad = staff.post(f"{LIST}/{rid}/status", json={"status": "WHATEVER"})
        self.assertEqual(bad.status_code, 400)
        ok = staff.post(f"{LIST}/{rid}/status", json={"status": "contacted", "internal_note": "Called, will collect Monday"})
        self.assertEqual(ok.status_code, 200, ok.get_data(as_text=True))
        data = ok.get_json()["data"]
        self.assertEqual(data["status"], "CONTACTED")
        self.assertEqual(data["handled_by"], self.user[1])
        self.assertEqual(staff.post(f"{LIST}/nope/status", json={"status": "DONE"}).status_code, 404)


if __name__ == "__main__":
    unittest.main()
