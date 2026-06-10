from flask import Blueprint, request, redirect

from app.extensions.db import db
from app.models.driver import Driver
from app.models.transport_box import TransportBox
from app.utils.auth import role_required


drivers_web_bp = Blueprint("drivers_web", __name__)


@drivers_web_bp.route("/drivers")
@role_required("SUPER_ADMIN", "COLLECTOR")
def drivers_page():

    drivers = Driver.query.all()
    rows = ""

    for driver in drivers:

        boxes = TransportBox.query.filter_by(driver_id=driver.id).all()
        box_codes = ", ".join([box.box_code for box in boxes])

        rows += f"""
        <tr>
            <td>{driver.driver_code}</td>
            <td>{driver.full_name}</td>
            <td>{driver.phone or ""}</td>
            <td>{driver.vehicle_no or ""}</td>
            <td>{driver.status}</td>
            <td>{box_codes}</td>
        </tr>
        """

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">

        <h1>Drivers / Collectors</h1>

        <a href="/drivers/new"
           style="background:#0d6efd;color:white;padding:10px 15px;text-decoration:none;border-radius:6px;">
           + New Driver
        </a>

        <br><br>

        <table border="1" cellpadding="10" style="background:white;width:100%;">
            <tr>
                <th>Code</th>
                <th>Name</th>
                <th>Phone</th>
                <th>Vehicle</th>
                <th>Status</th>
                <th>Assigned Boxes</th>
            </tr>
            {rows}
        </table>

        <br>
        <a href="/dashboard">Back to Dashboard</a>

    </body>
    </html>
    """


@drivers_web_bp.route("/drivers/new", methods=["GET", "POST"])
@role_required("SUPER_ADMIN")
def new_driver():

    if request.method == "POST":

        driver = Driver(
            driver_code=request.form.get("driver_code"),
            full_name=request.form.get("full_name"),
            phone=request.form.get("phone"),
            vehicle_no=request.form.get("vehicle_no"),
            status=request.form.get("status") or "ACTIVE"
        )

        db.session.add(driver)
        db.session.commit()

        return redirect("/drivers")

    return """
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">

        <h1>New Driver</h1>

        <form method="POST">
            <label>Driver Code</label><br>
            <input name="driver_code" placeholder="DRV001" required>

            <br><br>

            <label>Full Name</label><br>
            <input name="full_name" placeholder="Nguyen Van Tai" required>

            <br><br>

            <label>Phone</label><br>
            <input name="phone" placeholder="0900000004">

            <br><br>

            <label>Vehicle No</label><br>
            <input name="vehicle_no" placeholder="51A-12345">

            <br><br>

            <label>Status</label><br>
            <select name="status">
                <option value="ACTIVE">ACTIVE</option>
                <option value="INACTIVE">INACTIVE</option>
            </select>

            <br><br>

            <button type="submit">Save Driver</button>
        </form>

        <br>
        <a href="/drivers">Back</a>

    </body>
    </html>
    """
