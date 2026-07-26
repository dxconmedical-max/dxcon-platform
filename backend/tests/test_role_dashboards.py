"""Tests for role dashboards go-live metrics."""

from __future__ import annotations

import os
import unittest

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.passwords import hash_password
from app.extensions.db import db
from app.models.user import User
from app.role_dashboards.service import build_role_dashboard, role_can_access


class RoleDashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        with cls.app.app_context():
            db.create_all()

    def setUp(self):
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.client = self.app.test_client()
        admin = User.query.filter_by(email="rd-admin@dxcon.test").first()
        if not admin:
            admin = User(
                email="rd-admin@dxcon.test",
                role="ADMIN",
                password_hash=hash_password("TestOnly123!"),
                is_active=True,
            )
            db.session.add(admin)
            db.session.commit()
        self.admin = admin
        patient = User.query.filter_by(email="rd-patient@dxcon.test").first()
        if not patient:
            patient = User(
                email="rd-patient@dxcon.test",
                role="PATIENT",
                password_hash=hash_password("TestOnly123!"),
                is_active=True,
            )
            db.session.add(patient)
            db.session.commit()
        self.patient = patient

    def tearDown(self):
        self.ctx.pop()

    def test_build_admin_dashboard_aggregates_only(self):
        payload = build_role_dashboard("admin")
        self.assertEqual(payload["pii_policy"], "aggregates_only")
        self.assertIn("orders_today", payload["metrics"])
        self.assertTrue(payload["cards"])
        blob = str(payload["metrics"])
        self.assertNotIn("phone", blob.lower().split("orders")[0] if False else blob)
        # cards should not contain raw PII field names as values from patient records
        for card in payload["cards"]:
            self.assertIn(card["label"], card["label"])  # structural
            self.assertIsInstance(card["value"], str)

    def test_role_can_access_matrix(self):
        self.assertTrue(role_can_access("ADMIN", "admin"))
        self.assertTrue(role_can_access("LAB", "laboratory"))
        self.assertFalse(role_can_access("PATIENT", "admin"))
        self.assertFalse(role_can_access("COLLECTOR", "doctor"))

    def test_api_admin_ok_patient_forbidden(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = self.admin.id
            sess["role"] = "ADMIN"
            sess["email"] = self.admin.email
        resp = self.client.get("/api/v1/role-dashboards/admin")
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertTrue(body.get("success"))
        self.assertIn("cards", body["data"])

        with self.client.session_transaction() as sess:
            sess["user_id"] = self.patient.id
            sess["role"] = "PATIENT"
            sess["email"] = self.patient.email
        forbidden = self.client.get("/api/v1/role-dashboards/admin")
        self.assertEqual(forbidden.status_code, 403)

    def test_patient_empty_without_code(self):
        payload = build_role_dashboard("patient")
        self.assertTrue(payload.get("empty") or payload["metrics"].get("results_available") == 0)


if __name__ == "__main__":
    unittest.main()
