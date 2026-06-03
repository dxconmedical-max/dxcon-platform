from flask import Blueprint, request

from app.extensions.db import db
from app.models.laboratory import Laboratory


laboratories_bp = Blueprint(
    "laboratories",
    __name__,
    url_prefix="/api/v1/laboratories"
)


@laboratories_bp.route("", methods=["GET"])
def get_laboratories():

    labs = Laboratory.query.all()

    return {
        "count": len(labs),
        "laboratories": [
            lab.to_dict()
            for lab in labs
        ]
    }


@laboratories_bp.route("", methods=["POST"])
def create_laboratory():

    data = request.get_json()

    lab = Laboratory(
        code=data.get("code"),
        name=data.get("name"),
        address=data.get("address"),
        phone=data.get("phone"),
        email=data.get("email")
    )

    db.session.add(lab)
    db.session.commit()

    return {
        "message": "Laboratory created",
        "laboratory": lab.to_dict()
    }, 201
