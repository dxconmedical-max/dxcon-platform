"""Reception desk demo dashboard for pilot workflow."""

from flask import Blueprint

from app.models.order import Order
from app.models.patient import Patient
from app.web.demo_pilot_lib import (
    DEMO_ORDER_PREFIX,
    DEMO_PATIENT_PREFIX,
    metric_cards,
    page_header,
    render_safe_page,
    safe_query,
    seeded_summary,
    system_status,
    system_status_cards,
)

reception_web_bp = Blueprint("reception_web", __name__)


def _build_reception_body() -> str:
    summary = seeded_summary()
    status = system_status()
    patients = safe_query(Patient, filter_like=("patient_code", DEMO_PATIENT_PREFIX), limit=10)
    orders = safe_query(Order, filter_like=("order_code", DEMO_ORDER_PREFIX), limit=10)

    patient_rows = "".join(
        f"<tr><td>{p.patient_code}</td><td>{p.full_name}</td><td>{p.phone or ''}</td><td>{p.email or ''}</td></tr>"
        for p in patients
    ) or "<tr><td colspan='4'>No demo patients found. Run seed_demo_data.py --apply.</td></tr>"

    order_rows = "".join(
        f"<tr><td>{o.order_code}</td><td>{o.patient_id}</td><td>{o.status}</td><td>{o.total_amount or 0}</td></tr>"
        for o in orders
    ) or "<tr><td colspan='4'>No demo orders found.</td></tr>"

    return f"""
    {page_header("Reception Dashboard", "Front desk view for demo patients and incoming orders.")}
    {metric_cards([
        ("Demo Patients", summary["patients"]),
        ("Demo Orders", summary["orders"]),
        ("Users", summary["users"]),
        ("Test Catalog", summary["test_catalog"]),
    ])}
    <div class="card">
        <h2>System Status</h2>
        {system_status_cards(status)}
        <p class="muted">Last probe: {status["timestamp"]}</p>
    </div>
    <div class="card">
        <h2>Recent Demo Patients</h2>
        <table><tr><th>Code</th><th>Name</th><th>Phone</th><th>Email</th></tr>{patient_rows}</table>
    </div>
    <div class="card">
        <h2>Recent Demo Orders</h2>
        <table><tr><th>Order</th><th>Patient Ref</th><th>Status</th><th>Amount</th></tr>{order_rows}</table>
    </div>
    <div class="card links">
        <a href="/patients">Patient Registry</a>
        <a href="/orders">Orders</a>
        <a href="/order-lifecycle">Order Lifecycle</a>
        <a href="/demo-accounts">Demo Accounts</a>
    </div>
    """


@reception_web_bp.route("/reception")
def reception_dashboard():
    return render_safe_page(
        "Reception Dashboard",
        "Front desk view for demo patients and incoming orders.",
        _build_reception_body,
    )
