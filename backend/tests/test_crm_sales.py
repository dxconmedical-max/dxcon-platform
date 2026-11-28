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

    def _csv(self, text):
        import io

        return {"file": (io.BytesIO(text.encode("utf-8")), "khach.csv"), "apply": "0"}

    def test_import_dry_run_then_apply_skips_duplicates_and_reports_errors(self):
        a = self._as("sale_a")
        head = "Tên,Loại,Liên hệ,Điện thoại,Địa chỉ,Quận,Ca,Giai đoạn,Hẹn,Ghi chú,Sale\n"
        body = (
            "PK Import Một,Phòng khám,BS A,0901,1 ABC,Quận 1,30,Đã gặp,2026-12-01 00:00:00,ghi chú,\n"
            "PK Import Hai,Bệnh viện,,,,,,,,,\n"
            ",Phòng khám,,,,,,,,,\n"
            "PK Import Ba,Loại lạ,,,,,,,,,\n"
            "pk import một,Phòng khám,,,,,,,,,\n"
        )
        data = self._csv(head + body)
        r = a.post(f"{B}/accounts/import", data=data, content_type="multipart/form-data")
        self.assertEqual(r.status_code, 200)
        j = r.get_json()["data"]
        self.assertEqual((j["applied"], j["created"], j["error_count"], j["skipped_count"]), (False, 2, 2, 1))
        self.assertEqual(a.get(f"{B}/accounts?q=PK Import").get_json()["data"]["accounts"], [])  # dry run saved nothing
        data = self._csv(head + body)
        data["apply"] = "1"
        r = a.post(f"{B}/accounts/import", data=data, content_type="multipart/form-data")
        self.assertEqual(r.get_json()["data"]["created"], 2)
        mine = a.get(f"{B}/accounts?q=PK Import").get_json()["data"]["accounts"]
        self.assertEqual(sorted(x["name"] for x in mine), ["PK Import Hai", "PK Import Một"])
        one = [x for x in mine if x["name"] == "PK Import Một"][0]
        self.assertEqual((one["stage"], one["est_monthly_cases"], one["next_followup_date"], one["owner_user_id"]), ("MET", 30, "2026-12-01", self.users["sale_a"][0]))
        # another sale cannot see them; re-import is all duplicates
        self.assertEqual(self._as("sale_b").get(f"{B}/accounts?q=PK Import").get_json()["data"]["accounts"], [])
        again = self._csv(head + body)
        again["apply"] = "1"
        self.assertEqual(a.post(f"{B}/accounts/import", data=again, content_type="multipart/form-data").get_json()["data"]["created"], 0)

    def test_import_admin_assigns_owner_by_email_and_sale_cannot(self):
        admin, sale_b = self._as("admin"), self._as("sale_b")
        head = "Tên,Loại,Liên hệ,Điện thoại,Địa chỉ,Quận,Ca,Giai đoạn,Hẹn,Ghi chú,Sale\n"
        line = f"PK Giao Sale,Phòng khám,,,,,,,,,{self.users['sale_b'][1]}\nPK Sale Sai,Phòng khám,,,,,,,,,nobody@x.test\n"
        d = self._csv(head + line)
        d["apply"] = "1"
        j = admin.post(f"{B}/accounts/import", data=d, content_type="multipart/form-data").get_json()["data"]
        self.assertEqual((j["created"], j["error_count"]), (1, 1))
        self.assertEqual([x["name"] for x in sale_b.get(f"{B}/accounts?q=PK Giao").get_json()["data"]["accounts"]], ["PK Giao Sale"])
        # a sale's owner column is ignored: they own what they import
        d2 = self._csv(head + f"PK Sale Tu Nhap,Phòng khám,,,,,,,,,{self.users['sale_b'][1]}\n")
        d2["apply"] = "1"
        self._as("sale_a").post(f"{B}/accounts/import", data=d2, content_type="multipart/form-data")
        mine = self._as("sale_a").get(f"{B}/accounts?q=Tu Nhap").get_json()["data"]["accounts"]
        self.assertEqual(mine[0]["owner_user_id"], self.users["sale_a"][0])

    def test_exports_are_excel_and_sale_export_has_no_margin(self):
        from io import BytesIO

        from openpyxl import load_workbook

        self._as("sale_a").post(f"{B}/accounts", json={"name": "=HYPERLINK(1)"})
        r = self._as("sale_a").get(f"{B}/accounts/export")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.data.startswith(b"PK"))
        ws = load_workbook(BytesIO(r.data)).active
        header = [c.value for c in ws[1]]
        self.assertFalse(any(str(h).startswith("Lãi") for h in header))
        self.assertTrue(any(str(c.value).startswith("'=") for row in ws.iter_rows(min_row=2) for c in row))  # formula neutralised
        admin_ws = load_workbook(BytesIO(self._as("admin").get(f"{B}/accounts/export").data)).active
        self.assertTrue(any(str(c.value).startswith("Lãi") for c in admin_ws[1]))
        t = self._as("sale_a").get(f"{B}/accounts/import/template")
        self.assertEqual(t.status_code, 200)
        self.assertIn(self._as("reception").get(f"{B}/accounts/export").status_code, (401, 403))
        self.assertIn(self.app.test_client().post(f"{B}/accounts/import").status_code, (401, 403))

    def test_market_by_district_groups_and_hides_margin_from_sale(self):
        a, b, admin = self._as("sale_a"), self._as("sale_b"), self._as("admin")
        a.post(f"{B}/accounts", json={"name": "PK Quận Một A", "district": "Quận 77", "est_monthly_cases": 30, "stage": "ACTIVE"})
        a.post(f"{B}/accounts", json={"name": "PK Quận Một B", "district": "Quận 77", "est_monthly_cases": 20})
        a.post(f"{B}/accounts", json={"name": "PK Không Quận", "est_monthly_cases": 5})
        mine = {r["district"]: r for r in a.get(f"{B}/market").get_json()["data"]["districts"]}
        self.assertEqual((mine["Quận 77"]["accounts"], mine["Quận 77"]["est_monthly_cases"], mine["Quận 77"]["active_accounts"]), (2, 50, 1))
        self.assertIn("Chưa rõ khu vực", mine)
        self.assertIsNone(mine["Quận 77"]["share_pct"])  # nothing linked to an organization yet
        self.assertNotIn("margin", mine["Quận 77"])
        self.assertNotIn("Quận 77", [r["district"] for r in b.get(f"{B}/market").get_json()["data"]["districts"]])
        adm = {r["district"]: r for r in admin.get(f"{B}/market").get_json()["data"]["districts"]}
        self.assertIn("margin", adm["Quận 77"])
        self.assertIn(self._as("reception").get(f"{B}/market").status_code, (401, 403))
        self.assertIn(self.app.test_client().get(f"{B}/market").status_code, (401, 403))


if __name__ == "__main__":
    unittest.main()
