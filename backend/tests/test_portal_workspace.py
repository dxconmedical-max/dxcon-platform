"""Tests for Sprint 009 doctor and patient portals."""

from __future__ import annotations

import unittest
import uuid

from app import create_app
from app.extensions.db import db
from app.doctor_portal.service import dashboard as doctor_dashboard, search_patients
from app.models.user import User
from app.patient_portal.service import patient_portal_report


class PortalWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.doctor = User(email=f"doc-{uuid.uuid4().hex[:6]}@test.local", role="DOCTOR", password_hash="x", is_active=True)
        self.patient = User(email=f"pat-{uuid.uuid4().hex[:6]}@test.local", role="PATIENT", password_hash="x", is_active=True)
        db.session.add_all([self.doctor, self.patient])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        try:
            db.drop_all()
        except Exception:
            pass
        self.ctx.pop()

    def test_doctor_dashboard(self):
        data = doctor_dashboard(doctor_id=self.doctor.id)
        self.assertIn("widgets", data)

    def test_patient_search(self):
        result = search_patients(q="P-")
        self.assertIn("data", result)

    def test_patient_portal_report(self):
        report = patient_portal_report()
        self.assertEqual(report["report"], "PATIENT_PORTAL_REPORT")

    def test_doctor_portal_ui(self):
        client = self.app.test_client()
        with client.session_transaction() as sess:
            sess["user_id"] = self.doctor.id
            sess["role"] = self.doctor.role
            sess["email"] = self.doctor.email
        self.assertEqual(client.get("/app/doctor/dashboard").status_code, 200)

    def test_patient_portal_ui(self):
        client = self.app.test_client()
        with client.session_transaction() as sess:
            sess["user_id"] = self.patient.id
            sess["role"] = self.patient.role
            sess["email"] = self.patient.email
        self.assertEqual(client.get("/app/patient/dashboard").status_code, 200)


if __name__ == "__main__":
    unittest.main()
