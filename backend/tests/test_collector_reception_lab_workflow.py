"""Legacy bridge tests updated for collection_mode ownership."""

from __future__ import annotations

import os
import tempfile
import unittest
import uuid

_TEST_DB = tempfile.NamedTemporaryFile(prefix="dxcon_crl2_", suffix=".db", delete=False)
_TEST_DB.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB.name}"

from app import create_app
from app.business_engine import service as biz
from app.extensions.db import db
from app.models.sample_collection import SampleCollection
from app.models.test_catalog import TestCatalog
from app.models.user import User
from app.reception_workspace.service import create_reception_order
from app.sample_collection_workspace.collection_domain import (
    MODE_AT_RECEPTION,
    ST_REQUESTED,
    normalize_status,
)
from app.sample_collection_workspace.collection_routing import (
    ensure_desk_sample_collection,
    list_reception_desk_queue,
)
from app.sample_collection_workspace.service import list_production_queue


class CollectorReceptionLabWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.drop_all()
        db.create_all()
        biz.ensure_test_catalog_seed()
        self.admin = User(
            email=f"sa-{uuid.uuid4().hex[:6]}@test.local",
            role="SUPER_ADMIN",
            password_hash="x",
            is_active=True,
        )
        db.session.add(self.admin)
        db.session.commit()
        self.test = TestCatalog.query.first()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _create_reception_order(self):
        patient = biz.create_patient(
            full_name="CRL WORKFLOW PATIENT",
            phone=f"0988{uuid.uuid4().hex[:6]}",
            patient_code=f"P-CRL-{uuid.uuid4().hex[:6].upper()}",
            actor=self.admin.email,
        )
        result = create_reception_order(
            patient_code=patient.patient_code,
            test_catalog_ids=[self.test.id],
            collection_mode=MODE_AT_RECEPTION,
            actor=self.admin.email,
        )
        db.session.commit()
        return result

    def test_reception_order_creates_sample_collection(self):
        result = self._create_reception_order()
        order = result["order"]
        self.assertIn("sample_collection_id", result)
        sc = SampleCollection.query.get(result["sample_collection_id"])
        self.assertIsNotNone(sc)
        self.assertEqual(sc.order_id, order["id"])
        self.assertIsNone(sc.marketplace_booking_id)
        self.assertEqual(sc.collection_mode, MODE_AT_RECEPTION)
        self.assertEqual(sc.status, ST_REQUESTED)

    def test_idempotent_ensure_desk_sample_collection(self):
        result = self._create_reception_order()
        from app.models.biz_order import BizOrder

        order = BizOrder.query.get(result["order"]["id"])
        first = ensure_desk_sample_collection(order)
        second = ensure_desk_sample_collection(order)
        db.session.commit()
        self.assertEqual(first.id, second.id)
        self.assertEqual(SampleCollection.query.filter_by(order_id=order.id).count(), 1)

    def test_at_reception_in_desk_not_field_queue(self):
        result = self._create_reception_order()
        sc_id = result["sample_collection_id"]
        desk = list_reception_desk_queue()
        self.assertIn(sc_id, {item["id"] for item in desk["items"]})
        field = list_production_queue()
        self.assertNotIn(sc_id, {item["id"] for item in field["items"]})

    def test_status_normalization(self):
        self.assertEqual(normalize_status("assigned"), "ASSIGNED")
        self.assertEqual(normalize_status("PENDING"), "REQUESTED")
        self.assertEqual(normalize_status("CHECKED_IN"), "VERIFIED")
        self.assertEqual(normalize_status("RECEIVED"), "ARRIVED_AT_LAB")


if __name__ == "__main__":
    unittest.main()
