from flask import Blueprint, request
from sqlalchemy.exc import IntegrityError

from app.extensions.db import db
from app.models.company import Company


companies_bp = Blueprint(
    "companies",
    __name__,
    url_prefix="/api/v1/companies"
)


@companies_bp.route("", methods=["GET"])
def get_companies():

    companies = Company.query.all()

    return {
        "count": len(companies),
        "companies": [
            company.to_dict()
            for company in companies
        ]
    }


@companies_bp.route("", methods=["POST"])
def create_company():

    data = request.get_json()

    company = Company(
        company_code=data.get("company_code"),
        company_name=data.get("company_name"),
        tax_code=data.get("tax_code"),
        contact_person=data.get("contact_person"),
        phone=data.get("phone"),
        email=data.get("email"),
        address=data.get("address"),
        status=data.get("status", "ACTIVE")
    )

    try:
        db.session.add(company)
        db.session.commit()

        return {
            "message": "Company created successfully",
            "company": company.to_dict()
        }, 201

    except IntegrityError:
        db.session.rollback()

        return {
            "error": "Company code already exists"
        }, 409


@companies_bp.route("/<company_id>", methods=["GET"])
def get_company(company_id):

    company = Company.query.get(company_id)

    if not company:
        return {
            "error": "Company not found"
        }, 404

    return company.to_dict()


@companies_bp.route("/<company_id>", methods=["PUT"])
def update_company(company_id):

    company = Company.query.get(company_id)

    if not company:
        return {
            "error": "Company not found"
        }, 404

    data = request.get_json()

    company.company_name = data.get("company_name", company.company_name)
    company.tax_code = data.get("tax_code", company.tax_code)
    company.contact_person = data.get("contact_person", company.contact_person)
    company.phone = data.get("phone", company.phone)
    company.email = data.get("email", company.email)
    company.address = data.get("address", company.address)
    company.status = data.get("status", company.status)

    db.session.commit()

    return {
        "message": "Company updated successfully",
        "company": company.to_dict()
    }


@companies_bp.route("/<company_id>", methods=["DELETE"])
def delete_company(company_id):

    company = Company.query.get(company_id)

    if not company:
        return {
            "error": "Company not found"
        }, 404

    db.session.delete(company)
    db.session.commit()

    return {
        "message": "Company deleted successfully"
    }
