"""Tests for Sprint 008 reporting engine."""

from __future__ import annotations

import unittest
import uuid

from app import create_app
from app.extensions.db import db
from app.models.user import User
from app.reporting_engine.report_generation_service import generate_report_code, generate_report_hash
from app.reporting_engine.service import reporting_engine_report, review_queue


class ReportingEngineTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        user = User(email=f"doc-{uuid.uuid4().hex[:6]}@test.local", role="DOCTOR", password_hash="x", is_active=True)
        db.session.add(user)
        db.session.commit()
        self.user = user

    def tearDown(self):
        db.session.remove()
        try:
            db.drop_all()
        except Exception:
            pass
        self.ctx.pop()

    def test_generate_report_code(self):
        code = generate_report_code()
        self.assertTrue(code.startswith("RPT-"))

    def test_generate_report_hash(self):
        h = generate_report_hash({"a": 1})
        self.assertEqual(len(h), 64)

    def test_review_queue(self):
        result = review_queue()
        self.assertIn("data", result)
        self.assertIn("pagination", result)

    def test_reporting_engine_report(self):
        report = reporting_engine_report()
        self.assertEqual(report["report"], "REPORTING_ENGINE_REPORT")

    def test_doctor_review_ui(self):
        client = self.app.test_client()
        with client.session_transaction() as sess:
            sess["user_id"] = self.user.id
            sess["role"] = self.user.role
            sess["email"] = self.user.email
        resp = client.get("/app/doctor/review")
        self.assertEqual(resp.status_code, 200)

    def test_reports_search_ui(self):
        client = self.app.test_client()
        with client.session_transaction() as sess:
            sess["user_id"] = self.user.id
            sess["role"] = self.user.role
            sess["email"] = self.user.email
        resp = client.get("/app/reports")
        self.assertEqual(resp.status_code, 200)


if __name__ == "__main__":
    unittest.main()
