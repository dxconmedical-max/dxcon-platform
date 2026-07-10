"""Tests for Pilot Readiness API — Epic 8."""

from __future__ import annotations

import os
import unittest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app import create_app
from app.extensions.db import db
from app.pilot_readiness.audit import run_production_readiness_audit
from app.pilot_readiness.models import PartnerRegistration


class PilotReadinessTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_audit_public(self):
        with self.app.app_context():
            audit = run_production_readiness_audit(self.app)
        self.assertIn("production_readiness_score", audit)
        self.assertGreaterEqual(audit["production_readiness_score"], 0)

    def test_audit_endpoint(self):
        res = self.client.get("/api/v1/pilot-readiness/audit")
        self.assertEqual(res.status_code, 200)
        self.assertIn("production_readiness_score", res.get_json()["data"])

    def test_partner_self_registration(self):
        res = self.client.post(
            "/api/v1/pilot-readiness/partner-registration",
            json={
                "partner_type": "CLINIC",
                "organization_name": "Demo Clinic",
                "contact_email": "clinic@example.com",
            },
        )
        self.assertEqual(res.status_code, 201)
        self.assertEqual(PartnerRegistration.query.count(), 1)

    def test_onboarding_flow(self):
        start = self.client.post(
            "/api/v1/pilot-readiness/onboarding",
            json={"onboarding_type": "LABORATORY", "requester_email": "lab@example.com"},
        )
        self.assertEqual(start.status_code, 201)
        code = start.get_json()["data"]["session_code"]
        detail = self.client.get(f"/api/v1/pilot-readiness/onboarding/{code}")
        self.assertEqual(detail.status_code, 200)
        self.assertIn("steps", detail.get_json()["data"])

    def test_subscription_plans(self):
        res = self.client.get("/api/v1/pilot-readiness/subscription-plans")
        self.assertEqual(res.status_code, 200)
        plans = res.get_json()["data"]
        self.assertGreaterEqual(len(plans), 4)

    def test_knowledge_base(self):
        res = self.client.get("/api/v1/pilot-readiness/knowledge")
        self.assertEqual(res.status_code, 200)
        self.assertGreater(len(res.get_json()["data"]), 0)

    def test_operations_center_wired(self):
        res = self.client.get("/api/v1/operations-center/dashboard")
        self.assertIn(res.status_code, (200, 401, 403))


if __name__ == "__main__":
    unittest.main()
