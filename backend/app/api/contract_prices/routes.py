from flask import Blueprint, request

from app.extensions.db import db
from app.models.contract_price import ContractPrice


contract_prices_bp = Blueprint(
    "contract_prices",
    __name__,
    url_prefix="/api/v1/contract-prices"
)


@contract_prices_bp.route("", methods=["GET"])
def get_contract_prices():

    prices = ContractPrice.query.all()

    return {
        "count": len(prices),
        "contract_prices": [
            price.to_dict()
            for price in prices
        ]
    }


@contract_prices_bp.route("", methods=["POST"])
def create_contract_price():

    data = request.get_json()

    standard_price = float(data.get("standard_price", 0))
    contract_price = float(data.get("contract_price", 0))

    discount_percent = 0

    if standard_price > 0:
        discount_percent = round(
            ((standard_price - contract_price) / standard_price) * 100,
            2
        )

    price = ContractPrice(
        contract_id=data.get("contract_id"),
        test_catalog_id=data.get("test_catalog_id"),
        standard_price=standard_price,
        contract_price=contract_price,
        discount_percent=discount_percent
    )

    db.session.add(price)
    db.session.commit()

    return {
        "message": "Contract price created successfully",
        "contract_price": price.to_dict()
    }, 201
