from flask import Blueprint, request
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity
)

from app.extensions.db import db
from app.models.user import User
from app.models.patient import Patient
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.test_result import TestResult
from app.models.sample_tracking import SampleTracking
from app.models.clinical_summary import ClinicalSummary
from app.models.home_collection import HomeCollection
from app.core.passwords import verify_password


mobile_bp = Blueprint(
    "mobile",
    __name__,
    url_prefix="/api/v1/mobile"
)


def get_patient_from_token():

    identity = get_jwt_identity()

    if not identity:
        return None

    return Patient.query.get(identity)


@mobile_bp.route("/login", methods=["POST"])
def mobile_login():

    data = request.json or {}

    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(
        email=email,
        role="PATIENT"
    ).first()

    if not user:
        return {"error": "Invalid account"}, 401

    if not verify_password(user.password_hash, password):
        return {"error": "Invalid password"}, 401

    patient = Patient.query.filter_by(
        phone=user.phone
    ).first()

    if not patient:
        return {"error": "Patient profile not found"}, 404

    token = create_access_token(
        identity=patient.id,
        additional_claims={
            "role": "PATIENT",
            "email": user.email
        }
    )

    return {
        "success": True,
        "token": token,
        "patient_id": patient.id,
        "email": user.email
    }


@mobile_bp.route("/me")
@jwt_required()
def me():

    patient = get_patient_from_token()

    if not patient:
        return {"error": "Patient not found"}, 404

    return {
        "patient": patient.to_dict()
    }


@mobile_bp.route("/profile/<patient_id>")
def profile(patient_id):

    patient = Patient.query.get(patient_id)

    if not patient:
        return {"error": "Patient not found"}, 404

    return patient.to_dict()


@mobile_bp.route("/orders/<patient_id>")
def orders(patient_id):

    items = Order.query.filter_by(
        patient_id=patient_id
    ).all()

    return {
        "orders": [
            item.to_dict()
            for item in items
        ]
    }


@mobile_bp.route("/results/<patient_id>")
def results(patient_id):

    data = []

    orders = Order.query.filter_by(
        patient_id=patient_id
    ).all()

    for order in orders:

        order_items = OrderItem.query.filter_by(
            order_id=order.id
        ).all()

        for item in order_items:

            result = TestResult.query.filter_by(
                order_item_id=item.id
            ).first()

            if result:
                data.append(result.to_dict())

    return {"results": data}


@mobile_bp.route("/tracking/<patient_id>")
def tracking(patient_id):

    data = [
        item.to_dict()
        for item in SampleTracking.query.all()
    ]

    return {"tracking": data}


@mobile_bp.route("/clinical-summary/<patient_id>")
def clinical_summary(patient_id):

    data = []

    orders = Order.query.filter_by(
        patient_id=patient_id
    ).all()

    for order in orders:

        summary = ClinicalSummary.query.filter_by(
            order_id=order.id
        ).first()

        if summary:
            data.append(summary.to_dict())

    return {
        "clinical_summaries": data
    }


@mobile_bp.route("/home-collection", methods=["POST"])
def create_home_collection():

    data = request.json or {}

    booking = HomeCollection(
        patient_id=data.get("patient_id"),
        address=data.get("address"),
        scheduled_time=data.get("scheduled_time"),
        status="PENDING"
    )

    db.session.add(booking)
    db.session.commit()

    return {
        "success": True,
        "booking": booking.to_dict()
    }


@mobile_bp.route("/home-collections/<patient_id>", methods=["GET"])
def list_home_collections(patient_id):

    bookings = HomeCollection.query.filter_by(
        patient_id=patient_id
    ).all()

    return {
        "count": len(bookings),
        "home_collections": [
            item.to_dict()
            for item in bookings
        ]
    }


@mobile_bp.route("/secure/profile")
@jwt_required()
def secure_profile():

    patient = get_patient_from_token()

    if not patient:
        return {"error": "Patient not found"}, 404

    return patient.to_dict()


@mobile_bp.route("/secure/orders")
@jwt_required()
def secure_orders():

    patient = get_patient_from_token()

    if not patient:
        return {"error": "Patient not found"}, 404

    items = Order.query.filter_by(
        patient_id=patient.id
    ).all()

    return {
        "orders": [
            item.to_dict()
            for item in items
        ]
    }
