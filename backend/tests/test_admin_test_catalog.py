import os
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_tmp = tempfile.NamedTemporaryFile(prefix="dxcon_catalog_", suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

URL = "/api/v1/admin/test-catalog/import"


class AdminTestCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import create_app
        from app.core.passwords import hash_password
        from app.extensions.db import db
        from app.models.partner_foundation import OrganizationUser, PartnerOrganization
        from app.models.test_catalog import TestCatalog
        from app.models.user import User
        from app.partner_foundation.service import seed_organization_roles

        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.tag = uuid.uuid4().hex[:6].upper()
        with cls.app.app_context():
            db.create_all()
            seed_organization_roles()
            org = PartnerOrganization(
                organization_code=f"CT-INT-{cls.tag}", organization_name=f"Catalog internal {cls.tag}",
                organization_type="DXCON_INTERNAL",
            )
            db.session.add(org)
            db.session.flush()
            cls.users = {}
            for role in ("ADMIN", "RECEPTION"):
                email = f"{role.lower()}-{cls.tag}@placeholder.dxcon.test".lower()
                user = User(email=email, role=role, password_hash=hash_password("Str0ng-pass-123"),
                            is_active=True, organization_id=org.id)
                db.session.add(user)
                db.session.flush()
                db.session.add(OrganizationUser(organization_id=org.id, user_id=user.id, role_code="ORG_OWNER", active=True))
                cls.users[role] = (user.id, email)
            db.session.add(TestCatalog(code="DEMO-TST-001", name="Demo Test 1", price=10))
            db.session.add(TestCatalog(code="KEEP-1", name="Old name", category="X", sample_type="Blood", price=5))
            db.session.commit()

    def _client(self, role="ADMIN"):
        client = self.app.test_client()
        with client.session_transaction() as s:
            s["user_id"], s["role"], s["email"] = self.users[role][0], role, self.users[role][1]
        return client

    def _rows(self):
        return [
            {"code": "T-1", "name": "Test one", "category": "Immunology", "sample_type": "Blood", "price": 100000},
            {"code": "KEEP-1", "name": "New name", "category": "X", "sample_type": "Blood", "price": 7},
            {"code": "T-1", "name": "Test one (dup, last wins)", "category": "Immunology", "sample_type": "Blood", "price": 120000},
        ]

    def test_reception_is_forbidden(self):
        res = self._client("RECEPTION").post(URL, json={"rows": self._rows()})
        self.assertIn(res.status_code, (401, 403))
        self.assertIn(self.app.test_client().post(URL, json={"rows": self._rows()}).status_code, (401, 403))

    def test_preview_changes_nothing_then_apply(self):
        from app.models.test_catalog import TestCatalog

        client = self._client()
        res = client.post(URL, json={"rows": self._rows(), "remove_demo": True})
        self.assertEqual(res.status_code, 200, res.get_data(as_text=True))
        data = res.get_json()["data"]
        self.assertEqual((data["create"], data["update"], data["demo_present"], data["applied"]), (1, 1, 1, False))
        with self.app.app_context():
            self.assertIsNone(TestCatalog.query.filter_by(code="T-1").first())
        res = client.post(URL, json={"rows": self._rows(), "apply": True, "remove_demo": True})
        self.assertEqual(res.status_code, 200, res.get_data(as_text=True))
        self.assertTrue(res.get_json()["data"]["applied"])
        with self.app.app_context():
            self.assertEqual(TestCatalog.query.filter_by(code="T-1").first().price, 120000)
            self.assertEqual(TestCatalog.query.filter_by(code="KEEP-1").first().name, "New name")
            self.assertIsNone(TestCatalog.query.filter_by(code="DEMO-TST-001").first())
        again = client.post(URL, json={"rows": self._rows()}).get_json()["data"]
        self.assertEqual((again["create"], again["update"], again["unchanged"]), (0, 0, 2))

    def test_validation(self):
        client = self._client()
        self.assertEqual(client.post(URL, json={"rows": []}).status_code, 400)
        self.assertEqual(client.post(URL, json={"rows": [{"code": "", "name": "x", "price": 1}]}).status_code, 400)
        self.assertEqual(client.post(URL, json={"rows": [{"code": "A", "name": "", "price": 1}]}).status_code, 400)
        self.assertEqual(client.post(URL, json={"rows": [{"code": "A", "name": "x", "price": "abc"}]}).status_code, 400)
        self.assertEqual(client.post(URL, json={"rows": [{"code": "A", "name": "x", "price": -1}]}).status_code, 400)


if __name__ == "__main__":
    unittest.main()
