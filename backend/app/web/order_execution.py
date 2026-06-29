from flask import Blueprint, redirect, request

from app.models.medical_order import MedicalOrder
from app.models.sample_incident import SampleIncident
from app.services.order_workflow_service import OrderWorkflowError, OrderWorkflowService
from app.services.sample_tracking_service import SampleTrackingService


order_execution_web_bp = Blueprint(
    "order_execution_web",
    __name__,
)


def _page_styles():
    return """
    body { margin: 0; font-family: Arial, sans-serif; background: #f1f5f9; color: #0f172a; }
    .layout { display: flex; min-height: 100vh; }
    .sidebar { width: 240px; background: #0a4b5c; color: white; padding: 24px; }
    .sidebar h2 { margin-top: 0; margin-bottom: 30px; }
    .menu a { display: block; color: white; text-decoration: none; padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,.15); }
    .content { flex: 1; padding: 32px; }
    .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; gap: 16px; flex-wrap: wrap; }
    .btn { background: #0d6efd; color: white; padding: 10px 16px; border-radius: 8px; text-decoration: none; font-weight: bold; border: none; cursor: pointer; display: inline-block; margin-right: 8px; margin-bottom: 8px; }
    .btn-secondary { background: #6c757d; }
    .card { background: white; border-radius: 12px; padding: 24px; box-shadow: 0 4px 12px rgba(0,0,0,.08); margin-bottom: 24px; }
    table { width: 100%; border-collapse: collapse; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,.08); margin-bottom: 24px; }
    th { background: #e2e8f0; text-align: left; padding: 14px; }
    td { padding: 14px; border-bottom: 1px solid #e5e7eb; vertical-align: top; }
    .badge { display: inline-block; background: #e0f2fe; color: #0369a1; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: bold; margin-right: 6px; }
    .error { background: #fee2e2; color: #991b1b; padding: 12px 16px; border-radius: 8px; margin-bottom: 16px; }
    pre { background: #f8fafc; padding: 12px; border-radius: 8px; overflow-x: auto; }
    """


def _sidebar_html():
    return """
    <div class="sidebar">
        <h2>DxCon</h2>
        <div class="menu">
            <a href="/dashboard">Dashboard</a>
            <a href="/order-execution">Order Execution</a>
            <a href="/order-lifecycle">Order Lifecycle</a>
            <a href="/collector-operations">Collector Ops</a>
        </div>
    </div>
    """


@order_execution_web_bp.route("/order-execution")
def order_execution_page():
    orders = MedicalOrder.query.order_by(MedicalOrder.created_at.desc()).limit(30).all()
    rows = ""
    for order in orders:
        rows += f"""
        <tr>
            <td><a href="/order-execution/orders/{order.id}">{order.order_code}</a></td>
            <td>{order.patient_name}</td>
            <td><span class="badge">{order.status}</span></td>
            <td>{order.payment_status or "-"}</td>
            <td>{order.barcode_value or "-"}</td>
        </tr>
        """

    return f"""
    <html>
    <head><title>Order Execution - DxCon</title><style>{_page_styles()}</style></head>
    <body>
        <div class="layout">
            {_sidebar_html()}
            <div class="content">
                <div class="header"><h1>Order Execution Platform</h1></div>
                <div class="card"><p>Production medical order workflow from booking to delivery.</p></div>
                <table>
                    <thead>
                        <tr><th>Order</th><th>Patient</th><th>Status</th><th>Payment</th><th>Barcode</th></tr>
                    </thead>
                    <tbody>{rows or "<tr><td colspan='5'>No medical orders found</td></tr>"}</tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """


