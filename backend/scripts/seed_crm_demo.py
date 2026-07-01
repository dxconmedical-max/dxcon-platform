import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app
from app.core.statuses import (
    CRM_ACTIVITY_CALL,
    CRM_ACTIVITY_EMAIL,
    CRM_ACTIVITY_MEETING,
    CRM_ACTIVITY_NOTE,
    CRM_ACTIVITY_TASK,
    CRM_CONTRACT_TYPES,
    CRM_CUSTOMER_ACTIVE,
    CRM_LEAD_NEW,
    CRM_OPPORTUNITY_OPEN,
    CRM_ORG_ACTIVE,
    CRM_PIPELINE_STAGES,
    CRM_PRICE_SOURCE_CUSTOMER,
    CRM_QUOTATION_DRAFT,
)
from app.extensions.db import db
from app.models.crm_activity import Activity
from app.models.crm_lead import CrmLead
from app.models.crm_organization import Customer, Organization
from app.models.crm_pipeline import Opportunity
from app.models.crm_quotation import PriceBook, Quotation
from app.models.crm_sales_contract import SalesContract, SalesContractPrice
from app.models.test_catalog import TestCatalog
from app.services.crm_service import CrmService
from app.services.quotation_service import QuotationService


INDUSTRIES = ["Healthcare", "Insurance", "Corporate", "Pharma", "Retail"]
OWNERS = ["sales.alpha", "sales.beta", "sales.gamma", "sales.delta", "sales.epsilon"]
ACTIVITY_TYPES = [
    CRM_ACTIVITY_CALL,
    CRM_ACTIVITY_MEETING,
    CRM_ACTIVITY_EMAIL,
    CRM_ACTIVITY_TASK,
    CRM_ACTIVITY_NOTE,
]


def _ensure_test_catalog():
    if TestCatalog.query.count() >= 5:
        return TestCatalog.query.limit(10).all()
    tests = []
    catalog = [
        ("GLU", "Glucose", 150000),
        ("CBC", "Complete Blood Count", 250000),
        ("LIP", "Lipid Panel", 320000),
        ("TSH", "Thyroid Stimulating Hormone", 280000),
        ("HBA1C", "HbA1c", 210000),
        ("UA", "Urinalysis", 120000),
        ("CRP", "C-Reactive Protein", 190000),
        ("VITD", "Vitamin D", 350000),
    ]
    for code, name, price in catalog:
        existing = TestCatalog.query.filter_by(code=code).first()
        if existing:
            tests.append(existing)
            continue
        test = TestCatalog(code=code, name=name, category="LAB", sample_type="BLOOD", price=price)
        db.session.add(test)
        tests.append(test)
    db.session.commit()
    return tests


