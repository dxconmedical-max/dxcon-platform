from flask import Blueprint, request
from sqlalchemy.exc import IntegrityError

from app.extensions.db import db
from app.models.contract import Contract


contracts_bp = Blueprint(
    "contracts",
    __name__,
    url_prefix="/api/v1/contracts"
)


@contracts_bp.route("", methods=["GET"])
def get_contracts():

    contracts = Contract.query.all()

    return {
        "count": len(contracts),
        "contracts": [
            contract.to_dict()
            for contract in contracts
        ]
    }


@contracts_bp.route("", methods=["POST"])
def create_contract():

    data = request.get_json()

    contract = Contract(
        contract_code=data.get("contract_code"),
        company_id=data.get("company_id"),
        title=data.get("title"),
        contract_type=data.get("contract_type", "SERVICE"),
        start_date=data.get("start_date"),
        end_date=data.get("end_date"),
        status=data.get("status", "DRAFT"),
        total_value=data.get("total_value", 0)
    )

    try:
        db.session.add(contract)
        db.session.commit()

        return {
            "message": "Contract created successfully",
            "contract": contract.to_dict()
        }, 201

    except IntegrityError:
        db.session.rollback()

        return {
            "error": "Contract code already exists"
        }, 409


@contracts_bp.route("/<contract_id>", methods=["GET"])
def get_contract(contract_id):

    contract = Contract.query.get(contract_id)

    if not contract:
        return {
            "error": "Contract not found"
        }, 404

    return contract.to_dict()


@contracts_bp.route("/<contract_id>", methods=["PUT"])
def update_contract(contract_id):

    contract = Contract.query.get(contract_id)

    if not contract:
        return {
            "error": "Contract not found"
        }, 404

    data = request.get_json()

    contract.title = data.get("title", contract.title)
    contract.contract_type = data.get("contract_type", contract.contract_type)
    contract.start_date = data.get("start_date", contract.start_date)
    contract.end_date = data.get("end_date", contract.end_date)
    contract.status = data.get("status", contract.status)
    contract.total_value = data.get("total_value", contract.total_value)

    db.session.commit()

    return {
        "message": "Contract updated successfully",
        "contract": contract.to_dict()
    }


@contracts_bp.route("/<contract_id>", methods=["DELETE"])
def delete_contract(contract_id):

    contract = Contract.query.get(contract_id)

    if not contract:
        return {
            "error": "Contract not found"
        }, 404

    db.session.delete(contract)
    db.session.commit()

    return {
        "message": "Contract deleted successfully"
    }
