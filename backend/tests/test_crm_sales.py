import os
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_tmp = tempfile.NamedTemporaryFile(prefix="dxcon_crm_", suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

B = "/api/v1/reception/workspace/crm"


class CrmSalesTests(unittest.TestCase):
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
        tag = uuid.uuid4().hex[:6]
        cls.users = {}
        with cls.app.app_context():
            db.create_all()
            seed_organization_roles()
            org = PartnerOrganization(organization_code=f"CRM-{tag}".upper(), organization_name=f"CRM internal {tag}", organization_type="DXCON_INTERNAL")
            db.session.add(org)
            db.session.flush()
            for key, role in (("admin", "ADMIN"), ("sale_a", "SALE"), ("sale_b", "SALE"), ("reception", "RECEPTION")):
                email = f"{key}-{tag}@placeholder.dxcon.test"
                u = User(email=email, role=role, password_hash=hash_password("Str0ng-pass-123"), is_active=True, organization_id=org.id)
                db.session.add(u)
                db.session.flush()
                db.session.add(OrganizationUser(organization_id=org.id, user_id=u.id, role_code="ORG_OWNER" if role == "ADMIN" else "VIEWER", active=True))
                cls.users[key] = (u.id, email, role)
            db.session.commit()

    def _as(self, key):
        client = self.app.test_client()
        uid, email, role = self.users[key]
        with client.session_transaction() as s:
            s["user_id"], s["role"], s["email"] = uid, role, email
        return client

    def test_login_required(self):
        c = self.app.test_client()
        for method, url in [
            ("get", f"{B}/accounts"),
            ("post", f"{B}/accounts"),
            ("get", f"{B}/accounts/x"),
            ("post", f"{B}/accounts/x"),
            ("post", f"{B}/accounts/x/activities"),
            ("get", f"{B}/sales"),
            ("post", f"{B}/sales/x/target"),
        ]:
            self.assertIn(getattr(c, method)(url).status_code, (401, 403), f"{method} {url}")

    def test_other_staff_roles_are_rejected(self):
        self.assertIn(self._as("reception").get(f"{B}/accounts").status_code, (401, 403))

    def test_sale_sees_only_own_accounts_and_no_margin(self):
        a, b, admin = self._as("sale_a"), self._as("sale_b"), self._as("admin")
        created = a.post(f"{B}/accounts", json={"name": "Phòng khám A", "est_monthly_cases": 40, "owner_user_id": self.users["sale_b"][0]})
        self.assertEqual(created.status_code, 201)
        acc_id = created.get_json()["data"]["id"]
        # owner passed by a sale is ignored: sale A owns what A creates
        mine = a.get(f"{B}/accounts").get_json()["data"]
        self.assertFalse(mine["is_admin"])
        self.assertEqual([r["name"] for r in mine["accounts"]], ["Phòng khám A"])
        self.assertEqual(mine["accounts"][0]["owner_user_id"], self.users["sale_a"][0])
        self.assertNotIn("margin", mine["accounts"][0])
        self.assertNotIn("margin", mine["totals"])
        # other sale cannot see, read or edit it
        self.assertEqual(b.get(f"{B}/accounts").get_json()["data"]["accounts"], [])
        self.assertEqual(b.get(f"{B}/accounts/{acc_id}").status_code, 404)
        self.assertEqual(b.post(f"{B}/accounts/{acc_id}", json={"name": "hijack"}).status_code, 404)
        self.assertEqual(b.post(f"{B}/accounts/{acc_id}/activities", json={"kind": "NOTE", "summary": "x"}).status_code, 404)
        # admin sees it and can reassign, a sale cannot reassign
        self.assertIn("Phòng khám A", [r["name"] for r in admin.get(f"{B}/accounts").get_json()["data"]["accounts"]])
        a.post(f"{B}/accounts/{acc_id}", json={"owner_user_id": self.users["sale_b"][0]})
        self.assertEqual(admin.get(f"{B}/accounts/{acc_id}").get_json()["data"]["account"]["owner_user_id"], self.users["sale_a"][0])
        ok = admin.post(f"{B}/accounts/{acc_id}", json={"owner_user_id": self.users["sale_b"][0]})
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(b.get(f"{B}/accounts/{acc_id}").status_code, 200)
        bad = admin.post(f"{B}/accounts/{acc_id}", json={"owner_user_id": self.users["reception"][0]})
        self.assertEqual(bad.status_code, 400)

    def test_activity_log_and_followup(self):
        a = self._as("sale_a")
        acc_id = a.post(f"{B}/accounts", json={"name": "Phòng khám log"}).get_json()["data"]["id"]
        self.assertEqual(a.post(f"{B}/accounts/{acc_id}/activities", json={"kind": "NOPE", "summary": "x"}).status_code, 400)
        self.assertEqual(a.post(f"{B}/accounts/{acc_id}/activities", json={"kind": "CALL", "summary": "Gọi giới thiệu", "next_followup_date": "2020-01-01"}).status_code, 201)
        detail = a.get(f"{B}/accounts/{acc_id}").get_json()["data"]
        self.assertEqual(detail["activities"][0]["summary"], "Gọi giới thiệu")
        row = [r for r in a.get(f"{B}/accounts").get_json()["data"]["accounts"] if r["id"] == acc_id][0]
        self.assertTrue(row["followup_overdue"])

    def test_sales_endpoints_are_admin_only(self):
        self.assertIn(self._as("sale_a").get(f"{B}/sales").status_code, (401, 403))
        self.assertIn(self._as("sale_a").post(f"{B}/sales/{self.users['sale_a'][0]}/target", json={"target_cases": 5}).status_code, (401, 403))
        admin = self._as("admin")
        self.assertEqual(admin.post(f"{B}/sales/{self.users['sale_a'][0]}/target", json={"target_cases": 50, "target_revenue": 10000000}).status_code, 200)
        rows = admin.get(f"{B}/sales").get_json()["data"]["sales"]
        mine = [r for r in rows if r["user_id"] == self.users["sale_a"][0]][0]
        self.assertEqual(mine["target_cases"], 50)

    def test_sale_is_an_assignable_platform_role(self):
        from app.core.roles import ALL_ROLES
        from app.web_gateway.routing import workspace_path_for_role

        self.assertIn("SALE", ALL_ROLES)
        self.assertEqual(workspace_path_for_role("SALE"), "/app/sales")


if __name__ == "__main__":
    unittest.main()