def seed_crm_demo(force=False):
    if not force and CrmLead.query.count() >= 100:
        return {
            "leads": CrmLead.query.count(),
            "customers": Customer.query.count(),
            "organizations": Organization.query.count(),
            "opportunities": Opportunity.query.count(),
            "contracts": SalesContract.query.count(),
            "quotations": Quotation.query.count(),
            "activities": Activity.query.count(),
            "skipped": True,
        }

    tests = _ensure_test_catalog()
    CrmService.ensure_default_pipeline()
    pipeline = CrmService.list_pipelines()["items"][0]

    organizations = []
    for idx in range(20):
        org = Organization(
            org_code=f"ORG-{idx + 1:04d}",
            name=f"Organization {idx + 1}",
            org_type=random.choice(["CORPORATE", "CLINIC", "HOSPITAL", "INSURANCE"]),
            industry=random.choice(INDUSTRIES),
            tax_code=f"TAX{100000 + idx}",
            phone=f"028{random.randint(1000000, 9999999)}",
            email=f"org{idx + 1}@demo.dxcon.local",
            owner=random.choice(OWNERS),
            status=CRM_ORG_ACTIVE,
        )
        db.session.add(org)
        organizations.append(org)
    db.session.flush()

    customers = []
    for idx in range(50):
        org = organizations[idx % len(organizations)]
        customer = Customer(
            customer_code=f"CUST-{idx + 1:04d}",
            name=f"Customer {idx + 1}",
            organization_id=org.id,
            customer_type="B2B",
            email=f"customer{idx + 1}@demo.dxcon.local",
            phone=f"09{random.randint(10000000, 99999999)}",
            owner=random.choice(OWNERS),
            status=CRM_CUSTOMER_ACTIVE,
        )
        db.session.add(customer)
        customers.append(customer)
    db.session.flush()

    for customer in customers[:15]:
        for test in random.sample(tests, k=min(3, len(tests))):
            db.session.add(
                PriceBook(
                    price_book_code=f"PB-{customer.customer_code}-{test.code}",
                    name=f"{test.name} customer price",
                    source_type=CRM_PRICE_SOURCE_CUSTOMER,
                    customer_id=customer.id,
                    test_catalog_id=test.id,
                    unit_price=test.price * random.uniform(0.85, 0.95),
                    discount_percent=random.uniform(5, 15),
                )
            )

    leads = []
    for idx in range(100):
        org = organizations[idx % len(organizations)]
        lead = CrmLead(
            lead_code=f"LEAD-{idx + 1:04d}",
            company_name=f"Prospect Co {idx + 1}",
            contact_person=f"Contact {idx + 1}",
            phone=f"09{random.randint(10000000, 99999999)}",
            email=f"lead{idx + 1}@demo.dxcon.local",
            lead_source=random.choice(["WEB", "REFERRAL", "EVENT", "PARTNER"]),
            organization_id=org.id,
            pipeline_stage=random.choice(CRM_PIPELINE_STAGES),
            status=CRM_LEAD_NEW,
            estimated_revenue=random.randint(5, 500) * 1000000,
            owner=random.choice(OWNERS),
            notes=f"Demo lead {idx + 1}",
        )
        db.session.add(lead)
        leads.append(lead)
    db.session.flush()

    opportunities = []
    for idx in range(30):
        lead = leads[idx]
        customer = customers[idx % len(customers)]
        opp = Opportunity(
            opportunity_code=f"OPP-{idx + 1:04d}",
            title=f"Opportunity {idx + 1}",
            lead_id=lead.id,
            customer_id=customer.id,
            organization_id=customer.organization_id,
            pipeline_id=pipeline["id"],
            pipeline_stage=random.choice(CRM_PIPELINE_STAGES),
            amount=random.randint(10, 800) * 1000000,
            expected_close_date=(datetime.utcnow() + timedelta(days=random.randint(7, 120))).date(),
            status=CRM_OPPORTUNITY_OPEN,
            owner=random.choice(OWNERS),
        )
        db.session.add(opp)
        opportunities.append(opp)
    db.session.flush()

    contracts = []
    for idx in range(15):
        customer = customers[idx]
        effective = datetime.utcnow().date() - timedelta(days=random.randint(30, 180))
        expiry = effective + timedelta(days=random.randint(180, 540))
        contract = SalesContract(
            contract_code=f"SC-{idx + 1:04d}",
            title=f"{random.choice(CRM_CONTRACT_TYPES)} Contract {idx + 1}",
            contract_type=CRM_CONTRACT_TYPES[idx % len(CRM_CONTRACT_TYPES)],
            customer_id=customer.id,
            organization_id=customer.organization_id,
            effective_date=effective,
            expiry_date=expiry,
            renewal_reminder_at=datetime.combine(
                expiry - timedelta(days=30), datetime.min.time()
            ),
            corporate_discount_percent=random.uniform(5, 20),
            status="ACTIVE",
            owner=random.choice(OWNERS),
        )
        db.session.add(contract)
        contracts.append(contract)
    db.session.flush()

    for contract in contracts:
        for test in random.sample(tests, k=min(4, len(tests))):
            discount = contract.corporate_discount_percent
            db.session.add(
                SalesContractPrice(
                    contract_id=contract.id,
                    test_catalog_id=test.id,
                    item_code=test.code,
                    item_name=test.name,
                    standard_price=test.price,
                    contract_price=test.price * (1 - discount / 100),
                    discount_percent=discount,
                )
            )

    for idx in range(50):
        customer = customers[idx % len(customers)]
        contract = contracts[idx % len(contracts)] if idx % 3 == 0 else None
        source = "CONTRACT" if contract else random.choice(["CATALOG", "CUSTOMER"])
        quotation = QuotationService.generate_quotation(
            {
                "customer_id": customer.id,
                "opportunity_id": opportunities[idx % len(opportunities)].id if opportunities else None,
                "price_source": source,
                "contract_id": contract.id if contract else None,
                "test_catalog_ids": [t.id for t in random.sample(tests, k=min(3, len(tests)))],
                "owner": random.choice(OWNERS),
            }
        )
        if idx % 4 == 0:
            quotation.approval_status = CRM_QUOTATION_DRAFT

    activity_count = 0
    for idx in range(120):
        lead = random.choice(leads)
        customer = random.choice(customers)
        opp = random.choice(opportunities)
        activity = Activity(
            activity_type=random.choice(ACTIVITY_TYPES),
            subject=f"Activity {idx + 1}",
            description=f"Demo activity for pipeline follow-up {idx + 1}",
            lead_id=lead.id,
            customer_id=customer.id,
            opportunity_id=opp.id,
            due_date=datetime.utcnow() + timedelta(days=random.randint(1, 14)),
            reminder_at=datetime.utcnow() + timedelta(days=random.randint(0, 7)),
            owner=random.choice(OWNERS),
        )
        db.session.add(activity)
        activity_count += 1

    db.session.commit()
    return {
        "leads": CrmLead.query.count(),
        "customers": Customer.query.count(),
        "organizations": Organization.query.count(),
        "opportunities": Opportunity.query.count(),
        "contracts": SalesContract.query.count(),
        "quotations": Quotation.query.count(),
        "activities": Activity.query.count(),
        "skipped": False,
    }


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
        summary = seed_crm_demo(force="--force" in sys.argv)
        print(summary)
