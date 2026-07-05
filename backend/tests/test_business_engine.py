import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.business_engine import service as biz
from app.business_engine.service import BusinessEngineError
from app.business_engine.statuses import ORDER_RELEASED
from app.extensions.db import db
from app.models.biz_order import BizWorkflowAudit


class BusinessEngineTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        biz.ensure_test_catalog_seed()
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_full_workflow(self):
        patient = biz.create_patient(full_name="Test Patient", phone="0901111222")
        order = biz.create_order(patient_code=patient.patient_code)
        biz.submit_order_for_payment(order.order_code)
        biz.mark_order_paid(order.order_code, payment_method="card")
        biz.create_collection_job(order.order_code, collector_name="C1", pickup_address="Addr")
        biz.collect_sample(order.order_code)
        biz.handover_sample(order.order_code)
        biz.receive_sample_at_lab(order.order_code, received_by="Lab")
        biz.enter_results(
            order.order_code,
            [{"test_name": order.items[0].test_name, "test_code": order.items[0].test_code, "result_value": "5.0", "reference_range": "4-6"}],
        )
        biz.approve_result(order.order_code, doctor_note="OK")
        biz.release_report(order.order_code)
        db.session.commit()
        detail = biz.order_to_detail(order.order_code)
        self.assertEqual(detail["status"], ORDER_RELEASED)
        self.assertGreater(BizWorkflowAudit.query.count(), 0)

    def test_duplicate_phone_blocked(self):
        biz.create_patient(full_name="A", phone="0909999888")
        db.session.commit()
        with self.assertRaises(BusinessEngineError):
            biz.create_patient(full_name="B", phone="0909999888")

    def test_patient_search(self):
        biz.create_patient(full_name="Unique Name XYZ", phone="0903333444")
        db.session.commit()
        rows = biz.search_patients("Unique Name")
        self.assertTrue(any("Unique Name" in p.full_name for p in rows))


if __name__ == "__main__":
    unittest.main()
