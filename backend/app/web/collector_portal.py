from flask import Blueprint, redirect

from app.extensions.db import db
from app.models.home_collection import HomeCollection
from app.models.patient import Patient
from app.utils.auth import role_required


collector_portal_web_bp = Blueprint(
    "collector_portal_web",
    __name__
)


@collector_portal_web_bp.route("/collector")
@role_required("SUPER_ADMIN", "COLLECTOR")
def collector_dashboard():

    collections = HomeCollection.query.all()

    rows = ""

    for item in collections:

        patient = Patient.query.get(item.patient_id)
        patient_name = patient.full_name if patient else ""

        rows += f"""
        <tr>
            <td>{patient_name}</td>
            <td>{item.address or ""}</td>
            <td>{item.scheduled_time or ""}</td>
            <td>{item.status}</td>
            <td>
                <a href="/collector/status/{item.id}/ASSIGNED">Accept</a>
                |
                <a href="/collector/status/{item.id}/COLLECTED">Collected</a>
                |
                <a href="/collector/status/{item.id}/DELIVERED">Delivered</a>
            </td>
        </tr>
        """

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">

        <h1>Collector Portal</h1>

        <p>Home sample collection task list</p>

        <table border="1" cellpadding="10" style="background:white;width:100%;">
            <tr>
                <th>Patient</th>
                <th>Address</th>
                <th>Schedule</th>
                <th>Status</th>
                <th>Action</th>
            </tr>

            {rows}

        </table>

        <br>

        <a href="/dashboard">Back to Dashboard</a>

    </body>
    </html>
    """


@collector_portal_web_bp.route("/collector/status/<collection_id>/<status>")
@role_required("SUPER_ADMIN", "COLLECTOR")
def update_collector_status(collection_id, status):

    item = HomeCollection.query.get(collection_id)

    if not item:
        return "Collection not found"

    item.status = status
    db.session.commit()

    return redirect("/collector")
