import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.web import result_upload


class PortalFileAccessTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.item = SimpleNamespace(order_id="o1")

    def _check(self, session_data):
        with self.app.test_request_context("/"):
            from flask import session

            session.update(session_data)
            with mock.patch.object(result_upload.Order, "query") as q:
                q.get.return_value = SimpleNamespace(patient_id="p1")
                return result_upload._may_download_result_file(self.item)

    def test_staff_allowed(self):
        self.assertTrue(self._check({"role": "LAB_TECHNICIAN"}))

    def test_owner_patient_allowed(self):
        self.assertTrue(self._check({"patient_id": "p1"}))

    def test_other_patient_denied(self):
        self.assertFalse(self._check({"patient_id": "p2"}))

    def test_logged_in_without_role_or_patient_denied(self):
        self.assertFalse(self._check({"user_id": "u1", "role": "CLINIC_VIEWER"}))


if __name__ == "__main__":
    unittest.main()
