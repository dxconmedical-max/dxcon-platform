from flask import Blueprint, redirect

from app.services.payment_gateway_service import PaymentService, RefundService


payment_gateway_web_bp = Blueprint("payment_gateway_web", __name__)


def _styles():
    return """
    body { margin:0; font-family:Arial,sans-serif; background:#f8fafc; color:#0f172a; }
    .layout { display:flex; min-height:100vh; }
    .sidebar { width:220px; background:#312e81; color:white; padding:24px; }
    .sidebar a { display:block; color:white; text-decoration:none; padding:12px 0; border-bottom:1px solid rgba(255,255,255,.12); }
    .content { flex:1; padding:32px; }
    .card { background:white; border-radius:12px; padding:24px; box-shadow:0 4px 12px rgba(0,0,0,.08); margin-bottom:24px; }
    table { width:100%; border-collapse:collapse; }
    th, td { padding:12px; border-bottom:1px solid #e5e7eb; text-align:left; font-size:14px; }
    th { background:#e2e8f0; }
    """


def _sidebar(active):
    links = [
        ("/payment/history", "History"),
        ("/payment/refunds", "Refunds"),
    ]
    items = ""
    for href, label in links:
        style = ' style="font-weight:bold;"' if href == active else ""
        items += f'<a href="{href}"{style}>{label}</a>'
    return f'<div class="sidebar"><h2>Payment Gateway</h2>{items}</div>'


@payment_gateway_web_bp.route("/payment")
def payment_home():
    return redirect("/payment/history")


@payment_gateway_web_bp.route("/payment/history")
def payment_history_page():
    history = PaymentService.get_history()
    rows = ""
    for item in history.get("history", [])[:25]:
        payment = item.get("payment") or {}
        rows += f"<tr><td>{item.get('external_transaction_id', '')}</td><td>{item.get('provider', '')}</td><td>{item.get('amount', 0)}</td><td>{item.get('status', '')}</td><td>{payment.get('invoice_id', '')}</td></tr>"
    return f"""
    <html><head><title>Payment History</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar("/payment/history")}<div class="content">
    <div class="card"><h1>Payment History</h1>
    <table><tr><th>Transaction</th><th>Provider</th><th>Amount</th><th>Status</th><th>Invoice</th></tr>{rows or "<tr><td colspan='5'>No payments</td></tr>"}</table>
    </div></div></div></body></html>
    """


@payment_gateway_web_bp.route("/payment/refunds")
def payment_refunds_page():
    refunds = RefundService.list_refunds()
    rows = ""
    for item in refunds.get("refunds", [])[:25]:
        rows += f"<tr><td>{item.get('refund_code', '')}</td><td>{item.get('provider', '')}</td><td>{item.get('amount', 0)}</td><td>{item.get('status', '')}</td><td>{item.get('reason', '')}</td></tr>"
    return f"""
    <html><head><title>Payment Refunds</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar("/payment/refunds")}<div class="content">
    <div class="card"><h1>Refunds</h1>
    <table><tr><th>Code</th><th>Provider</th><th>Amount</th><th>Status</th><th>Reason</th></tr>{rows or "<tr><td colspan='5'>No refunds</td></tr>"}</table>
    </div></div></div></body></html>
    """
