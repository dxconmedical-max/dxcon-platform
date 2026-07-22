"""Integration test: reception workspace workflow happy path."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.business_engine import service as biz
from app.business_engine.statuses import ORDER_IN_TRANSIT, ORDER_PAID
from app.extensions.db import db
from app.models.user import User


class ReceptionWorkflowApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()
        biz.ensure_test_catalog_seed()

        self.user = User(
            email="reception@test.local",
            role="RECEPTION",
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
        with self.client.session_transaction() as sess:
            sess["user_id"] = self.user.id
            sess["email"] = self.user.email
            sess["role"] = "RECEPTION"
        return {"X-Organization-ID": "org-test", "Content-Type": "application/json"}

    def test_reception_workflow_patient_to_lab_queue(self):
        headers = self._auth_headers()

        register = self.client.post(
            "/api/v1/reception/workspace/patients/register",
            headers=headers,
            json={
                "full_name": "Reception Workflow Patient",
                "phone": "0907111222",
                "national_id": "NID-RX-001",
            },
        )
        self.assertEqual(register.status_code, 201, register.get_json())
        patient_code = register.get_json()["data"]["patient"]["patient_code"]

        search = self.client.get(
            f"/api/v1/reception/workspace/search?q={patient_code}",
            headers=headers,
        )
        self.assertEqual(search.status_code, 200, search.get_json())
        search_body = search.get_json()
        self.assertGreater(len(search_body["data"]), 0, search_body)
        self.assertTrue(
            any(row.get("patient_code") == patient_code for row in search_body["data"]),
            search_body["data"],
        )

        tests = self.client.get("/api/v1/reception/workspace/tests", headers=headers)
        self.assertEqual(tests.status_code, 200, tests.get_json())
        test_id = tests.get_json()["data"][0]["id"]

        order_res = self.client.post(
            "/api/v1/reception/workspace/orders",
            headers=headers,
            json={"patient_code": patient_code, "test_catalog_ids": [test_id], "discount": 0},
        )
        self.assertEqual(order_res.status_code, 201, order_res.get_json())
        order_body = order_res.get_json()["data"]
        order_code = order_body["order"]["order_code"]
        self.assertGreater(order_body["pricing"]["total"], 0)

        pay = self.client.post(
            f"/api/v1/reception/workspace/orders/{order_code}/payment",
            headers=headers,
            json={"payment_method": "cash"},
        )
        self.assertEqual(pay.status_code, 200, pay.get_json())
        self.assertEqual(pay.get_json()["data"]["order_status"], ORDER_PAID)
        self.assertIn("barcodes", pay.get_json()["data"])

        collection = self.client.post(
            f"/api/v1/reception/workspace/orders/{order_code}/collection",
            headers=headers,
            json={"collector_name": "Walk-in Collector", "pickup_address": "Reception Desk"},
        )
        self.assertEqual(collection.status_code, 201, collection.get_json())

        collect = self.client.post(
            f"/api/v1/reception/workspace/orders/{order_code}/collect",
            headers=headers,
            json={},
        )
        self.assertEqual(collect.status_code, 200, collect.get_json())

        transit = self.client.post(
            f"/api/v1/reception/workspace/orders/{order_code}/transit",
            headers=headers,
            json={},
        )
        self.assertEqual(transit.status_code, 200, transit.get_json())
        self.assertEqual(transit.get_json()["data"]["status"], ORDER_IN_TRANSIT)

        barcodes = self.client.get(
            f"/api/v1/reception/workspace/orders/{order_code}/barcode",
            headers=headers,
        )
        self.assertEqual(barcodes.status_code, 200, barcodes.get_json())
        self.assertTrue(barcodes.get_json()["data"]["order_barcode"])

        request_form = self.client.get(
            f"/api/v1/reception/workspace/orders/{order_code}/request-form",
            headers=headers,
        )
        self.assertEqual(request_form.status_code, 200, request_form.get_json())
        self.assertIn("html", request_form.get_json()["data"])

        incoming = biz.list_lab_incoming(limit=20)
        self.assertTrue(any(row["order_code"] == order_code for row in incoming))

        dashboard = self.client.get("/api/v1/reception/workspace/dashboard", headers=headers)
        self.assertEqual(dashboard.status_code, 200, dashboard.get_json())
        self.assertIn("kpis", dashboard.get_json()["data"])

    def test_unauthenticated_reception_workflow_is_rejected(self):
        res = self.client.get("/api/v1/reception/workspace/tests")
        self.assertIn(res.status_code, (401, 403, 422))


if __name__ == "__main__":
    unittest.main()
