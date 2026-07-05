"""Tests for Sprint 006 reception operational workspace."""

from __future__ import annotations

import unittest
import uuid

from app import create_app
from app.business_engine import service as biz
from app.extensions.db import db
from app.models.user import User
from app.reception_workspace.service import duplicate_warnings, fast_search_patients, workspace_dashboard


class ReceptionWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        biz.ensure_test_catalog_seed()
        user = User(
            email=f"reception-{uuid.uuid4().hex[:6]}@test.local",
            role="RECEPTION",
            password_hash="x",
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()
        self.user = user

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_workspace_dashboard(self):
        dash = workspace_dashboard()
        self.assertIn("kpis", dash)
        self.assertGreaterEqual(len(dash.get("widgets", [])), 8)

    def test_fast_search_empty_query(self):
        result = fast_search_patients("")
        self.assertIn("data", result)
        self.assertIn("pagination", result)

    def test_duplicate_warnings_empty(self):
        self.assertEqual(duplicate_warnings(phone="0000000000"), [])

    def test_reception_ui_route(self):
        client = self.app.test_client()
        with client.session_transaction() as sess:
            sess["user_id"] = self.user.id
            sess["role"] = self.user.role
            sess["email"] = self.user.email
        resp = client.get("/app/reception")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Reception Workspace", resp.data)


if __name__ == "__main__":
    unittest.main()
