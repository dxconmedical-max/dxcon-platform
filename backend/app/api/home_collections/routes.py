from flask import Blueprint, request
import logging

from app.extensions.db import db
from app.models.home_collection import HomeCollection


logger = logging.getLogger("dxcon.home_collections")

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

    payload = request.get_json() or {}

    item = HomeCollection(
        patient_id=payload.get("patient_id"),
        collector_id=payload.get("collector_id"),
        address=payload.get("address"),
        scheduled_time=payload.get("scheduled_time"),
        status="REQUESTED",
    )

    db.session.add(item)
    db.session.flush()

    sample_collection = None
    try:
        from app.sample_collection_workspace.collection_routing import (
            ensure_sample_collection_from_home_collection,
        )

        sample_collection = ensure_sample_collection_from_home_collection(
            item,
            actor=request.headers.get("X-Actor") or "home_collections_api",
        )
    except Exception:
        logger.exception("SampleCollection bridge failed for HomeCollection %s", item.id)

    db.session.commit()

    data = item.to_dict()
    if sample_collection:
        data["sample_collection_id"] = sample_collection.id
        data["collection_mode"] = sample_collection.collection_mode
        data["sample_status"] = sample_collection.status

    return {
        "message": "Home collection created",
        "data": data,
    }, 201
