import os
import sys
import unittest
import uuid
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from flask_jwt_extended import create_access_token

from app import create_app
from app.core.passwords import hash_password
from app.extensions.db import db
from app.models.biz_order import BizOrder, BizPayment
from app.models.user import User


def _headers(role):
    user = User(
        email=f"ob-{role.lower()}-{uuid.uuid4().hex[:8]}@test.local",
        role=role,
        password_hash=hash_password("Password123!"),
        is_active=True,
    )
    db.session.add(user)
    db.session.commit()
    token = create_access_token(
        identity=user.id, additional_claims={"role": user.role, "email": user.email}
    )
    return {"Authorization": f"Bearer {token}"}


def _order(code, name, status, total, created):
    db.session.add(
        BizOrder(
            order_code=code,
            patient_code=f"P-{code}",
            patient_name=name,
            status=status,
            subtotal=total,
            total_amount=total,
            created_at=created,
        )
    )


class OpsBoardTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        now = datetime.utcnow()
        _order("ORD-1", "Nguyen Van A", "paid", 100000, now)
        _order("ORD-2", "Le Thi B", "draft", 50000, now)
        _order("ORD-3", "Tran C", "paid", 70000, now - timedelta(days=10))
        db.session.commit()
        self.admin = _headers("SUPER_ADMIN")

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _get(self, qs=""):
        res = self.client.get(f"/api/v1/ops-board/orders{qs}", headers=self.admin)
        self.assertEqual(res.status_code, 200)
        return res.get_json()

    def test_lists_everything_with_summary(self):
        data = self._get()
        self.assertEqual(data["total_rows"], 3)
        self.assertEqual(data["summary"]["orders"], 3)
        self.assertEqual(data["summary"]["by_status"], {"paid": 2, "draft": 1})
        self.assertEqual(data["summary"]["orders_value"], 220000)

    def test_filters_by_status_and_search(self):
        self.assertEqual(self._get("?status=paid")["total_rows"], 2)
        self.assertEqual(self._get("?q=le%20thi")["total_rows"], 1)
        self.assertEqual(self._get("?q=ORD-3")["orders"][0]["order_code"], "ORD-3")

    def test_date_range(self):
        today = (datetime.utcnow() + timedelta(hours=7)).date().isoformat()
        data = self._get(f"?date_from={today}&date_to={today}")
        self.assertEqual(data["total_rows"], 2)

    def test_collected_sums_payments(self):
        order = BizOrder.query.filter_by(order_code="ORD-1").one()
        db.session.add(
            BizPayment(
                invoice_id="inv-1",
                order_id=order.id,
                payment_method="cash",
                receipt_number="RC-1",
                amount=100000,
                paid_at=datetime.utcnow(),
            )
        )
        db.session.commit()
        self.assertEqual(self._get()["summary"]["collected"], 100000)

    def test_doctor_denied_and_admin_without_internal_org_denied(self):
        res = self.client.get("/api/v1/ops-board/orders", headers=_headers("DOCTOR"))
        self.assertEqual(res.status_code, 403)
        res = self.client.get("/api/v1/ops-board/orders", headers=_headers("ADMIN"))
        self.assertEqual(res.status_code, 403)

    def test_daily_report_excludes_cancelled_and_buckets_by_day(self):
        _order("ORD-4", "Huy", "cancelled", 999000, datetime.utcnow())
        db.session.commit()
        today = (datetime.utcnow() + timedelta(hours=7)).date().isoformat()
        res = self.client.get(f"/api/v1/ops-board/report?date_from={today}&date_to={today}", headers=self.admin)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(len(data["days"]), 1)
        self.assertEqual(data["totals"]["orders"], 2)
        self.assertEqual(data["totals"]["orders_value"], 150000)

    def test_collections_board_lists_field_requests_with_unassigned_count(self):
        from app.models.sample_collection import SampleCollection

        order = BizOrder.query.filter_by(order_code="ORD-1").one()
        db.session.add(
            SampleCollection(
                order_id=order.id,
                collection_mode="HOME_COLLECTION",
                status="PENDING_ASSIGNMENT",
                pickup_address="1 Le Loi",
            )
        )
        db.session.add(
            SampleCollection(order_id=order.id, collection_mode="AT_RECEPTION", status="PENDING")
        )
        db.session.commit()
        res = self.client.get("/api/v1/ops-board/collections", headers=self.admin)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["summary"]["total"], 1)
        self.assertEqual(data["summary"]["unassigned"], 1)
        self.assertEqual(data["items"][0]["order_code"], "ORD-1")
        self.assertFalse(data["items"][0]["collector_online"])

    def test_new_endpoints_deny_doctor(self):
        for path in ("/collections", "/report"):
            res = self.client.get(f"/api/v1/ops-board{path}", headers=_headers("DOCTOR"))
            self.assertEqual(res.status_code, 403)


if __name__ == "__main__":
    unittest.main()
