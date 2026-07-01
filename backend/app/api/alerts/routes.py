from flask import Blueprint, request
from datetime import datetime
import uuid

from app.extensions.db import db
from app.models.alert import Alert
from app.observability.alert_engine import AlertEngine


alerts_bp = Blueprint(
    "alerts",
    __name__,
    url_prefix="/api/v1/alerts"
)


def alert_code():
    return "ALT-" + str(uuid.uuid4())[:8].upper()


@alerts_bp.route("", methods=["GET"])
def list_alerts():
    alerts = Alert.query.order_by(Alert.created_at.desc()).all()
    platform = AlertEngine.list_alerts(limit=100)
    return {
        "count": len(alerts) + platform["count"],
        "alerts": [a.to_dict() for a in alerts],
        "platform_alerts": platform["alerts"],
        "rules": platform["rules"],
    }


@alerts_bp.route("", methods=["POST"])
def create_alert():

    data = request.get_json() or {}

    alert = Alert(
        alert_code=alert_code(),
        alert_type=data.get("alert_type"),
        severity=data.get("severity", "MEDIUM"),
        source_type=data.get("source_type"),
        source_id=data.get("source_id"),
        message=data.get("message"),
        status="OPEN"
    )

    db.session.add(alert)
    db.session.commit()

    return alert.to_dict(), 201


@alerts_bp.route("/<alert_id>/ack", methods=["POST"])
def ack_alert(alert_id):

    alert = Alert.query.get(alert_id)

    if not alert:
        return {"error": "Alert not found"}, 404

    alert.status = "ACKNOWLEDGED"
    alert.acknowledged_at = datetime.utcnow()

    db.session.commit()

    return alert.to_dict()


@alerts_bp.route("/<alert_id>/resolve", methods=["POST"])
def resolve_alert(alert_id):

    alert = Alert.query.get(alert_id)

    if not alert:
        return {"error": "Alert not found"}, 404

    alert.status = "RESOLVED"
    alert.resolved_at = datetime.utcnow()

    db.session.commit()

    return alert.to_dict()
