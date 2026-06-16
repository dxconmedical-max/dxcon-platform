from flask import Blueprint

from app.models.patient import Patient
from app.models.order import Order
from app.models.driver import Driver
from app.models.sample_tracking import SampleTracking
from app.models.home_collection import HomeCollection
from app.models.clinical_summary import ClinicalSummary

executive_v8_bp = Blueprint(
    "executive_v8",
    __name__
)


@executive_v8_bp.route("/executive")
def executive():

    patients = Patient.query.count()
    orders = Order.query.count()
    collectors = Driver.query.count()
    samples = SampleTracking.query.count()
    bookings = HomeCollection.query.count()

    low = ClinicalSummary.query.filter_by(
        risk_level="LOW"
    ).count()

    medium = ClinicalSummary.query.filter_by(
        risk_level="MEDIUM"
    ).count()

    high = ClinicalSummary.query.filter_by(
        risk_level="HIGH"
    ).count()

    critical = ClinicalSummary.query.filter_by(
        risk_level="CRITICAL"
    ).count()

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px">

        <h1>DxCon Executive Command Center</h1>

        <div style="display:flex;gap:20px;flex-wrap:wrap">

            <div style="background:white;padding:20px;width:220px">
                <h3>Patients</h3>
                <h1>{patients}</h1>
            </div>

            <div style="background:white;padding:20px;width:220px">
                <h3>Orders</h3>
                <h1>{orders}</h1>
            </div>

            <div style="background:white;padding:20px;width:220px">
                <h3>Collectors</h3>
                <h1>{collectors}</h1>
            </div>

            <div style="background:white;padding:20px;width:220px">
                <h3>Samples</h3>
                <h1>{samples}</h1>
            </div>

            <div style="background:white;padding:20px;width:220px">
                <h3>Bookings</h3>
                <h1>{bookings}</h1>
            </div>

        </div>

        <br><br>

        <div style="background:white;padding:25px">

            <h2>AI Risk Distribution</h2>

            <p>LOW : {low}</p>
            <p>MEDIUM : {medium}</p>
            <p>HIGH : {high}</p>
            <p>CRITICAL : {critical}</p>

        </div>

    </body>
    </html>
    """
