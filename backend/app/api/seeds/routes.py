from flask import Blueprint

from app.extensions.db import db

from app.models.patient import Patient
from app.models.company import Company
from app.models.contract import Contract
from app.models.test_catalog import TestCatalog


seeds_bp = Blueprint(
    "seeds",
    __name__,
    url_prefix="/api/v1/seeds"
)


@seeds_bp.route("/demo", methods=["POST"])
def seed_demo():

    patient = Patient(
        patient_code="PT002",
        full_name="Nguyen Van A",
        gender="MALE",
        phone="0901234567"
    )

    company = Company(
        company_code="DXC002",
        company_name="DxCon Demo Clinic",
        tax_code="0312345678",
        contact_person="Nguyen Van B",
        phone="0909999999",
        email="clinic@dxcon.vn",
        status="ACTIVE"
    )

    test1 = TestCatalog(
        code="HBA1C",
        name="HbA1c",
        category="Biochemistry",
        sample_type="Blood",
        price=250000
    )

    test2 = TestCatalog(
        code="CBC",
        name="Complete Blood Count",
        category="Hematology",
        sample_type="Blood",
        price=150000
    )

    db.session.add(patient)
    db.session.add(company)
    db.session.add(test1)
    db.session.add(test2)

    db.session.commit()

    contract = Contract(
        contract_code="CTR002",
        company_id=company.id,
        title="DxCon Service Contract",
        contract_type="LAB_SERVICE",
        start_date="2026-06-01",
        end_date="2027-06-01",
        status="ACTIVE",
        total_value=50000000
    )

    db.session.add(contract)
    db.session.commit()

    return {
        "message": "Demo data created successfully"
    }
