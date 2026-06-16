from flask import Blueprint, request
from datetime import datetime
import uuid

from app.extensions.db import db
from app.models.incident import Incident


incidents_bp = Blueprint(
    "incidents",
    __name__,
    url_prefix="/api/v1/incidents"
)


def incident_code():
    return "INC-" + str(uuid.uuid4())[:8].upper()


@incidents_bp.route("", methods=["GET"])
def list_incidents():

    incidents = Incident.query.order_by(
        Incident.created_at.desc()
    ).all()

    return {
        "count": len(incidents),
        "incidents": [
            item.to_dict()
            for item in incidents
        ]
    }


@incidents_bp.route("", methods=["POST"])
def create_incident():

    data = request.get_json() or {}

    incident = Incident(
        incident_code=incident_code(),
        incident_type=data.get("incident_type", "GENERAL"),
        severity=data.get("severity", "MEDIUM"),
        title=data.get("title"),
        description=data.get("description"),
        related_object_type=data.get("related_object_type"),
        related_object_id=data.get("related_object_id"),
        status="OPEN"
    )

    db.session.add(incident)
    db.session.commit()

    return incident.to_dict(), 201


@incidents_bp.route("/<incident_id>/resolve", methods=["POST"])
def resolve_incident(incident_id):

    incident = Incident.query.get(incident_id)

    if not incident:
        return {"error": "Incident not found"}, 404

    incident.status = "RESOLVED"
    incident.resolved_at = datetime.utcnow()

    db.session.commit()

    return incident.to_dict()
