
from flask import Blueprint, current_app
from app.models.order import Order
from app.models.patient import Patient
from app.models.test_catalog import TestCatalog
from app.models.user import User
from app.web.demo_pilot_lib import (
    DEMO_ORDER_PREFIX,
    metric_cards,
    render_pilot_page,
    safe_query,
    seeded_summary,
    system_status,
    system_status_cards,
)

executive_v9_bp = Blueprint("executive_v9", __name__)


@executive_v9_bp.route("/executive-v9")
def executive_v9():
    summary = seeded_summary()
    status = system_status()
    recent_orders = safe_query(Order, filter_like=("order_code", DEMO_ORDER_PREFIX), limit=10)

    order_rows = "".join(
        f"<tr><td>{o.order_code}</td><td>{o.patient_id}</td><td>{o.status}</td><td>{o.total_amount or 0}</td></tr>"
        for o in recent_orders
    ) or "<tr><td colspan='4'>No demo orders found.</td></tr>"

    try:
        total_users = User.query.count()
        total_patients = Patient.query.count()
        total_tests = TestCatalog.query.count()
        total_orders = Order.query.count()
    except Exception:
        total_users = summary["users"]
        total_patients = summary["patients"]
        total_tests = summary["test_catalog"]
        total_orders = summary["orders"]

    body = f"""
    <h1>Executive Dashboard</h1>
    <p style="color:#475569;">Pilot overview using seeded demo data and live system probes.</p>
    {metric_cards([
        ("Total Users", total_users),
        ("Total Patients", total_patients),
        ("Test Catalog Items", total_tests),
        ("Total Orders", total_orders),
    ])}
    <div class="card">
        <h2>Seeded Demo Dataset</h2>
        {metric_cards([
            ("Demo Users", summary["users"]),
            ("Demo Patients", summary["patients"]),
            ("Demo Tests", summary["test_catalog"]),
            ("Demo Orders", summary["orders"]),
        ])}
    </div>
    <div class="card">
        <h2>System Status</h2>
        {system_status_cards(status)}
        <p style="color:#64748b;font-size:13px;">Last probe: {status["timestamp"]}</p>
    </div>
    <div class="card">
        <h2>Recent Demo Orders</h2>
        <table><tr><th>Order</th><th>Patient Ref</th><th>Status</th><th>Amount</th></tr>{order_rows}</table>
    </div>
    """
    return render_pilot_page("Executive Dashboard", body)
