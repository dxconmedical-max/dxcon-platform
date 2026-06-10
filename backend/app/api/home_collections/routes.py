from flask import Blueprint, request

from app.extensions.db import db
from app.models.home_collection import HomeCollection


home_collections_bp = Blueprint(
    "home_collections",
    __name__,
    url_prefix="/api/v1/home-collections"
)


@home_collections_bp.route("", methods=["GET"])
def get_home_collections():

    data = HomeCollection.query.all()

    return {
        "count": len(data),
        "data": [
            item.to_dict()
            for item in data
        ]
    }


@home_collections_bp.route("", methods=["POST"])
def create_home_collection():

    payload = request.get_json()

    item = HomeCollection(
        patient_id=payload.get("patient_id"),
        collector_id=payload.get("collector_id"),
        address=payload.get("address"),
        scheduled_time=payload.get("scheduled_time"),
        status="REQUESTED"
    )

    db.session.add(item)
    db.session.commit()

    return {
        "message": "Home collection created",
        "data": item.to_dict()
    }, 201
