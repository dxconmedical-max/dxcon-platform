from flask import Blueprint, redirect
from datetime import datetime

from app.extensions.db import db
from app.models.incident import Incident
from app.utils.auth import role_required


incidents_web_bp = Blueprint(
    "incidents_web",
    __name__
)


@incidents_web_bp.route("/incidents")
@role_required("SUPER_ADMIN")
def incidents_page():

    incidents = Incident.query.order_by(
        Incident.created_at.desc()
    ).all()

    rows = ""

    for item in incidents:

        color = "#0d6efd"

        if item.severity == "CRITICAL":
            color = "#dc3545"

        elif item.severity == "HIGH":
            color = "#f97316"

        elif item.severity == "LOW":
            color = "#198754"

        action = ""

        if item.status != "RESOLVED":
            action = f"""
            <a href="/incidents/resolve/{item.id}">
                Resolve
            </a>
            """

        rows += f"""
        <tr>
            <td>{item.incident_code}</td>
            <td>{item.incident_type}</td>
            <td style="color:{color};font-weight:bold;">{item.severity}</td>
            <td>{item.title or ""}</td>
            <td>{item.status}</td>
            <td>{item.created_at}</td>
            <td>{action}</td>
        </tr>
        """

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">

        <h1>DxCon Incident Management</h1>

        <table border="1" cellpadding="10" style="width:100%;background:white;border-collapse:collapse;">
            <tr style="background:#e2e8f0;">
                <th>Code</th>
                <th>Type</th>
                <th>Severity</th>
                <th>Title</th>
                <th>Status</th>
                <th>Created</th>
                <th>Action</th>
            </tr>
            {rows}
        </table>

        <br>
        <a href="/dashboard">Dashboard</a>
        |
        <a href="/executive">CEO Dashboard</a>
        |
        <a href="/alerts">Alerts</a>

    </body>
    </html>
    """


@incidents_web_bp.route("/incidents/resolve/<incident_id>")
@role_required("SUPER_ADMIN")
def resolve_incident_web(incident_id):

    incident = Incident.query.get(incident_id)

    if incident:
        incident.status = "RESOLVED"
        incident.resolved_at = datetime.utcnow()
        db.session.commit()

    return redirect("/incidents")
