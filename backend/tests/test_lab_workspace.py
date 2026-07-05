"""Tests for Sprint 007 laboratory workspace."""

from __future__ import annotations

import unittest
import uuid

from app import create_app
from app.extensions.db import db
from app.lab_workspace.flags import calculate_abnormal_flag
from app.lab_workspace.service import workspace_dashboard
from app.models.user import User


class LabWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        user = User(email=f"lab-{uuid.uuid4().hex[:6]}@test.local", role="LAB", password_hash="x", is_active=True)
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

    def test_abnormal_flag_high(self):
        flag, warnings = calculate_abnormal_flag("10", reference_range="3-7")
        self.assertEqual(flag, "high")
        self.assertIsInstance(warnings, list)

    def test_workspace_dashboard(self):
        dash = workspace_dashboard()
        self.assertIn("kpis", dash)
        self.assertGreaterEqual(len(dash.get("widgets", [])), 8)

    def test_lab_ui_route(self):
        client = self.app.test_client()
        with client.session_transaction() as sess:
            sess["user_id"] = self.user.id
            sess["role"] = self.user.role
            sess["email"] = self.user.email
        resp = client.get("/app/lab")
        self.assertEqual(resp.status_code, 200)


if __name__ == "__main__":
    unittest.main()
