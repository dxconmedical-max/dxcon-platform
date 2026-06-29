from flask import Blueprint, redirect, request

from app.services.billing_service import BillingService, InvoiceService, LedgerService


billing_invoice_web_bp = Blueprint("billing_invoice_web", __name__)


def _styles():
    return """
    body { margin:0; font-family:Arial,sans-serif; background:#f8fafc; color:#0f172a; }
    .layout { display:flex; min-height:100vh; }
    .sidebar { width:220px; background:#7c2d12; color:white; padding:24px; }
    .sidebar a { display:block; color:white; text-decoration:none; padding:12px 0; border-bottom:1px solid rgba(255,255,255,.12); }
    .content { flex:1; padding:32px; }
    .card { background:white; border-radius:12px; padding:24px; box-shadow:0 4px 12px rgba(0,0,0,.08); margin-bottom:24px; }
    .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:16px; }
    .metric { background:#ffedd5; border-radius:12px; padding:16px; }
    .metric strong { display:block; font-size:24px; }
    table { width:100%; border-collapse:collapse; }
    th, td { padding:12px; border-bottom:1px solid #e5e7eb; text-align:left; font-size:14px; }
    th { background:#e2e8f0; }
    """


def _sidebar(active):
    links = [
        ("/billing/invoices", "Invoices"),
        ("/billing/ledger", "Ledger"),
    ]
    items = ""
    for href, label in links:
        style = ' style="font-weight:bold;"' if href == active else ""
        items += f'<a href="{href}"{style}>{label}</a>'
    return f'<div class="sidebar"><h2>Billing</h2>{items}</div>'


@billing_invoice_web_bp.route("/billing")
def billing_home():
    return redirect("/billing/invoices")


@billing_invoice_web_bp.route("/billing/invoices")
def billing_invoices_page():
    invoices = InvoiceService.list_invoices()
    summary = BillingService.get_summary()
    rows = ""
    for item in invoices.get("invoices", [])[:25]:
        rows += f"<tr><td>{item.get('invoice_no', '')}</td><td>{item.get('total_amount', 0)}</td><td>{item.get('billing_status', '')}</td></tr>"
    return f"""
    <html><head><title>Billing Invoices</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar("/billing/invoices")}<div class="content">
    <div class="card"><h1>Invoices</h1>
    <div class="grid">
        <div class="metric"><span>Total</span><strong>{summary.get("invoices_total", 0)}</strong></div>
        <div class="metric"><span>Paid</span><strong>{summary.get("invoices_paid", 0)}</strong></div>
        <div class="metric"><span>Revenue</span><strong>{summary.get("revenue_total", 0)}</strong></div>
    </div>
    <table><tr><th>Invoice No</th><th>Amount</th><th>Status</th></tr>{rows or "<tr><td colspan='3'>No invoices</td></tr>"}</table>
    </div></div></div></body></html>
    """


@billing_invoice_web_bp.route("/billing/ledger")
def billing_ledger_page():
    ledger = LedgerService.list_ledger()
    summary = BillingService.get_summary()
    rows = ""
    for item in ledger.get("entries", [])[:25]:
        rows += f"<tr><td>{item.get('entry_type', '')}</td><td>{item.get('amount', 0)}</td><td>{item.get('description', '')}</td></tr>"
    return f"""
    <html><head><title>Billing Ledger</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar("/billing/ledger")}<div class="content">
    <div class="card"><h1>Ledger</h1>
    <div class="grid">
        <div class="metric"><span>Entries</span><strong>{ledger.get("count", 0)}</strong></div>
        <div class="metric"><span>Outstanding</span><strong>{summary.get("outstanding_total", 0)}</strong></div>
        <div class="metric"><span>Tax</span><strong>{summary.get("tax_total", 0)}</strong></div>
    </div>
    <table><tr><th>Type</th><th>Amount</th><th>Description</th></tr>{rows or "<tr><td colspan='3'>No ledger entries</td></tr>"}</table>
    </div></div></div></body></html>
    """
