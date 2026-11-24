import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_tmp = tempfile.NamedTemporaryFile(prefix="dxcon_labpay_", suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"


class LabPayablesTests(unittest.TestCase):
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
        b = "/api/v1/reception/workspace/lab-payables"
        for method, url in [
            ("get", f"{b}/labs"),
            ("post", f"{b}/labs"),
            ("get", f"{b}/organizations"),
            ("get", f"{b}/routing"),
            ("post", f"{b}/routing"),
            ("get", f"{b}/unassigned"),
            ("post", f"{b}/orders/assign"),
            ("get", f"{b}/x"),
            ("get", f"{b}/x/costs"),
            ("post", f"{b}/x/costs/bulk"),
            ("get", f"{b}/x/costs/template"),
            ("post", f"{b}/x/costs/upload"),
            ("post", f"{b}/x/recalc"),
            ("post", f"{b}/x/statements/preview"),
            ("post", f"{b}/x/statements"),
            ("get", f"{b}/x/statements/y"),
            ("post", f"{b}/x/statements/y/void"),
            ("post", f"{b}/x/payments"),
        ]:
            res = getattr(c, method)(url)
            self.assertIn(res.status_code, (401, 403), f"{method} {url} -> {res.status_code}")

    def test_order_cost_counts_missing_lines(self):
        from app.extensions.db import db
        from app.lab_payables.cost import order_cost
        from app.models.lab_payables import LabCostPrice

        with self.app.app_context():
            db.session.add(LabCostPrice(organization_id="lab1", test_catalog_id="t1", cost=100000))
            db.session.commit()
            order = SimpleNamespace(
                items=[
                    SimpleNamespace(test_catalog_id="t1", quantity=2),
                    SimpleNamespace(test_catalog_id="t2", quantity=1),
                ]
            )
            self.assertEqual(order_cost(order, "lab1"), (200000.0, 1))

    def test_form_upload_reads_filled_column_and_skips_blank(self):
        from openpyxl import Workbook

        from app.clinic_billing.bulk import build_template_xlsx, sheet_to_text

        blob = build_template_xlsx("Giá nhập (điền)", [("CBC", "Công thức máu", 150000, None), ("TSH", "TSH", 200000, None), ("FT4", "FT4", 220000, None)])
        from openpyxl import load_workbook

        wb = load_workbook(io.BytesIO(blob))
        ws = wb.active
        ws["D2"] = 120000
        ws["D3"] = "-"
        out = io.BytesIO()
        wb.save(out)
        text = sheet_to_text("form.xlsx", out.getvalue())
        self.assertEqual(text.splitlines(), ["CBC\t120000", "TSH\t-"])

    def test_csv_form_with_semicolons(self):
        from app.clinic_billing.bulk import sheet_to_text

        data = "Mã;Tên;Giá public;Giá nhập\nCBC;Công thức máu;150000;120.000\nTSH;TSH;200000;\n".encode("utf-8")
        self.assertEqual(sheet_to_text("f.csv", data), "CBC\t120.000")


if __name__ == "__main__":
    unittest.main()
