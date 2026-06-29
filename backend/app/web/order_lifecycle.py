from flask import Blueprint, redirect, request

from app.models.marketplace_booking import MarketplaceBooking
from app.models.order import Order
from app.models.sample_collection import SampleCollection
from app.services.order_lifecycle import OrderLifecycleError, OrderLifecycleService
from app.services.sample_collection_workflow import (
    SampleCollectionWorkflowError,
    SampleCollectionWorkflowService,
)


order_lifecycle_web_bp = Blueprint(
    "order_lifecycle_web",
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
    .btn-success { background: #198754; }
    .card { background: white; border-radius: 12px; padding: 24px; box-shadow: 0 4px 12px rgba(0,0,0,.08); margin-bottom: 24px; }
    table { width: 100%; border-collapse: collapse; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,.08); margin-bottom: 24px; }
    th { background: #e2e8f0; text-align: left; padding: 14px; }
    td { padding: 14px; border-bottom: 1px solid #e5e7eb; vertical-align: top; }
    .badge { display: inline-block; background: #e0f2fe; color: #0369a1; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: bold; margin-right: 6px; }
    .error { background: #fee2e2; color: #991b1b; padding: 12px 16px; border-radius: 8px; margin-bottom: 16px; }
    """


def _sidebar_html():
    return """
    <div class="sidebar">
        <h2>DxCon</h2>
        <div class="menu">
            <a href="/dashboard">Dashboard</a>
            <a href="/order-lifecycle">Order Lifecycle</a>
            <a href="/scheduling">Scheduling</a>
            <a href="/marketplace">Marketplace</a>
            <a href="/partners">Partners</a>
        </div>
    </div>
    """


@order_lifecycle_web_bp.route("/order-lifecycle")
def order_lifecycle_page():
    bookings = MarketplaceBooking.query.order_by(
        MarketplaceBooking.created_at.desc()
    ).limit(30).all()

    rows = ""
    for booking in bookings:
        order = Order.query.filter_by(marketplace_booking_id=booking.id).first()
        collection = SampleCollection.query.filter_by(
            marketplace_booking_id=booking.id
        ).first()
        rows += f"""
        <tr>
            <td><a href="/order-lifecycle/bookings/{booking.id}">{booking.booking_code}</a></td>
            <td>{booking.patient_name}</td>
            <td>{booking.status}</td>
            <td>{order.order_code if order else "-"}</td>
            <td>{order.status if order else "-"}</td>
            <td>{collection.status if collection else "-"}</td>
        </tr>
        """

    return f"""
    <html>
    <head><title>Order Lifecycle - DxCon</title><style>{_page_styles()}</style></head>
    <body>
        <div class="layout">
            {_sidebar_html()}
            <div class="content">
                <div class="header">
                    <h1>Order Lifecycle & Sample Collection</h1>
                </div>
                <div class="card">
                    <p>Track marketplace bookings through order creation and sample collection workflow.</p>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>Booking</th>
                            <th>Patient</th>
                            <th>Booking Status</th>
                            <th>Order</th>
                            <th>Order Status</th>
                            <th>Collection</th>
                        </tr>
                    </thead>
                    <tbody>{rows or "<tr><td colspan='6'>No bookings found</td></tr>"}</tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """


@order_lifecycle_web_bp.route("/order-lifecycle/bookings/<booking_id>", methods=["GET", "POST"])
def order_lifecycle_booking_page(booking_id):
    booking = MarketplaceBooking.query.get(booking_id)
    if not booking:
        return redirect("/order-lifecycle")

    error = None
    message = request.args.get("message")

    if request.method == "POST":
        action = request.form.get("action")
        try:
            if action == "create_order":
                OrderLifecycleService.create_order_from_booking(booking_id)
                message = "Order created"
            elif action == "check_in":
                SampleCollectionWorkflowService.check_in_collection(booking_id)
                message = "Collector checked in"
            elif action == "collect":
                SampleCollectionWorkflowService.record_collection(booking_id)
                message = "Sample collected"
            elif action == "dispatch":
                SampleCollectionWorkflowService.dispatch_sample(booking_id)
                message = "Sample dispatched"
            elif action == "lab_receive":
                SampleCollectionWorkflowService.receive_at_lab(booking_id)
                message = "Sample received at lab"
        except (OrderLifecycleError, SampleCollectionWorkflowError) as exc:
            error = exc.message

    order = OrderLifecycleService.get_order_for_booking(booking_id)
    collection = SampleCollectionWorkflowService.get_collection_for_booking(booking_id)

    error_html = f'<div class="error">{error}</div>' if error else ""
    message_html = f'<div class="card"><strong>{message}</strong></div>' if message else ""

    actions = ""
    if not order:
        actions += """
        <form method="post" style="display:inline">
            <input type="hidden" name="action" value="create_order">
            <button class="btn" type="submit">Create Order</button>
        </form>
        """
    if order:
        actions += """
        <form method="post" style="display:inline">
            <input type="hidden" name="action" value="check_in">
            <button class="btn btn-secondary" type="submit">Check In</button>
        </form>
        <form method="post" style="display:inline">
            <input type="hidden" name="action" value="collect">
            <button class="btn btn-success" type="submit">Collect Sample</button>
        </form>
        <form method="post" style="display:inline">
            <input type="hidden" name="action" value="dispatch">
            <button class="btn" type="submit">Dispatch</button>
        </form>
        <form method="post" style="display:inline">
            <input type="hidden" name="action" value="lab_receive">
            <button class="btn btn-secondary" type="submit">Lab Receive</button>
        </form>
        """

    return f"""
    <html>
    <head><title>{booking.booking_code} - Order Lifecycle</title><style>{_page_styles()}</style></head>
    <body>
        <div class="layout">
            {_sidebar_html()}
            <div class="content">
                <div class="header">
                    <h1>Booking {booking.booking_code}</h1>
                    <a class="btn btn-secondary" href="/order-lifecycle">Back</a>
                </div>
                {error_html}
                {message_html}
                <div class="card">
                    <p><strong>Patient:</strong> {booking.patient_name} ({booking.patient_phone})</p>
                    <p><strong>Booking status:</strong> <span class="badge">{booking.status}</span></p>
                    <p><strong>Order:</strong> {order.order_code if order else "Not created"} {f"({order.status})" if order else ""}</p>
                    <p><strong>Collection:</strong> {collection["status"] if collection else "Not started"}</p>
                    <div style="margin-top: 20px;">{actions}</div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
