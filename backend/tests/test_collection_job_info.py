import os
import sys
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.models.biz_order import BizOrder, BizOrderItem, BizPayment
from app.models.patient import Patient
from app.models.sample_collection import SampleCollection
from app.services.sample_collection_workflow import SampleCollectionWorkflowService


class CollectionJobInfoTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_job_info_has_patient_tests_and_amounts(self):
        db.session.add(Patient(patient_code="P1", full_name="Nguyen Van A", gender="M", date_of_birth="1990-01-02", phone="0900000001", address="59 Cao Thang"))
        order = BizOrder(order_code="ORD-1", patient_code="P1", patient_name="Nguyen Van A", status="paid", subtotal=150000, total_amount=150000, note="Nhin an sang")
        order.items.append(BizOrderItem(test_code="GLU", test_name="Glucose", unit_price=50000, quantity=1, line_total=50000))
        order.items.append(BizOrderItem(test_code="HBA1C", test_name="HbA1c", unit_price=100000, quantity=1, line_total=100000))
        db.session.add(order)
        db.session.flush()
        db.session.add(BizPayment(invoice_id="inv", order_id=order.id, payment_method="cash", receipt_number="RC1", amount=50000, paid_at=datetime.utcnow()))
        col = SampleCollection(order_id=order.id, collection_mode="HOME_COLLECTION", status="ASSIGNED", pickup_address="59 Cao Thang")
        db.session.add(col)
        db.session.commit()

        info = SampleCollectionWorkflowService._enrich_payload(col)["job_info"]
        self.assertTrue(info["order_found"])
        self.assertEqual(info["patient_name"], "Nguyen Van A")
        self.assertEqual(info["patient_phone"], "0900000001")
        self.assertEqual(info["patient_gender"], "M")
        self.assertEqual([t["test_code"] for t in info["tests"]], ["GLU", "HBA1C"])
        self.assertEqual(info["total_amount"], 150000)
        self.assertEqual(info["paid_amount"], 50000)
        self.assertEqual(info["due_amount"], 100000)
        self.assertEqual(info["note"], "Nhin an sang")

    def test_missing_order_is_reported_not_crashing(self):
        col = SampleCollection(order_id="gone", collection_mode="HOME_COLLECTION", status="ASSIGNED", contact_phone="0911")
        db.session.add(col)
        db.session.commit()
        info = SampleCollectionWorkflowService._enrich_payload(col)["job_info"]
        self.assertFalse(info["order_found"])
        self.assertEqual(info["patient_phone"], "0911")
        self.assertEqual(info["tests"], [])


if __name__ == "__main__":
    unittest.main()
