from flask import Blueprint

from app.models.driver import Driver
from app.models.transport_box import TransportBox
from app.models.sample_tracking import SampleTracking
from app.models.home_collection import HomeCollection
from app.models.patient import Patient
from app.models.laboratory import Laboratory
from app.utils.auth import role_required


dispatch_web_bp = Blueprint("dispatch_web", __name__)


@dispatch_web_bp.route("/dispatch")
@role_required("SUPER_ADMIN", "COLLECTOR", "LAB_TECHNICIAN")
def dispatch_center():

    boxes = TransportBox.query.all()
    rows = ""

    for box in boxes:

        driver_name = ""

        if box.driver_id:
            driver = Driver.query.get(box.driver_id)
            driver_name = driver.full_name if driver else ""

        samples = SampleTracking.query.filter_by(
            transport_box_id=box.id
        ).all()

        sample_count = len(samples)

        sample_links = ""

        destination_lab = ""

        for sample in samples:
            sample_links += f"""
            <a href="/samples/verify/{sample.sample_code}">
                {sample.sample_code}
            </a><br>
            """

        lab = Laboratory.query.first()
        if lab:
            destination_lab = lab.name

        map_link = ""

        if box.latitude and box.longitude:
            map_link = f"""
            <a target="_blank" href="{box.map_url()}">
                View Map
            </a>
            """

        alert_style = "color:#198754;font-weight:bold;"

        if box.alert_status != "NORMAL":
            alert_style = "color:#dc3545;font-weight:bold;"

        rows += f"""
        <tr>
            <td>{driver_name}</td>
            <td>{box.box_code}</td>
            <td>{sample_count}</td>
            <td>{sample_links}</td>
            <td>{box.temperature} °C</td>
            <td style="{alert_style}">{box.alert_status}</td>
            <td>{box.battery_level}%</td>
            <td>{destination_lab}</td>
            <td>{box.status}</td>
            <td>{map_link}</td>
        </tr>
        """

    return f"""
    <html>
    <head>
        <title>DxCon Dispatch Center</title>
    </head>

    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">

        <h1>DxCon Dispatch Center</h1>

        <p>
            Real-time overview of collectors, transport boxes,
            sample custody, temperature alerts, and destination lab.
        </p>

        <table border="1" cellpadding="10" style="background:white;width:100%;">
            <tr>
                <th>Driver</th>
                <th>Box</th>
                <th>Samples</th>
                <th>Sample Codes</th>
                <th>Temperature</th>
                <th>Alert</th>
                <th>Battery</th>
                <th>Destination Lab</th>
                <th>Status</th>
                <th>GPS</th>
            </tr>
            {rows}
        </table>

        <br>

        <a href="/dashboard">Back to Dashboard</a>

    </body>
    </html>
    """
