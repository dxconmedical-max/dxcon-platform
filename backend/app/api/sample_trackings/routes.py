from flask import Blueprint, request

from app.extensions.db import db
from app.models.sample_tracking import SampleTracking

import uuid


sample_trackings_bp = Blueprint(
    "sample_trackings",
    __name__,
    url_prefix="/api/v1/sample-trackings"
)


def generate_sample_code():

    return "DX-SAMPLE-" + str(uuid.uuid4())[:8].upper()


@sample_trackings_bp.route("", methods=["GET"])
def get_sample_trackings():

    data = SampleTracking.query.all()

    return {
        "count": len(data),
        "data": [
            item.to_dict()
            for item in data
        ]
    }


@sample_trackings_bp.route("", methods=["POST"])
def create_sample_tracking():

    payload = request.get_json()

    item = SampleTracking(
        sample_code=payload.get(
            "sample_code",
            generate_sample_code()
        ),
        home_collection_id=payload.get("home_collection_id"),
        collector_id=payload.get("collector_id"),
        latitude=payload.get("latitude"),
        longitude=payload.get("longitude"),
        status=payload.get("status", "CHECKED_IN")
    )

    db.session.add(item)
    db.session.commit()

    return {
        "message": "Sample tracking created",
        "data": item.to_dict()
    }, 201


@sample_trackings_bp.route(
    "/<sample_id>/status",
    methods=["PATCH"]
)
def update_sample_status(sample_id):

    payload = request.get_json()

    item = SampleTracking.query.get(sample_id)

    if not item:
        return {
            "error": "Sample tracking not found"
        }, 404

    item.status = payload.get(
        "status",
        item.status
    )

    db.session.commit()

    return {
        "message": "Sample status updated",
        "data": item.to_dict()
    }
