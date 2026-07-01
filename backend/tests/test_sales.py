import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import (
    CRM_APPROVAL_PENDING,
    CRM_PRICE_SOURCE_CATALOG,
    CRM_PRICE_SOURCE_CONTRACT,
    CRM_PRICE_SOURCE_CUSTOMER,
)
from app.extensions.db import db
from app.models.crm_quotation import Quotation, QuotationItem
from app.models.test_catalog import TestCatalog
from app.services.crm_service import CrmService
from app.services.quotation_service import QuotationService


class SalesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        self.test = TestCatalog(
            code="GLU",
            name="Glucose",
            category="LAB",
            sample_type="BLOOD",
            price=150000,
        )
        db.session.add(self.test)
        db.session.commit()

        self.customer = CrmService.create_customer({"name": "Sales Customer"})
        self.contract_customer = CrmService.create_customer({"name": "Contract Customer"})

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_generate_quotation_from_catalog(self):
        quotation = QuotationService.generate_quotation(
            {
                "customer_id": self.customer.id,
                "price_source": CRM_PRICE_SOURCE_CATALOG,
                "test_catalog_ids": [self.test.id],
            }
        )
        self.assertGreater(quotation.total_amount, 0)
        items = QuotationItem.query.filter_by(quotation_id=quotation.id).all()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].item_code, "GLU")

    def test_generate_quotation_from_customer_pricing(self):
        QuotationService.create_price_book(
            {
                "name": "Customer GLU",
                "source_type": CRM_PRICE_SOURCE_CUSTOMER,
                "customer_id": self.customer.id,
                "test_catalog_id": self.test.id,
                "unit_price": 120000,
                "discount_percent": 10,
            }
        )
        quotation = QuotationService.generate_quotation(
            {
                "customer_id": self.customer.id,
                "price_source": CRM_PRICE_SOURCE_CUSTOMER,
                "test_catalog_ids": [self.test.id],
            }
        )
        item = QuotationItem.query.filter_by(quotation_id=quotation.id).first()
        self.assertEqual(item.unit_price, 120000)

    def test_quotation_approval_flow(self):
        quotation = QuotationService.create_quotation(
            {"customer_id": self.customer.id, "total_amount": 1000000}
        )
        submitted = QuotationService.submit_for_approval(quotation.id)
        self.assertEqual(submitted.approval_status, CRM_APPROVAL_PENDING)

        approved = QuotationService.approve_quotation(quotation.id)
        self.assertEqual(approved.approval_status, "APPROVED")

    def test_quotations_api(self):
        response = self.client.post(
            "/api/v1/crm/quotations/generate",
            json={
                "customer_id": self.customer.id,
                "price_source": CRM_PRICE_SOURCE_CATALOG,
                "test_catalog_ids": [self.test.id],
            },
        )
        self.assertEqual(response.status_code, 201)

        response = self.client.get("/api/v1/crm/quotations")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertGreaterEqual(payload["pagination"]["total"], 1)


if __name__ == "__main__":
    unittest.main()
