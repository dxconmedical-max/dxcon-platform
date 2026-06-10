from flask import Blueprint, request, redirect

from app.extensions.db import db
from app.models.home_collection import HomeCollection
from app.models.patient import Patient


home_collections_web_bp = Blueprint(
    "home_collections_web",
    __name__
)


@home_collections_web_bp.route("/home-collections")
def home_collections_page():

    collections = HomeCollection.query.all()

    rows = ""

    for item in collections:

        patient = Patient.query.get(item.patient_id)

        patient_name = (
            patient.full_name
            if patient else ""
        )

        rows += f"""
        <tr>
            <td>{patient_name}</td>
            <td>{item.address}</td>
            <td>{item.scheduled_time}</td>
            <td>{item.status}</td>

            <td>
                <a href="/home-collections/status/{item.id}/ASSIGNED">
                    Assign
                </a>
            </td>

            <td>
                <a href="/home-collections/status/{item.id}/COLLECTED">
                    Collected
                </a>
            </td>

            <td>
                <a href="/home-collections/status/{item.id}/DELIVERED">
                    Delivered
                </a>
            </td>

            <td>
                <a href="/home-collections/status/{item.id}/COMPLETED">
                    Completed
                </a>
            </td>
        </tr>
        """

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">

        <h1>Home Collections</h1>

        <a href="/home-collections/new"
           style="background:#0d6efd;color:white;padding:10px 15px;text-decoration:none;border-radius:6px;">
           + New Collection
        </a>

        <br><br>

        <table border="1" cellpadding="10"
               style="background:white;width:100%;">

            <tr>
                <th>Patient</th>
                <th>Address</th>
                <th>Schedule</th>
                <th>Status</th>
                <th>Assign</th>
                <th>Collected</th>
                <th>Delivered</th>
                <th>Completed</th>
            </tr>

            {rows}

        </table>

    </body>
    </html>
    """


@home_collections_web_bp.route(
    "/home-collections/new",
    methods=["GET", "POST"]
)
def new_collection():

    patients = Patient.query.all()

    if request.method == "POST":

        item = HomeCollection(
            patient_id=request.form.get(
                "patient_id"
            ),
            address=request.form.get(
                "address"
            ),
            scheduled_time=request.form.get(
                "scheduled_time"
            ),
            status="REQUESTED"
        )

        db.session.add(item)
        db.session.commit()

        return redirect("/home-collections")

    patient_options = ""

    for patient in patients:

        patient_options += f"""
        <option value="{patient.id}">
            {patient.full_name}
        </option>
        """

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">

        <h1>New Home Collection</h1>

        <form method="POST">

            <label>Patient</label>
            <br>

            <select name="patient_id">
                {patient_options}
            </select>

            <br><br>

            <input
                name="address"
                placeholder="Address"
                style="width:400px;padding:10px;"
            >

            <br><br>

            <input
                name="scheduled_time"
                placeholder="2026-06-10 08:00"
                style="width:300px;padding:10px;"
            >

            <br><br>

            <button type="submit">
                Save
            </button>

        </form>

    </body>
    </html>
    """


@home_collections_web_bp.route(
    "/home-collections/status/<collection_id>/<status>"
)
def update_status(
    collection_id,
    status
):

    item = HomeCollection.query.get(
        collection_id
    )

    if not item:
        return "Collection not found"

    item.status = status

    db.session.commit()

    return redirect(
        "/home-collections"
    )
