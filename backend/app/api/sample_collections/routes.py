from flask import Blueprint, request

from app.extensions.db import db
from app.models.sample_collection import SampleCollection


sample_collections_bp = Blueprint(
    "sample_collections",
    __name__,
    url_prefix="/api/v1/sample-collections"
)


@sample_collections_bp.route("", methods=["GET"])
def get_sample_collections():

    collections = SampleCollection.query.all()

    return {
        "count": len(collections),
        "collections": [
            item.to_dict()
            for item in collections
        ]
    }


@sample_collections_bp.route("", methods=["POST"])
def create_sample_collection():

    data = request.get_json()

    collection = SampleCollection(
        order_id=data.get("order_id"),
        collector_name=data.get("collector_name"),
        status=data.get("status", "PENDING")
    )

    db.session.add(collection)
    db.session.commit()

    return {
        "message": "Sample collection created",
        "collection": collection.to_dict()
    }, 201