@order_execution_web_bp.route("/order-execution/orders/<order_id>", methods=["GET", "POST"])
def order_execution_detail_page(order_id):
    try:
        detail = OrderWorkflowService.get_order_detail(order_id)
    except OrderWorkflowError:
        return redirect("/order-execution")

    error = None
    message = request.args.get("message")

    if request.method == "POST":
        action = request.form.get("action")
        try:
            if action == "advance":
                OrderWorkflowService.advance_booking_workflow(order_id)
                message = "Order advanced through booking workflow"
            elif action == "complete_demo":
                OrderWorkflowService.run_demo_execution_flow(order_id)
                message = "Demo execution flow completed"
            elif action == "print_label":
                SampleTrackingService.create_label(order_id, mark_printed=True)
                message = "Label generated"
            elif action == "cancel":
                OrderWorkflowService.cancel_order(order_id, reason="Cancelled from admin UI")
                message = "Order cancelled"
        except OrderWorkflowError as exc:
            error = exc.message

    if request.method == "POST":
        detail = OrderWorkflowService.get_order_detail(order_id)

    timeline_rows = ""
    for event in detail["timeline"]:
        timeline_rows += f"""
        <tr>
            <td>{event["event_type"]}</td>
            <td>{event.get("from_status") or ""} → {event.get("to_status") or ""}</td>
            <td>{event.get("message") or ""}</td>
            <td>{event.get("created_at") or ""}</td>
        </tr>
        """

    incident_rows = ""
    incidents = SampleIncident.query.filter_by(medical_order_id=order_id).all()
    for incident in incidents:
        incident_rows += f"""
        <tr>
            <td>{incident.incident_type}</td>
            <td>{incident.severity}</td>
            <td>{incident.status}</td>
            <td>{incident.description}</td>
        </tr>
        """

    tracking = detail.get("tracking")
    sample = detail.get("sample")
    label_payload = detail["labels"][0]["print_payload"] if detail["labels"] else "No label yet"

    error_html = f'<div class="error">{error}</div>' if error else ""
    message_html = f'<div class="card"><strong>{message}</strong></div>' if message else ""

    return f"""
    <html>
    <head><title>{detail["order_code"]} - Order Execution</title><style>{_page_styles()}</style></head>
    <body>
        <div class="layout">
            {_sidebar_html()}
            <div class="content">
                <div class="header">
                    <h1>{detail["order_code"]}</h1>
                    <a class="btn btn-secondary" href="/order-execution">Back</a>
                </div>
                {error_html}
                {message_html}
                <div class="card">
                    <p><strong>Patient:</strong> {detail["patient_name"]} ({detail.get("patient_phone") or ""})</p>
                    <p><strong>Status:</strong> <span class="badge">{detail["status"]}</span></p>
                    <p><strong>Barcode:</strong> {detail.get("barcode_value") or "-"}</p>
                    <p><strong>Sample:</strong> {sample["sample_code"] if sample else "None"} ({sample["status"] if sample else "-"})</p>
                    <p><strong>Tracking:</strong> {tracking["status"] if tracking else "None"}</p>
                    <form method="post" style="margin-top:16px">
                        <button class="btn" name="action" value="advance" type="submit">Advance Booking Flow</button>
                        <button class="btn" name="action" value="complete_demo" type="submit">Run Demo Flow</button>
                        <button class="btn btn-secondary" name="action" value="print_label" type="submit">Print Label</button>
                        <button class="btn btn-secondary" name="action" value="cancel" type="submit">Cancel</button>
                    </form>
                </div>
                <h2>Timeline</h2>
                <table>
                    <thead><tr><th>Event</th><th>Transition</th><th>Message</th><th>Time</th></tr></thead>
                    <tbody>{timeline_rows or "<tr><td colspan='4'>No events</td></tr>"}</tbody>
                </table>
                <h2>Incident History</h2>
                <table>
                    <thead><tr><th>Type</th><th>Severity</th><th>Status</th><th>Description</th></tr></thead>
                    <tbody>{incident_rows or "<tr><td colspan='4'>No incidents</td></tr>"}</tbody>
                </table>
                <h2>Label Payload</h2>
                <div class="card"><pre>{label_payload}</pre></div>
            </div>
        </div>
    </body>
    </html>
    """
