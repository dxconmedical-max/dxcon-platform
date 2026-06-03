from flask import Blueprint, request
from sqlalchemy.exc import IntegrityError

from app.extensions.db import db
from app.models.test_catalog import TestCatalog

test_catalogs_bp = Blueprint(
    "test_catalogs",
    __name__,
    url_prefix="/api/v1/test-catalogs"
)


@test_catalogs_bp.route("", methods=["GET"])
def get_tests():
    tests = TestCatalog.query.order_by(TestCatalog.code).all()

    return {
        "count": len(tests),
        "data": [test.to_dict() for test in tests]
    }, 200

@test_catalogs_bp.route("", methods=["POST"])
def create_test():
    data = request.get_json()

    code = data.get("code")
    name = data.get("name")

    if not code:
        return {"error": "code is required"}, 400

    if not name:
        return {"error": "name is required"}, 400

    test = TestCatalog(
        code=code,
        name=name,
        category=data.get("category"),
        sample_type=data.get("sample_type"),
        price=data.get("price", 0)
    )

    try:
        db.session.add(test)
        db.session.commit()

        return {
            "message": "Test created",
            "test": test.to_dict()
        }, 201

    except IntegrityError:
        db.session.rollback()

        return {
            "error": "Test code already exists"
        }, 409
