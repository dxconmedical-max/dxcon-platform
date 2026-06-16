from flask import Blueprint, request

from app.extensions.db import db
from app.models.home_collection import HomeCollection

mobile_home_collection_bp = Blueprint(
    "mobile_home_collection",
    __name__,
    url_prefix="/api/v1/mobile"
)


@mobile_home_collection_bp.route(
    "/home-collection",
    methods=["POST"]
)
def create_home_collection():

    data = request.json

    booking = HomeCollection(
        patient_id=data["patient_id"],
        address=data["address"],
        scheduled_time=data["scheduled_time"],
        status="PENDING"
    )

    db.session.add(booking)
    db.session.commit()

    return {
        "success": True,
        "booking_id": booking.id
    }
