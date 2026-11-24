import os
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_tmp = tempfile.NamedTemporaryFile(prefix="dxcon_billing_", suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"


class ClinicBillingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import create_app
        from app.extensions.db import db

        cls.app = create_app()
        cls.app.config["TESTING"] = True
        with cls.app.app_context():
            db.create_all()

    def test_every_endpoint_requires_login(self):
        c = self.app.test_client()
        b = "/api/v1/reception/workspace/clinic-billing"
        for method, url in [
            ("get", f"{b}/receivables"),
            ("get", f"{b}/x"),
            ("post", f"{b}/x/settings"),
            ("get", f"{b}/x/prices"),
            ("post", f"{b}/x/prices/y"),
            ("post", f"{b}/x/prices/bulk"),
            ("post", f"{b}/x/contracts"),
            ("get", f"{b}/x/contracts/y/file"),
            ("post", f"{b}/x/statements/preview"),
            ("post", f"{b}/x/statements"),
            ("get", f"{b}/x/statements/y"),
            ("post", f"{b}/x/statements/y/void"),
            ("post", f"{b}/x/payments"),
        ]:
            r = getattr(c, method)(url)
            self.assertIn(r.status_code, (401, 403), f"{method} {url} -> {r.status_code}")

    def test_clinic_price_rules(self):
        from app.clinic_billing.logic import clinic_unit_price

        self.assertEqual(clinic_unit_price(100000, 80000, 10), 80000)  # fixed price wins
        self.assertEqual(clinic_unit_price(100000, None, 10), 90000)  # default discount
        self.assertEqual(clinic_unit_price(100000, None, 0), 100000)
        self.assertEqual(clinic_unit_price(100000, None, 150), 0)  # discount capped at 100%

    def test_fifo_allocation_and_aging(self):
        from app.clinic_billing.logic import aging_summary, allocate_payments, due_date_for

        stmts = [
            {"id": "b", "period_start": "2026-10-01", "due_date": "2026-11-30", "total_amount": 500.0},
            {"id": "a", "period_start": "2026-09-01", "due_date": "2026-10-30", "total_amount": 1000.0},
        ]
        out = allocate_payments(stmts, 1200.0)
        by = {s["id"]: s for s in out}
        self.assertEqual(by["a"]["outstanding"], 0)
        self.assertEqual(by["b"]["outstanding"], 300.0)
        aging = aging_summary(out, date(2026, 12, 15))
        self.assertEqual(aging["d1_30"], 300.0)
        self.assertEqual(due_date_for(date(2026, 10, 31), 30), date(2026, 11, 30))

    def test_pricing_never_blocks_without_tables(self):
        from app.clinic_billing.pricing import apply_clinic_prices

        with self.app.app_context():
            self.assertFalse(apply_clinic_prices(None, "x"))
            self.assertFalse(apply_clinic_prices("NOPE", "x"))


if __name__ == "__main__":
    unittest.main()


def test_bulk_price_parsing():
    from app.clinic_billing.logic import parse_price, parse_price_lines

    assert parse_price("1.200.000") == 1200000
    assert parse_price("1,200,000") == 1200000
    assert parse_price("350000đ") == 350000
    assert parse_price("abc") is None
    rows = parse_price_lines("CBC\t120000\nHBA1C;250.000\nTSH -\nBAD\nX abc")
    assert [r["price"] for r in rows[:2]] == [120000.0, 250000.0]
    assert rows[2]["remove"] is True
    assert rows[3]["error"] and rows[4]["error"]
