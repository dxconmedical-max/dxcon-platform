from flask import Blueprint, redirect

from app.extensions.db import db
from app.models.sample_tracking import SampleTracking
from app.models.home_collection import HomeCollection
from app.models.patient import Patient
from app.utils.auth import role_required


lab_worklist_bp = Blueprint(
    "lab_worklist",
    __name__
)


@lab_worklist_bp.route("/lab-worklist")
@role_required("SUPER_ADMIN", "LAB_TECHNICIAN")
def lab_worklist():

    samples = SampleTracking.query.all()

    rows = ""

    for sample in samples:

        patient_name = ""

        if sample.home_collection_id:
            collection = HomeCollection.query.get(
                sample.home_collection_id
            )

            if collection:
                patient = Patient.query.get(
                    collection.patient_id
                )

                patient_name = patient.full_name if patient else ""

        rows += f"""
        <tr>
            <td>{sample.sample_code}</td>
            <td>{patient_name}</td>
            <td>{sample.status}</td>

            <td>
                <a href="/lab-worklist/status/{sample.id}/RECEIVED">
                    Received
                </a>
                |
                <a href="/lab-worklist/status/{sample.id}/PROCESSING">
                    Processing
                </a>
                |
                <a href="/lab-worklist/status/{sample.id}/COMPLETED">
                    Completed
                </a>
            </td>
        </tr>
        """

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">

        <h1>Lab Worklist</h1>

        <table border="1" cellpadding="10" style="background:white;width:100%;">

            <tr>
                <th>Sample Code</th>
                <th>Patient</th>
                <th>Status</th>
                <th>Action</th>
            </tr>

            {rows}

        </table>

        <br>

        <a href="/dashboard">
            Back to Dashboard
        </a>

    </body>
    </html>
    """
    

@lab_worklist_bp.route(
    "/lab-worklist/status/<sample_id>/<status>"
)
@role_required("SUPER_ADMIN", "LAB_TECHNICIAN")
def update_lab_status(sample_id, status):

    sample = SampleTracking.query.get(sample_id)

    if not sample:
        return "Sample not found"

    sample.status = status

    db.session.commit()

    return redirect("/lab-worklist")
