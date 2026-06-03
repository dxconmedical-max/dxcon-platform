from app.models.contract_price import ContractPrice
from app.models.test_catalog import TestCatalog


def get_price_for_test(test_catalog_id, contract_id=None):

    test = TestCatalog.query.get(test_catalog_id)

    if not test:
        return {
            "error": "Test catalog not found"
        }

    standard_price = test.price or 0
    final_price = standard_price
    discount_percent = 0

    if contract_id:
        contract_price = ContractPrice.query.filter_by(
            contract_id=contract_id,
            test_catalog_id=test_catalog_id
        ).first()

        if contract_price:
            final_price = contract_price.contract_price
            discount_percent = contract_price.discount_percent

    return {
        "test_catalog_id": test_catalog_id,
        "test_name": test.name,
        "standard_price": standard_price,
        "final_price": final_price,
        "discount_percent": discount_percent
    }

