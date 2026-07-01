import os
import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import CRM_CONTRACT_TYPE_CORPORATE, CRM_CONTRACT_TYPE_HOSPITAL
from app.extensions.db import db
from app.models.crm_sales_contract import SalesContract
from app.services.crm_service import CrmService
from app.services.sales_contract_service import SalesContractError, SalesContractService


class ContractsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.customer = CrmService.create_customer({"name": "Contract Customer"})
        self.org = CrmService.create_organization({"name": "Contract Org"})

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_create_contract_with_renewal_reminder(self):
        effective = datetime.utcnow().date()
        expiry = effective + timedelta(days=365)
        contract = SalesContractService.create_contract(
            {
                "title": "Corporate Annual",
                "contract_type": CRM_CONTRACT_TYPE_CORPORATE,
                "customer_id": self.customer.id,
                "organization_id": self.org.id,
                "effective_date": effective.isoformat(),
                "expiry_date": expiry.isoformat(),
                "corporate_discount_percent": 12,
                "prices": [
                    {
                        "item_code": "GLU",
                        "item_name": "Glucose",
                        "standard_price": 150000,
                        "contract_price": 132000,
                        "discount_percent": 12,
                    }
                ],
            }
        )
        self.assertIsNotNone(contract.renewal_reminder_at)
        payload = SalesContractService.get_contract(contract.id)
        self.assertEqual(len(payload["prices"]), 1)

    def test_expiring_contracts(self):
        effective = datetime.utcnow().date() - timedelta(days=350)
        expiry = datetime.utcnow().date() + timedelta(days=10)
        SalesContractService.create_contract(
            {
                "title": "Expiring Hospital Contract",
                "contract_type": CRM_CONTRACT_TYPE_HOSPITAL,
                "customer_id": self.customer.id,
                "effective_date": effective.isoformat(),
                "expiry_date": expiry.isoformat(),
            }
        )
        expiring = SalesContractService.expiring_contracts(within_days=30)
        self.assertGreaterEqual(len(expiring), 1)

    def test_invalid_contract_type(self):
        with self.assertRaises(SalesContractError):
            SalesContractService.create_contract(
                {"title": "Bad", "contract_type": "INVALID", "customer_id": self.customer.id}
            )

    def test_contracts_api(self):
        response = self.client.post(
            "/api/v1/crm/contracts",
            json={
                "title": "API Contract",
                "contract_type": CRM_CONTRACT_TYPE_CORPORATE,
                "customer_id": self.customer.id,
            },
        )
        self.assertEqual(response.status_code, 201)

        response = self.client.get("/api/v1/crm/contracts/expiring")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/api/v1/crm/contracts")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.get_json()["pagination"]["total"], 1)


if __name__ == "__main__":
    unittest.main()
