import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_tmp = tempfile.NamedTemporaryFile(prefix="dxcon_rolegate_", suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

ADMINS = {"SUPER_ADMIN", "SYSTEM_ADMIN", "ADMIN"}
EXPECTED = {
    "business_ui.create_patient": ADMINS | {"RECEPTION"},
    "business_ui.edit_patient": ADMINS | {"RECEPTION"},
    "business_ui.create_order": ADMINS | {"RECEPTION"},
    "business_ui.mark_paid": ADMINS | {"RECEPTION", "ACCOUNTING"},
    "business_ui.create_collection": ADMINS | {"RECEPTION", "COLLECTOR"},
    "business_ui.collect_sample": ADMINS | {"RECEPTION", "COLLECTOR"},
    "business_ui.receive_sample": ADMINS | {"LAB", "LAB_TECHNICIAN"},
    "business_ui.enter_results": ADMINS | {"LAB", "LAB_TECHNICIAN"},
    "business_ui.approve_result": ADMINS | {"DOCTOR", "LAB"},
    "business_ui.release_report": ADMINS | {"DOCTOR"},
    "business_ui.print_report": ADMINS | {"RECEPTION", "COLLECTOR", "ACCOUNTING", "LAB", "LAB_TECHNICIAN", "DOCTOR"},
    "launch_ui.app_system": ADMINS,
    "launch_ui.app_collector": ADMINS | {"COLLECTOR"},
    "mdm_web.mdm_dashboard": ADMINS,
}


def _roles_of(view):
    for cell in view.__closure__ or ():
        v = cell.cell_contents
        if isinstance(v, tuple) and v and all(isinstance(x, str) for x in v):
            return set(v)
    return None


class WebRoleGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import create_app
        from app.extensions.db import db

        cls.app = create_app()
        cls.app.config["TESTING"] = True
        with cls.app.app_context():
            db.create_all()
        cls.client = cls.app.test_client()

    def test_each_page_has_the_expected_role_list(self):
        for endpoint, expected in EXPECTED.items():
            view = self.app.view_functions[endpoint]
            self.assertEqual(_roles_of(view), expected, endpoint)

    def test_super_admin_is_always_allowed(self):
        for endpoint in EXPECTED:
            self.assertIn("SUPER_ADMIN", _roles_of(self.app.view_functions[endpoint]), endpoint)

    def test_wrong_role_is_sent_to_login(self):
        with self.client.session_transaction() as s:
            s["user_id"] = "u1"
            s["role"] = "PATIENT"
        for method, path in (
            ("post", "/app/business/orders/X/approve"),
            ("post", "/app/business/orders/X/mark-paid"),
            ("post", "/app/business/orders/X/release"),
            ("get", "/app/system"),
            ("get", "/app/mdm"),
            ("get", "/app/collector"),
        ):
            r = getattr(self.client, method)(path)
            self.assertEqual(r.status_code, 302, path)
            self.assertTrue(r.headers["Location"].endswith("/login"), path)


if __name__ == "__main__":
    unittest.main()
