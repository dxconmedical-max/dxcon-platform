"""Schema reconciliation coverage + full laboratory lifecycle regression."""

from __future__ import annotations

import os
import re
import tempfile
import unittest
import uuid
from pathlib import Path

_TEST_DB = tempfile.NamedTemporaryFile(prefix="dxcon_schema_recon_", suffix=".db", delete=False)
_TEST_DB.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB.name}"

ROOT = Path(__file__).resolve().parents[1]
RECON = ROOT / "migrations" / "021_schema_reconciliation.sql"

from app import create_app
from app.business_engine import service as biz
from app.business_engine.statuses import ORDER_LAB_RECEIVED, ORDER_RELEASED
from app.extensions.db import db
from app.lab_workspace.service import (
    assign_processing,
    create_accession,
    enter_result_manual,
    mark_qc_passed,
    medical_validate,
    release_result,
    start_processing,
    validate_result,
)
from app.models.biz_order import BizLabQueueItem, BizOrder
from app.models.sample_collection import SampleCollection
from app.models.test_catalog import TestCatalog
from app.models.user import User
from app.reception_workspace.service import create_reception_order
from app.sample_collection_workspace.collection_routing import (
    assign_collector,
    list_field_collector_queue,
)
from app.services.sample_collection_workflow import SampleCollectionWorkflowService


class SchemaReconciliationTests(unittest.TestCase):
    def test_reconciliation_migration_covers_every_orm_column(self):
        self.assertTrue(RECON.exists(), "021_schema_reconciliation.sql missing")
        text = RECON.read_text(encoding="utf-8")
        # Ignore documentation comments when scanning for forbidden DDL
        code_only = "\n".join(
            ln for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("--")
        ).upper()
        self.assertNotIn("DROP COLUMN", code_only)
        self.assertNotIn("ALTER COLUMN", code_only)
        self.assertNotIn("ALTER TYPE", code_only)
        self.assertNotIn("DELETE FROM", code_only)
        self.assertIn("ADD COLUMN IF NOT EXISTS", text)
        self.assertIn("CREATE INDEX IF NOT EXISTS", text)

        app = create_app()
        with app.app_context():
            for table_name, table in db.Model.metadata.tables.items():
                self.assertIn(
                    f"-- ===== {table_name} =====",
                    text,
                    msg=f"table {table_name} missing from reconciliation",
                )
                for col in table.columns:
                    pattern = (
                        rf"ALTER TABLE\s+{re.escape(table_name)}\s+"
                        rf"ADD COLUMN IF NOT EXISTS\s+{re.escape(col.name)}\b"
                    )
                    self.assertRegex(
                        text,
                        pattern,
                        msg=f"{table_name}.{col.name} missing ADD COLUMN",
                    )

    def test_sample_collections_critical_columns_present(self):
        text = RECON.read_text(encoding="utf-8")
        for col in (
            "collection_mode",
            "marketplace_booking_id",
            "collector_id",
            "arrived_at_lab",
            "pickup_address",
            "priority",
        ):
            self.assertIn(
                f"ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS {col}",
                text,
            )


class SchemaLifecycleRegressionTests(unittest.TestCase):
    """Reception → collector → lab receive → accession → validate → release."""

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
        self.collector = User(
            email=f"col-{uuid.uuid4().hex[:6]}@test.local",
            role="COLLECTOR",
            password_hash="x",
            is_active=True,
        )
        db.session.add_all([self.admin, self.collector])
        db.session.commit()
        self.cbc = TestCatalog.query.filter_by(code="CBC").first() or TestCatalog.query.first()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_full_lifecycle_with_orm_sample_collection_columns(self):
        patient = biz.create_patient(
            full_name="Schema Recon",
            phone=f"09{uuid.uuid4().hex[:8]}",
            patient_code=f"P-SR-{uuid.uuid4().hex[:4].upper()}",
            actor=self.admin.email,
        )
        created = create_reception_order(
            patient_code=patient.patient_code,
            test_catalog_ids=[self.cbc.id],
            collection_mode="HOME",
            pickup={
                "pickup_address": "12 Schema St",
                "pickup_province": "HCM",
                "pickup_district": "Q1",
                "contact_person": patient.full_name,
                "contact_phone": "0912345678",
                "requested_date": "2026-09-01",
                "requested_time_window": "09:00-11:00",
                "specimen_type": "BLOOD",
                "priority": "ROUTINE",
            },
            actor=self.admin.email,
            organization_id="org-schema",
        )
        db.session.commit()
        sc_id = created["sample_collection_id"]
        order_code = created["order"]["order_code"]
        barcode = created["order"].get("barcode_value") or f"BC-{order_code}"

        sc = SampleCollection.query.get(sc_id)
        self.assertIsNotNone(sc)
        self.assertTrue(hasattr(sc, "collection_mode"))
        self.assertTrue(hasattr(sc, "marketplace_booking_id"))
        self.assertEqual(sc.collection_mode, "HOME_COLLECTION")
        # Touch every mapped column via to_dict (UndefinedColumn would fail on PG)
        payload = sc.to_dict()
        self.assertIn("collection_mode", payload)
        self.assertIn("marketplace_booking_id", payload)

        assign_collector(
            sc_id,
            collector_id=self.collector.id,
            collector_name="Schema Collector",
            actor=self.admin.email,
        )
        db.session.commit()
        self.assertIn(sc_id, {i["id"] for i in list_field_collector_queue()["items"]})

        SampleCollectionWorkflowService.verify_identifiers(
            sc_id,
            patient_name=created["order"]["patient_name"],
            booking_code=order_code,
            actor_email=self.collector.email,
        )
        SampleCollectionWorkflowService.record_collection_by_id(
            sc_id, scanned_barcode=barcode, require_barcode=True, actor_email=self.collector.email
        )
        SampleCollectionWorkflowService.dispatch_by_collection_id(
            sc_id, actor_email=self.collector.email
        )
        SampleCollectionWorkflowService.receive_by_collection_id(
            sc_id, actor_email=self.admin.email
        )

        order = BizOrder.query.filter_by(order_code=order_code).first()
        self.assertEqual(order.status, ORDER_LAB_RECEIVED)
        self.assertIsNotNone(BizLabQueueItem.query.filter_by(order_id=order.id).first())

        create_accession(order_code=order_code, accessioned_by="Lab", actor="lab")
        assign_processing(
            order_code=order_code, bench_id="B1", instrument_id="I1", technician="tech", actor="lab"
        )
        start_processing(order_code=order_code, actor="lab")
        enter_result_manual(
            order_code,
            test_code=self.cbc.code,
            result_value="5.1",
            unit="g/dL",
            reference_range="3.5-5.5",
            actor="lab",
        )
        mark_qc_passed(order_code, actor="lab")
        validate_result(order_code, actor="lab")
        medical_validate(order_code, doctor_note="ok", actor=self.admin.email)
        released = release_result(order_code, actor=self.admin.email)
        db.session.commit()

        self.assertEqual(released["status"], ORDER_RELEASED)
        sc = SampleCollection.query.get(sc_id)
        self.assertEqual(sc.status, "RELEASED")
        self.assertEqual(BizOrder.query.filter_by(order_code=order_code).first().status, ORDER_RELEASED)


if __name__ == "__main__":
    unittest.main()
