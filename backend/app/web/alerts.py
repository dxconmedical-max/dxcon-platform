from flask import Blueprint, redirect
from datetime import datetime

from app.extensions.db import db
from app.models.alert import Alert
from app.utils.auth import role_required


alerts_web_bp = Blueprint(
    "alerts_web",
    __name__
)


@alerts_web_bp.route("/alerts")
@role_required("SUPER_ADMIN")
def alerts_page():

    alerts = Alert.query.order_by(
        Alert.created_at.desc()
    ).all()

    rows = ""

    for alert in alerts:

        color = "#0d6efd"

        if alert.severity == "CRITICAL":
            color = "#dc3545"
        elif alert.severity == "HIGH":
            color = "#f97316"
        elif alert.severity == "LOW":
            color = "#198754"

        actions = ""

        if alert.status == "OPEN":
            actions += f'<a href="/alerts/ack/{alert.id}">ACK</a> '

        if alert.status != "RESOLVED":
            actions += f'<a href="/alerts/resolve/{alert.id}">RESOLVE</a>'

        rows += f"""
        <tr>
            <td>{alert.alert_code}</td>
            <td>{alert.alert_type}</td>
            <td style="color:{color};font-weight:bold;">
                {alert.severity}
            </td>
            <td>{alert.source_type or ""}</td>
            <td>{alert.message or ""}</td>
            <td>{alert.status}</td>
            <td>{actions}</td>
        </tr>
        """

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">

        <h1>DxCon Alert Center</h1>

        <table border="1" cellpadding="10"
               style="width:100%;background:white;border-collapse:collapse;">

            <tr style="background:#e2e8f0;">
                <th>Code</th>
                <th>Type</th>
                <th>Severity</th>
                <th>Source</th>
                <th>Message</th>
                <th>Status</th>
                <th>Action</th>
            </tr>

            {rows}

        </table>

        <br>

        <a href="/executive">CEO Dashboard</a>
        |
        <a href="/incidents">Incidents</a>

    </body>
    </html>
    """


@alerts_web_bp.route("/alerts/ack/<alert_id>")
def ack_alert(alert_id):

    alert = Alert.query.get(alert_id)

    if alert:
        alert.status = "ACKNOWLEDGED"
        alert.acknowledged_at = datetime.utcnow()
        db.session.commit()

    return redirect("/alerts")


@alerts_web_bp.route("/alerts/resolve/<alert_id>")
def resolve_alert(alert_id):

    alert = Alert.query.get(alert_id)

    if alert:
        alert.status = "RESOLVED"
        alert.resolved_at = datetime.utcnow()
        db.session.commit()

    return redirect("/alerts")
