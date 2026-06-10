from flask import Blueprint, request, redirect

from app.extensions.db import db
from app.models.patient import Patient


patients_web_bp = Blueprint("patients_web", __name__)


@patients_web_bp.route("/patients")
def patients_page():

    patients = Patient.query.all()

    rows = ""

    for patient in patients:
        rows += f"""
        <tr>
            <td>{patient.patient_code}</td>
            <td>{patient.full_name}</td>
            <td>{patient.date_of_birth or ""}</td>
            <td>{patient.gender or ""}</td>
            <td>{patient.phone or ""}</td>
            <td>{patient.national_id or ""}</td>
            <td>{patient.address or ""}</td>
        </tr>
        """

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">

        <h1>Patients Management</h1>

        <a href="/patients/new"
           style="background:#0d6efd;color:white;padding:10px 15px;text-decoration:none;border-radius:6px;">
           + New Patient
        </a>

        <br><br>

        <table border="1" cellpadding="10" style="background:white;width:100%;">
            <tr>
                <th>Code</th>
                <th>Full Name</th>
                <th>Date of Birth</th>
                <th>Gender</th>
                <th>Phone</th>
                <th>National ID</th>
                <th>Address</th>
            </tr>
            {rows}
        </table>

        <br>
        <a href="/dashboard">Back to Dashboard</a>

    </body>
    </html>
    """


@patients_web_bp.route("/patients/new", methods=["GET", "POST"])
def new_patient():

    if request.method == "POST":

        patient = Patient(
            patient_code=request.form.get("patient_code"),
            full_name=request.form.get("full_name"),
            gender=request.form.get("gender"),
            date_of_birth=request.form.get("date_of_birth"),
            phone=request.form.get("phone"),
            email=request.form.get("email"),
            address=request.form.get("address"),
            national_id=request.form.get("national_id")
        )

        db.session.add(patient)
        db.session.commit()

        return redirect("/patients")

    return """
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">

        <h1>New Patient</h1>

        <form method="POST">
            <label>Patient Code *</label><br>
            <input name="patient_code" placeholder="PT001" required><br><br>

            <label>Full Name *</label><br>
            <input name="full_name" placeholder="Nguyen Van A" required><br><br>

            <label>Date of Birth</label><br>
            <input name="date_of_birth" type="date"><br><br>

            <label>Gender</label><br>
            <select name="gender">
                <option value="">-- Select --</option>
                <option value="MALE">Male</option>
                <option value="FEMALE">Female</option>
                <option value="OTHER">Other</option>
            </select><br><br>

            <label>Phone *</label><br>
            <input name="phone" placeholder="0901234567" required><br><br>

            <label>Email</label><br>
            <input name="email" placeholder="patient@email.com"><br><br>

            <label>National ID / CCCD</label><br>
            <input name="national_id" placeholder="012345678901"><br><br>

            <label>Address</label><br>
            <textarea name="address" placeholder="Address"></textarea><br><br>

            <button type="submit">Save Patient</button>
        </form>

        <br>
        <a href="/patients">Back to Patients</a>

    </body>
    </html>
    """
