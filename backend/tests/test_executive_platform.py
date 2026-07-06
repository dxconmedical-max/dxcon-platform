"""Tests for Sprint 010 executive platform."""

from __future__ import annotations

import os
import unittest
import uuid

from app import create_app
from app.executive_platform.service import executive_dashboard, security_report
from app.extensions.db import db
from app.infrastructure.storage_service import StorageService
from app.models.user import User


class ExecutivePlatformTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.admin = User(email=f"adm-{uuid.uuid4().hex[:6]}@test.local", role="SUPER_ADMIN", password_hash="x", is_active=True)
        db.session.add(self.admin)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        try:
            db.drop_all()
        except Exception:
            pass
        self.ctx.pop()

    def test_executive_dashboard(self):
        data = executive_dashboard()
        self.assertIn("widgets", data)
        self.assertIn("charts", data)

    def test_security_report(self):
        report = security_report()
        self.assertEqual(report["report"], "SECURITY_REPORT")

    def test_storage_local(self):
        import tempfile
        os.environ["UPLOAD_FOLDER"] = tempfile.mkdtemp()
        svc = StorageService(provider="local")
        result = svc.store("test", "sample.txt", b"data")
        self.assertEqual(result["provider"], "local")

    def test_executive_ui(self):
        client = self.app.test_client()
        with client.session_transaction() as sess:
            sess["user_id"] = self.admin.id
            sess["role"] = self.admin.role
            sess["email"] = self.admin.email
        self.assertEqual(client.get("/app/executive").status_code, 200)
        self.assertEqual(client.get("/app/crm").status_code, 200)


if __name__ == "__main__":
    unittest.main()
