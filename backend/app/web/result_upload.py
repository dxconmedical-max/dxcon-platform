from flask import Blueprint, request, redirect, send_file, session
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import uuid

from app.extensions.db import db
from app.models.order import Order
from app.models.patient import Patient
from app.models.result_file import ResultFile
from app.utils.auth import role_required


result_upload_web_bp = Blueprint("result_upload_web", __name__)

UPLOAD_FOLDER = "uploads/results"


@result_upload_web_bp.route("/result-files")
@role_required("SUPER_ADMIN", "DOCTOR", "LAB_TECHNICIAN")
def result_files_page():

    files = ResultFile.query.all()
    rows = ""

    for item in files:
        order = Order.query.get(item.order_id)
        patient_name = ""

        if order:
            patient = Patient.query.get(order.patient_id)
            patient_name = patient.full_name if patient else ""

        rows += f"""
        <tr>
            <td>{patient_name}</td>
            <td>{order.order_code if order else ""}</td>
            <td>{item.file_name}</td>
            <td>
                <a href="/result-files/download/{item.id}">
                    Download
                </a>
            </td>
        </tr>
        """

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">

        <h1>Result Files</h1>

        <a href="/result-files/new"
           style="background:#0d6efd;color:white;padding:10px 15px;text-decoration:none;border-radius:6px;">
           + Upload Result File
        </a>

        <br><br>

        <table border="1" cellpadding="10" style="background:white;width:100%;">
            <tr>
                <th>Patient</th>
                <th>Order</th>
                <th>File</th>
                <th>Action</th>
            </tr>
            {rows}
        </table>

        <br>
        <a href="/dashboard">Back to Dashboard</a>

    </body>
    </html>
    """


@result_upload_web_bp.route("/result-files/new", methods=["GET", "POST"])
@role_required("SUPER_ADMIN", "LAB_TECHNICIAN")
def upload_result_file():

    orders = Order.query.all()

    if request.method == "POST":

        order_id = request.form.get("order_id")
        file = request.files.get("file")

        if not file:
            return "No file uploaded"

        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        original_name = secure_filename(file.filename)
        stored_name = f"{uuid.uuid4()}_{original_name}"
        file_path = os.path.join(UPLOAD_FOLDER, stored_name)

        file.save(file_path)

        item = ResultFile(
            order_id=order_id,
            file_name=original_name,
            file_path=file_path,
            uploaded_by=session.get("user_id"),
            created_at=datetime.utcnow()
        )

        db.session.add(item)
        db.session.commit()

        return redirect("/result-files")

    order_options = ""

    for order in orders:
        patient = Patient.query.get(order.patient_id)
        patient_name = patient.full_name if patient else ""

        order_options += f"""
        <option value="{order.id}">
            {order.order_code} - {patient_name}
        </option>
        """

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">

        <h1>Upload Result File</h1>

        <form method="POST" enctype="multipart/form-data">

            <label>Order</label><br>
            <select name="order_id">
                {order_options}
            </select>

            <br><br>

            <label>Result File</label><br>
            <input type="file" name="file">

            <br><br>

            <button type="submit">
                Upload
            </button>

        </form>

        <br>
        <a href="/result-files">Back</a>

    </body>
    </html>
    """


@result_upload_web_bp.route("/result-files/download/<file_id>")
@role_required("SUPER_ADMIN", "DOCTOR", "LAB_TECHNICIAN")
def download_result_file(file_id):

    item = ResultFile.query.get(file_id)

    if not item:
        return "File not found"

    return send_file(
        item.file_path,
        as_attachment=True,
        download_name=item.file_name
    )


@result_upload_web_bp.route("/portal/result-files/download/<file_id>")
def portal_download_result_file(file_id):

    item = ResultFile.query.get(file_id)

    if not item:
        return "File not found", 404

    return send_file(
        item.file_path,
        as_attachment=True,
        download_name=item.file_name
    )
