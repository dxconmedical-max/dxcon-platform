
from flask import Blueprint

from app.models.order import Order
from app.models.patient import Patient
from app.models.test_catalog import TestCatalog
from app.models.user import User
from app.web.demo_pilot_lib import (
    DEMO_ORDER_PREFIX,
    metric_cards,
    page_header,
    render_safe_page,
    safe_query,
    seeded_summary,
    system_status,
    system_status_cards,
)

executive_v9_bp = Blueprint("executive_v9", __name__)


def _build_executive_body() -> str:
    summary = seeded_summary()
    status = system_status()
    recent_orders = safe_query(Order, filter_like=("order_code", DEMO_ORDER_PREFIX), limit=10)

    order_rows = "".join(
        f"<tr><td>{o.order_code}</td><td>{o.patient_id}</td><td>{o.status}</td><td>{o.total_amount or 0}</td></tr>"
        for o in recent_orders
    ) or "<tr><td colspan='4'>No demo orders found.</td></tr>"

    total_users = safe_query(User)
    total_patients = safe_query(Patient)
    total_tests = safe_query(TestCatalog)
    total_orders = safe_query(Order)

    return f"""
    {page_header("Executive Dashboard", "Pilot overview using seeded demo data and live system probes.")}
    {metric_cards([
        ("Total Users", len(total_users)),
        ("Total Patients", len(total_patients)),
        ("Test Catalog Items", len(total_tests)),
        ("Total Orders", len(total_orders)),
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
        <p class="muted">Last probe: {status["timestamp"]}</p>
    </div>
    <div class="card">
        <h2>Recent Demo Orders</h2>
        <table><tr><th>Order</th><th>Patient Ref</th><th>Status</th><th>Amount</th></tr>{order_rows}</table>
    </div>
    """


@executive_v9_bp.route("/executive-v9")
def executive_v9():
    return render_safe_page(
        "Executive Dashboard",
        "Pilot overview using seeded demo data and live system probes.",
        _build_executive_body,
    )
