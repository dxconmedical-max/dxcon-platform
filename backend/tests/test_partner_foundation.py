"""Tests for Sprint 005 partner foundation."""

from __future__ import annotations

import unittest
import uuid

from app import create_app
from app.extensions.db import db
from app.partner_foundation.rbac import org_role_has_permission
from app.partner_foundation.service import (
    ensure_default_organization,
    organization_dashboard,
    permission_matrix,
    query_organizations,
    seed_organization_roles,
    upsert_organization,
)


class PartnerFoundationTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        seed_organization_roles()
        ensure_default_organization()
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_ensure_default_organization(self):
        org = ensure_default_organization()
        self.assertEqual(org.organization_code, "DXCON_INTERNAL")
        db.session.commit()
        again = ensure_default_organization()
        self.assertEqual(again.id, org.id)

    def test_organization_upsert_and_query(self):
        tag = uuid.uuid4().hex[:6]
        upsert_organization(
            {
                "organization_code": f"T-{tag}",
                "organization_name": "Test Org",
                "organization_type": "CLINIC",
            },
            actor="test@dxcon.test",
        )
        db.session.commit()
        result = query_organizations(search=f"T-{tag}")
        self.assertGreaterEqual(result["pagination"]["total"], 1)

    def test_rbac_permissions(self):
        self.assertTrue(org_role_has_permission("ORG_OWNER", "org.create"))
        self.assertFalse(org_role_has_permission("VIEWER", "org.delete"))

    def test_permission_matrix_seeded(self):
        matrix = permission_matrix()
        self.assertGreaterEqual(len(matrix.get("roles", [])), 5)
        codes = {r["role_code"] for r in matrix["roles"]}
        self.assertIn("ORG_OWNER", codes)
        self.assertIn("VIEWER", codes)


if __name__ == "__main__":
    unittest.main()
