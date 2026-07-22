"""Integration test: diagnostic workflow API happy path against business_engine."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.business_engine.statuses import ORDER_RELEASED
from app.extensions.db import db
from app.models.user import User


class DiagnosticWorkflowApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()

        self.user = User(
            email="workflow-admin@test.local",
            role="SUPER_ADMIN",
            password_hash="hash",
            is_active=True,
        )
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _auth_headers(self):
        # Dual-auth accepts session role for workflow endpoints.
        with self.client.session_transaction() as sess:
            sess["user_id"] = self.user.id
            sess["email"] = self.user.email
            sess["role"] = "SUPER_ADMIN"
        return {"X-Organization-ID": "org-test", "Content-Type": "application/json"}

    def test_happy_path_patient_to_released_report(self):
        headers = self._auth_headers()

        catalog = self.client.get("/api/v1/diagnostic-workflow/catalog", headers=headers)
        self.assertEqual(catalog.status_code, 200, catalog.get_json())
        items = catalog.get_json()["data"]["items"]
        self.assertGreater(len(items), 0)
        test_id = items[0]["id"]

        created = self.client.post(
            "/api/v1/diagnostic-workflow/patients",
            headers=headers,
            json={"full_name": "Workflow Patient", "phone": "0907000111"},
        )
        self.assertEqual(created.status_code, 201, created.get_json())
        patient_code = created.get_json()["data"]["patient_code"]

        order_res = self.client.post(
            "/api/v1/diagnostic-workflow/orders",
            headers=headers,
            json={"patient_code": patient_code, "test_catalog_ids": [test_id]},
        )
        self.assertEqual(order_res.status_code, 201, order_res.get_json())
        order = order_res.get_json()["data"]
        order_code = order["order_code"]
        self.assertEqual(order["milestone"], "ORDERED")

        steps = [
            ("pay", "ORDERED"),
            ("collection", "COLLECTION_SCHEDULED"),
            ("collect", "COLLECTED"),
            ("transit", "IN_TRANSIT"),
            ("receive", "RECEIVED_AT_LAB"),
            ("results", "PROCESSING"),
            ("qc", "PROCESSING"),
            ("approve", "APPROVED"),
            ("release", "RELEASED"),
        ]
        for path_suffix, milestone in steps:
            res = self.client.post(
                f"/api/v1/diagnostic-workflow/orders/{order_code}/{path_suffix}",
                headers=headers,
                json={},
            )
            self.assertIn(res.status_code, (200, 201), f"{path_suffix}: {res.get_json()}")
            payload = res.get_json()["data"]
            self.assertEqual(payload["milestone"], milestone, path_suffix)

        detail = self.client.get(
            f"/api/v1/diagnostic-workflow/orders/{order_code}",
            headers=headers,
        )
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.get_json()["data"]["status"], ORDER_RELEASED)

        report = self.client.get(
            f"/api/v1/diagnostic-workflow/orders/{order_code}/report",
            headers=headers,
        )
        self.assertEqual(report.status_code, 200, report.get_json())
        html = report.get_json()["data"]["html"]
        self.assertIn("DxCon Diagnostic Report", html)
        self.assertIn(order_code, html)

    def test_unauthenticated_is_rejected(self):
        res = self.client.get("/api/v1/diagnostic-workflow/catalog")
        self.assertIn(res.status_code, (401, 403, 422))


if __name__ == "__main__":
    unittest.main()
