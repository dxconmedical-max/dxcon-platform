import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_tmp = tempfile.NamedTemporaryFile(prefix="dxcon_clinicreq_", suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"


class ClinicOrderRequestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import create_app
        from app.extensions.db import db

        cls.app = create_app()
        cls.app.config["TESTING"] = True
        with cls.app.app_context():
            db.create_all()

    def test_every_endpoint_requires_login(self):
        c = self.app.test_client()
        for method, url in [
            ("get", "/api/v1/clinic-orders/status"),
            ("get", "/api/v1/clinic-orders/tests"),
            ("post", "/api/v1/clinic-orders/requests"),
            ("get", "/api/v1/clinic-orders/requests"),
            ("get", "/api/v1/reception/workspace/clinic-requests"),
            ("post", "/api/v1/reception/workspace/clinic-requests/x/approve"),
            ("post", "/api/v1/reception/workspace/clinic-requests/x/reject"),
            ("get", "/api/v1/reception/workspace/clinic-order-settings"),
            ("post", "/api/v1/reception/workspace/clinic-order-settings/x"),
        ]:
            r = getattr(c, method)(url)
            self.assertIn(r.status_code, (401, 403), f"{method} {url} -> {r.status_code}")

    def test_validation(self):
        from app.api.clinic_orders.routes import _validate
        from app.extensions.db import db
        from app.models.test_catalog import TestCatalog

        with self.app.app_context():
            t = TestCatalog(code="GLU", name="Glucose", price=10000)
            db.session.add(t)
            db.session.commit()
            good = {"patient_name": "Nguyễn Văn A", "birth_year": 1985, "tube_count": 2, "test_ids": [t.id]}
            values, error = _validate(good)
            self.assertIsNone(error)
            self.assertEqual(values["tests"][0]["code"], "GLU")
            for bad in (
                {**good, "patient_name": ""},
                {**good, "birth_year": 1800},
                {**good, "birth_year": 2999},
                {**good, "birth_year": "abc"},
                {**good, "tube_count": 0},
                {**good, "tube_count": 99},
                {**good, "test_ids": []},
                {**good, "test_ids": ["does-not-exist"]},
            ):
                _, error = _validate(bad)
                self.assertIsNotNone(error, bad)


if __name__ == "__main__":
    unittest.main()
